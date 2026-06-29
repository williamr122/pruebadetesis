"""
Proyecto: YELIA4AP
Archivo: backend/nlp/core.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
from __future__ import annotations

"""
Archivo: backend/nlp/core.py
Proyecto: YELIA4AP
Última revisión: 2026-02-10

Componentes de procesamiento de lenguaje natural (NLU/NLP) del backend.

Convenciones:
- Funciones pequeñas, nombres descriptivos y manejo de errores explícito.
- Evitar prints en producción: usar logging si aplica.
"""


#
# Archivo: backend/nlp/core.py
# Rol: Módulo del backend (Flask) de YELIA4AP.


"""Core
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.

backend/nlp/core.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Este archivo pertenece al backend (Flask) de YELIA. Contiene lógica de servidor
    y/o utilidades que soportan rutas, servicios, persistencia y orquestación NLP.
"""



import json
import os
import re
import ast
from typing import Any, Dict, List, Optional

import structlog

from backend.core.net import has_internet
from backend.services.temas_service import identificar_tema_desde_texto, TEMAS_DISPONIBLES
from backend.db.session import db_session

from .provider_router import seleccionar_proveedor
from .domain import match_domain, tiene_senal_materia, es_ambigua_pero_probable_materia
from .history_utils import (
    normalizar_historial,
    construir_contexto_desde_historial,
    extraer_ultima_pista_historial,
    extraer_ultimo_tema_relevante,
    hash_texto_corto,
)
from .intent import detectar_modo_interaccion, detectar_intencion_semantica
from .local_reply import respuesta_saludo_local
from .prompt_builder import build_prompt
import unicodedata

# Se mantiene por compatibilidad con estrategias de fallback que dependen de conectividad.


logger = structlog.get_logger()

# Cache simple en memoria (por sesión del servidor)
cache: dict = {}


# ============================================================
# Normalización de nivel (UI ↔ Backend)
# - Frontend puede enviar: "Básico", "Intermedio", "Avanzado", "Sin conocimientos"
# - Backend usa: "basica" / "avanzada" para control de tokens, pero también
#   conserva una etiqueta amigable para el prompt.
# ============================================================# ============================================================
# Helpers: respuestas "fundamentos" (operadores/expresiones)
#   - Evita que YELIA rechace preguntas básicas solo porque el
#     ejemplo esté en Python. Responde el concepto y, por defecto,
#     lo conecta con Java 17 (materia).
# ============================================================

_ALLOWED_BINOPS = {
    ast.Add: (lambda a, b: a + b),
    ast.Sub: (lambda a, b: a - b),
    ast.Mult: (lambda a, b: a * b),
    ast.Div: (lambda a, b: a / b),
    ast.FloorDiv: (lambda a, b: a // b),
    ast.Mod: (lambda a, b: a % b),
    ast.Pow: (lambda a, b: a ** b),
}

_ALLOWED_UNARYOPS = {
    ast.UAdd: (lambda a: +a),
    ast.USub: (lambda a: -a),
}

def _safe_eval_arith(expr: str, env: Dict[str, Any]) -> Optional[Any]:
    """Evalúa expresiones aritméticas simples (sin llamadas, sin atributos).
    Devuelve None si detecta algo fuera del subconjunto permitido.
    """
    try:
        tree = ast.parse(expr, mode="eval")
    except Exception:
        return None

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.Name):
            return env.get(node.id, None)
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
            left = _eval(node.left)
            right = _eval(node.right)
            if left is None or right is None:
                return None
            return _ALLOWED_BINOPS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARYOPS:
            val = _eval(node.operand)
            if val is None:
                return None
            return _ALLOWED_UNARYOPS[type(node.op)](val)
        return None

    return _eval(tree)

def _try_fundamentos_respuesta(pregunta: str) -> Optional[str]:
    """Genera una respuesta local para dudas tipo:
    - '¿Cuál es la salida y por qué?' con asignaciones + print(...)
    - Precedencia de operadores (+, *, etc.)
    """
    q = (pregunta or "").strip()
    ql = q.lower()

    # Señales típicas de este tipo de ejercicio
    if not any(s in ql for s in ["print(", "salida", "output", "resultado", "system.out.println", "+", "*", "-", "/", "%"]):
        return None

    # 1) Variables tipo: x = 10, y = 3 (en una línea o varias)
    env: Dict[str, Any] = {}
    for var, num in re.findall(r"\b([a-zA-Z_]\w*)\s*=\s*(-?\d+(?:\.\d+)?)", q):
        env[var] = float(num) if "." in num else int(num)

    # 2) Extraer expresión dentro de print(...) o System.out.println(...)
    expr = None
    m = re.search(r"print\s*\(([^\)]+)\)", q, flags=re.IGNORECASE)
    if m:
        expr = m.group(1).strip()
    if expr is None:
        m = re.search(r"System\.out\.println\s*\(([^\)]+)\)", q, flags=re.IGNORECASE)
        if m:
            expr = m.group(1).strip()

    # 3) Si no hay print, intentar tomar la parte después de '¿' o al final
    if expr is None:
        # Heurística: última 'línea' con operadores
        parts = [p.strip() for p in re.split(r"[\n;]+", q) if p.strip()]
        cand = parts[-1] if parts else ""
        if any(op in cand for op in ["+", "*", "-", "/", "%"]):
            expr = cand

    if not expr:
        return None

    # 4) Evaluar si es aritmética simple
    resultado = _safe_eval_arith(expr, env)
    if resultado is None:
        return None

    # 5) Armar explicación (siempre conectando con Java)
    # Detectar si el usuario pidió explícitamente Python
    pidio_python = "python" in ql or "py" in ql
    salida = str(int(resultado)) if isinstance(resultado, float) and resultado.is_integer() else str(resultado)

    # Explicación de precedencia (multiplicación antes que suma)
    explica = (
        f"**Salida:** `{salida}`\n\n"
        "**Por qué:** en las expresiones aritméticas, `*` tiene **mayor prioridad** que `+`. "
        f"Primero se calcula `y * 2` y luego se suma con `x` (equivale a `x + (y * 2)`).\n\n"
    )

    python_block = (
        "```python\n"
        "x = 10\n"
        "y = 3\n"
        "print(x + y * 2)\n"
        f"# {salida}\n"
        "```\n\n"
    )

    java_block = (
        "```java\n"
        "int x = 10;\n"
        "int y = 3;\n"
        "System.out.println(x + y * 2); // " + salida + "\n"
        "```\n\n"
    )

    # Si pidió Python, muestro Python primero; si no, priorizo Java (materia)
    if pidio_python:
        return "Precedencia de operadores (Fundamentos)\n\n" + explica + python_block + "En **Java** pasa igual:\n\n" + java_block
    return "Precedencia de operadores (Fundamentos)\n\n" + explica + "En **Java 17** (materia) sería así:\n\n" + java_block + "Si también lo necesitas en **Python**, sería:\n\n" + python_block



def _normalizar_nivel_explicacion(raw: str) -> tuple[str, str]:
    """
    Normaliza el nivel recibido desde UI/API.

    Returns:
        (nivel_interno, etiqueta_prompt)
        - nivel_interno: "basica" | "intermedia" | "avanzada"
        - etiqueta_prompt: texto amigable ("Sin conocimientos", "Básico", etc.)
    """
    r = (raw or "").strip()
    if not r:
        return ("basica", "Básico")

    r_low = r.lower()
    r_norm = "".join(c for c in unicodedata.normalize("NFD", r_low) if unicodedata.category(c) != "Mn")

    # Alias ya existentes del backend
    if r_norm in {"basica", "basic", "basico"}:
        return ("basica", "Básico")
    if r_norm in {"avanzada", "advanced", "avanzado"}:
        return ("avanzada", "Avanzado")

    # Etiquetas de UI
    if r_norm in {"intermedio", "intermedia", "medio"}:
        # Internamente lo tratamos como "intermedia" para routing/tokens
        return ("intermedia", "Intermedio")

    if r_norm in {"sin conocimientos", "sin_conocimientos", "ninguno", "cero"}:
        return ("basica", "Sin conocimientos")

    # Fallback
    return ("basica", r)

# ============================================================
# OFFLINE inteligente:
# - Mini FAQ para conceptos típicos (aunque temas.json no tenga match exacto)
# - Match aproximado sobre TEMAS_DISPONIBLES
_OFFLINE_MINI_FAQ: Dict[str, str] = {
    "mvc": (
        "MVC significa Modelo-Vista-Controlador. Es un patrón de arquitectura que separa una aplicación en Modelo, Vista y Controlador.\n"
        "- Modelo: gestiona datos y lógica.\n"
        "- Vista: muestra la interfaz.\n"
        "- Controlador: recibe acciones del usuario y conecta la vista con el modelo.\n\n"
        "**Ejemplo breve en Java:**\n"
        "```java\n"
        "// 1. Modelo: almacena los datos y la lógica\n"
        "class Producto {\n"
        "    private String nombre;\n"
        "    public Producto(String nombre) { this.nombre = nombre; }\n"
        "    public String getNombre() { return nombre; }\n"
        "}\n\n"
        "// 2. Vista: muestra la interfaz\n"
        "class ProductoVista {\n"
        "    public void mostrar(String nombre) {\n"
        "        System.out.println(\"Producto: \" + nombre);\n"
        "    }\n"
        "}\n\n"
        "// 3. Controlador: conecta la vista con el modelo\n"
        "class ProductoControlador {\n"
        "    private Producto modelo;\n"
        "    private ProductoVista vista;\n"
        "    public ProductoControlador(Producto modelo, ProductoVista vista) {\n"
        "        this.modelo = modelo;\n"
        "        this.vista = vista;\n"
        "    }\n"
        "    public void actualizar() {\n"
        "        vista.mostrar(modelo.getNombre());\n"
        "    }\n"
        "}\n"
        "```"
    ),
    "clase": (
        "**Clase (POO):** es una *plantilla/molde* que define **atributos** (datos) y "
        "**métodos** (acciones). A partir de una clase se crean **objetos**.\n\n"
        "**Ejemplo (Java):**\n"
        "```java\n"
        "class Persona {\n"
        "  String nombre;\n"
        "  int edad;\n"
        "  void saludar(){ System.out.println(\"Hola\"); }\n"
        "}\n\n"
        "Persona p = new Persona();\n"
        "p.nombre = \"Erick\";\n"
        "p.saludar();\n"
        "```"
    ),
    "objeto": (
        "**Objeto (POO):** es una *instancia* (un “ejemplar real”) de una clase.\n\n"
        "Ejemplo: si la clase es `Persona`, un objeto es `Persona p = new Persona();`.\n"
        "Cada objeto tiene su propio estado: `p.nombre`, `p.edad`, etc."
    ),
    "uml": (
        "**UML (Lenguaje Unificado de Modelado):** es un conjunto de diagramas estándar para representar "
        "un sistema antes/durante su implementación.\n\n"
        "Los más usados:\n"
        "- **Diagrama de clases** (clases, atributos, métodos, relaciones)\n"
        "- **Casos de uso** (actores y funcionalidades)\n"
        "- **Diagramas de interacción** (secuencia y colaboración)\n\n"
        "UML ayuda a visualizar la arquitectura y diseño del software de manera gráfica."
    ),
    "diagrama de clases": (
        "**Diagrama de clases (UML):** muestra clases, atributos, métodos y relaciones.\n\n"
        "Relaciones típicas:\n"
        "- **Asociación** (usa)\n"
        "- **Agregación** (tiene, pero puede vivir aparte)\n"
        "- **Composición** (parte de, depende totalmente)\n"
        "- **Herencia** (es-un)\n\n"
        "Dime 2–3 clases de tu sistema y te lo dibujo en texto."
    ),
    "herencia": (
        "**Herencia:** es el principio de la POO donde una clase hija reutiliza, hereda y extiende los atributos y métodos de una clase padre.\n\n"
        "```java\n"
        "class Animal { void comer(){} }\n"
        "class Perro extends Animal { void ladrar(){} }\n"
        "```\n"
        "Aquí, `Perro` hereda `comer()` de `Animal` y agrega su propio comportamiento `ladrar()`."
    ),
    "polimorfismo": (
        "**Polimorfismo:** es la capacidad que tienen los objetos de comportarse de diferentes formas según el contexto real, permitiendo que un mismo método actúe de manera distinta en diferentes clases.\n\n"
        "```java\n"
        "Animal a = new Perro();\n"
        "a.comer(); // se ejecuta la versión del Perro si fue sobrescrita\n"
        "```\n"
        "Es un pilar clave para programar utilizando **interfaces** y **clases abstractas**."
    ),
    "poo": (
        "**Programación Orientada a Objetos (POO):** es un paradigma de programación "
        "que organiza el diseño de software alrededor de datos u **objetos**, en lugar de "
        "funciones y lógica.\n\n"
        "Sus 4 pilares fundamentales son:\n"
        "1. **Encapsulamiento:** agrupar datos y métodos que operan sobre ellos, restringiendo el acceso directo.\n"
        "2. **Herencia:** permite a una clase nueva (hija) heredar los atributos y métodos de otra clase (padre).\n"
        "3. **Polimorfismo:** permite que un mismo método o mensaje se comporte de formas distintas según el objeto.\n"
        "4. **Abstracción:** enfocar en las características esenciales de un objeto omitiendo los detalles de implementación.\n\n"
        "Ejemplo: crear una clase `Vehiculo` con atributos como `marca` y métodos como `acelerar()`."
    ),
    "encapsulamiento": (
        "**Encapsulamiento:** es el pilar de la POO que consiste en **proteger u ocultar** el estado interno "
        "de un objeto, impidiendo que sea modificado directamente desde el exterior.\n\n"
        "Se implementa declarando los atributos como **privados** (`private`) y proveyendo métodos públicos "
        "**getters** (para leer) y **setters** (para modificar con validaciones).\n\n"
        "**Ejemplo en Java:**\n"
        "```java\n"
        "class CuentaBancaria {\n"
        "  private double saldo;\n"
        "  public double getSaldo() { return this.saldo; }\n"
        "  public void depositar(double monto) {\n"
        "    if(monto > 0) { this.saldo += monto; }\n"
        "  }\n"
        "}\n"
        "```"
    ),
    "base de datos": (
        "**Base de datos:** es un conjunto organizado de datos pertenecientes a un mismo contexto y almacenados "
        "sistemáticamente para su posterior uso. En programación avanzada, accedemos a bases de datos relacionales "
        "a través de lenguaje SQL.\n\n"
        "En **Java**, esto se realiza mediante:\n"
        "- **JDBC (Java Database Connectivity):** API estándar para conectar la aplicación con la base de datos y ejecutar consultas SQL.\n"
        "- **ORM (Object-Relational Mapping):** frameworks como Hibernate o JPA que mapean objetos Java a tablas de base de datos, evitando escribir SQL manual.\n\n"
        "Dime si necesitas ayuda con alguna consulta SQL específica o la conexión a tu base de datos."
    ),
}


def _obtener_temas_disponibles() -> List[str]:
    """Extrae nombres de temas desde TEMAS_DISPONIBLES."""
    nombres: List[str] = []
    if TEMAS_DISPONIBLES:
        for t in TEMAS_DISPONIBLES:
            nombre = t.get("nombre")
            if nombre and nombre not in nombres:
                nombres.append(nombre)
    return nombres


def _normalize_text(s: str) -> str:
    """Normaliza texto para comparación (minúsculas, sin tildes y espacios consistentes).

    Args:
        s: Texto de entrada.

    Returns:
        Texto normalizado (minúsculas y espacios consistentes).
    """
    s = (s or "").strip().lower()
    s = (
        s.replace("á", "a").replace("é", "e").replace("í", "i")
         .replace("ó", "o").replace("ú", "u").replace("ü", "u")
         .replace("ñ", "n")
     )
    s = re.sub(r"\s+", " ", s)
    return s


def _tokenize(s: str) -> List[str]:
    """Tokeniza un texto simple para matching offline.

    Args:
        s: Texto de entrada.

    Returns:
        Lista de tokens normalizados para matching.
    """
    s = _normalize_text(s)
    tokens = [t for t in re.split(r"[^a-záéíóúñ0-9]+", s) if t]
    return [t for t in tokens if len(t) >= 3]


def _tema_to_blob(tema: Dict[str, Any]) -> str:
    """Construye un 'blob' buscable de un tema.

    Args:
        tema: Estructura/diccionario del tema académico.

    Returns:
        Cadena concatenada y normalizada del contenido del tema.
    """
    nombre = _normalize_text(str(tema.get("nombre", "")))
    definicion = _normalize_text(str(tema.get("definición", "")))
    ventajas = tema.get("ventajas") or []
    ventajas_txt = _normalize_text(" ".join([str(v) for v in ventajas]))
    return f"{nombre} {definicion} {ventajas_txt}".strip()


def _buscar_tema_exacto(tema_nombre: str) -> Optional[Dict[str, Any]]:
    """Busca un tema por nombre exacto en TEMAS_DISPONIBLES.

    Args:
        tema_nombre: Parámetro de entrada.

    Returns:
        Valor retornado por la función.
    """
    if not tema_nombre or not TEMAS_DISPONIBLES:
        return None

    tn = _normalize_text(tema_nombre)
    for t in TEMAS_DISPONIBLES:
        nombre = _normalize_text(t.get("nombre") or "")
        if nombre == tn:
            return t
    return None


def _buscar_tema_aproximado(query: str) -> Optional[Dict[str, Any]]:
    """Busca un tema por coincidencia aproximada (keywords) dentro de TEMAS_DISPONIBLES.

    Args:
        query: Parámetro de entrada.

    Returns:
        Valor retornado por la función.
    """
    if not TEMAS_DISPONIBLES:
        return None

    tokens = _tokenize(query)
    if not tokens:
        return None

    best_score = 0
    best_tema: Optional[Dict[str, Any]] = None

    for tema in TEMAS_DISPONIBLES:
        blob = _tema_to_blob(tema)
        score = 0
        for tk in tokens:
            if tk in blob:
                score += 1
        if score > best_score:
            best_score = score
            best_tema = tema

    qn = _normalize_text(query)
    if best_score >= 2:
        return best_tema
    if len(qn) <= 6 and best_score >= 1:
        return best_tema

    return None


def _respuesta_offline_inteligente(
    pregunta: str,
    tema_identificado: str,
    nivel: str,
    modo_interaccion: str,
    intencion_semantica: str,
) -> Dict[str, Any]:
    """Genera una respuesta offline 'más inteligente' (sin LLM online)."""
    p_norm = _normalize_text(pregunta)

    keyword_mapping = {
        "poo": "poo",
        "programacion orientada a objetos": "poo",
        "encapsula": "encapsulamiento",
        "base de datos": "base de datos",
        "bases de datos": "base de datos",
        "database": "base de datos",
        "db": "base de datos",
        "bd": "base de datos",
        "uml": "uml",
        "polimorfismo": "polimorfismo",
        "herencia": "herencia",
        "clase": "clase",
        "objeto": "objeto",
        "qué es mvc": "mvc",
        "que es mvc": "mvc",
        "modelo vista controlador": "mvc",
        "modelo-vista-controlador": "mvc",
        "arquitectura mvc": "mvc",
        "patrón mvc": "mvc",
        "patron mvc": "mvc",
        "mvc": "mvc",
        "diagrama de clases": "diagrama de clases"
    }

    # Búsqueda ordenada para dar prioridad a términos de búsqueda más específicos
    for keyword in sorted(keyword_mapping.keys(), key=len, reverse=True):
        keyword_norm = _normalize_text(keyword)
        if keyword_norm in p_norm:
            faq_key = keyword_mapping[keyword]
            return {
                "respuesta": _OFFLINE_MINI_FAQ[faq_key],
                "tema": faq_key.capitalize(),
                "nivel": nivel,
                "modo": "local",
                "modo_interaccion": modo_interaccion,
                "intencion": intencion_semantica,
            }

    # 2) Búsqueda en el contenido oficial de las unidades y recursos (course_content.json)
    try:
        from backend.services.course_content_service import load_course_content
        content = load_course_content()
        if content and "units" in content:
            best_resource_match = None
            best_resource_score = 0
            best_unit_title = ""
            
            # Tokenize user question for search scoring
            q_tokens = [tk for tk in p_norm.split() if len(tk) >= 3]
            
            for unit in content.get("units", []):
                unit_title = unit.get("title", "")
                for resource in unit.get("resources", []):
                    title = resource.get("title", "")
                    desc = resource.get("description", "")
                    preview = resource.get("text_preview", "")
                    
                    title_norm = _normalize_text(title)
                    desc_norm = _normalize_text(desc)
                    preview_norm = _normalize_text(preview)
                    
                    score = 0
                    if title_norm and title_norm in p_norm:
                        score += 50
                    for tk in q_tokens:
                        if tk in title_norm:
                            score += 15
                        if tk in desc_norm:
                            score += 5
                        if tk in preview_norm:
                            score += 2
                            
                    # Boost score if "mvc" is in the query and in the resource
                    if "mvc" in p_norm and ("mvc" in title_norm or "mvc" in desc_norm or "mvc" in preview_norm):
                        score += 20
                            
                    if score > best_resource_score:
                        best_resource_score = score
                        best_resource_match = resource
                        best_unit_title = unit_title
            
            if best_resource_match and best_resource_score >= 15:
                title = best_resource_match.get("title", "")
                desc = best_resource_match.get("description", "")
                preview = best_resource_match.get("text_preview", "")
                
                parts = []
                parts.append(f"📌 **{title}** (Relacionado con: {best_unit_title})\n")
                if desc:
                    parts.append(desc)
                if preview:
                    preview_clean = preview.strip()
                    if len(preview_clean) > 800:
                        preview_clean = preview_clean[:800] + "..."
                    parts.append(f"\n{preview_clean}")
                
                return {
                    "respuesta": "\n".join(parts).strip(),
                    "tema": tema_identificado,
                    "nivel": nivel,
                    "modo": "local",
                    "modo_interaccion": modo_interaccion,
                    "intencion": intencion_semantica,
                }
    except Exception as exc:
        logger.warning("Error buscando en course_content.json", error=str(exc))

    # 3) Match exacto / aproximado en temas.json (TEMAS_DISPONIBLES)
    tema = _buscar_tema_exacto(tema_identificado)
    if not tema:
        tema = _buscar_tema_aproximado(tema_identificado) or _buscar_tema_aproximado(pregunta)

    if tema:
        nombre = tema.get("nombre") or tema_identificado
        definicion = (tema.get("definición") or tema.get("definicion") or "").strip()
        ventajas = tema.get("ventajas") or []
        ejemplo = (tema.get("ejemplo") or "").strip()

        partes = []
        partes.append(f"📌 Tema sugerido: **{nombre}**\n")

        if definicion:
            partes.append(f"**Definición:** {definicion}\n")

        if ventajas:
            partes.append("**Puntos clave:**")
            for v in ventajas[:6]:
                partes.append(f"- {v}")
            partes.append("")

        if ejemplo:
            partes.append("**Ejemplo:**")
            partes.append(f"```java\n{ejemplo}\n```")
            partes.append("")

        partes.append("¿Quieres que te haga un **ejercicio** o que lo aplique a un **caso real**? ✅")

        return {
            "respuesta": "\n".join(partes).strip(),
            "tema": nombre,
            "nivel": nivel,
            "modo": "local",
            "modo_interaccion": modo_interaccion,
            "intencion": intencion_semantica,
        }

    # 4) Fallback final
    return {
        "respuesta": "Puedo ayudarte con ese tema. Intenta escribirlo con otras palabras o dime a qué unidad pertenece para orientarte mejor.",
        "tema": tema_identificado,
        "nivel": nivel,
        "modo": "local",
        "modo_interaccion": modo_interaccion,
        "intencion": intencion_semantica,
    }


def procesar_consulta_educativa(
    pregunta: str,
    historial: List[Dict[str, Any]] | None,
    nivel_explicacion: str = "basica",
    usuario: Optional[str] = None,
    ciclo_academico: Optional[str] = None,
    estado_materia: Optional[str] = None,
    original_response: Optional[str] = None,
    unidad_actual: Optional[Any] = None,
) -> Dict[str, Any]:
    try:
        return _procesar_consulta_educativa_impl(
            pregunta=pregunta,
            historial=historial,
            nivel_explicacion=nivel_explicacion,
            usuario=usuario,
            ciclo_academico=ciclo_academico,
            estado_materia=estado_materia,
            original_response=original_response,
            unidad_actual=unidad_actual,
        )
    except Exception as e:
        logger.exception("Error critico en procesar_consulta_educativa, activando fallback local", error=str(e))
        try:
            offline = _respuesta_offline_inteligente(
                pregunta=pregunta,
                tema_identificado="Programación Avanzada",
                nivel=nivel_explicacion or "basica",
                modo_interaccion="normal",
                intencion_semantica="otro",
            )
            return {
                "ok": True,
                "respuesta": offline["respuesta"],
                "reply": offline["respuesta"],
                "tema": "Programación Avanzada",
                "nivel": nivel_explicacion or "basica",
                "proveedor": "local",
                "modo": "local",
                "modo_interaccion": "normal",
                "intencion": "otro",
                "proveedores_fallidos": ["exception"],
            }
        except Exception:
            return {
                "ok": True,
                "respuesta": "Puedo ayudarte con ese tema. Intenta escribirlo con otras palabras o dime a qué unidad pertenece para orientarte mejor.",
                "reply": "Puedo ayudarte con ese tema. Intenta escribirlo con otras palabras o dime a qué unidad pertenece para orientarte mejor.",
                "tema": "Programación Avanzada",
                "nivel": nivel_explicacion or "basica",
                "proveedor": "local",
                "modo": "local",
                "modo_interaccion": "normal",
                "intencion": "otro",
                "proveedores_fallidos": ["fatal_exception"],
            }


def obtener_recordatorio_diagnostico(usuario: str) -> str:
    """Retorna un recordatorio amigable personalizado con los temas a reforzar según el diagnóstico."""
    if not usuario:
        return "\n\n**Recordatorio de YELIA:** No olvides realizar tu **Diagnóstico inicial** para identificar qué temas necesitas reforzar."

    try:
        from backend.db.session import db_session
        import json
        with db_session(write=False) as conn:
            cur = conn.cursor()
            # Query latest diagnostic attempt
            cur.execute(
                "SELECT answers_json FROM diagnostic_attempts WHERE LOWER(usuario) = LOWER(?) ORDER BY id DESC LIMIT 1;",
                (usuario,)
            )
            row = cur.fetchone()
            if row:
                answers_json = row["answers_json"]
                if answers_json:
                    details = json.loads(answers_json)
                    missed = []
                    for item in details:
                        if not item.get("correct", True) and item.get("topic"):
                            t_name = item["topic"]
                            if t_name not in missed:
                                missed.append(t_name)
                    if missed:
                        if len(missed) == 1:
                            temas_str = f"**{missed[0]}**"
                        elif len(missed) == 2:
                            temas_str = f"**{missed[0]}** y **{missed[1]}**"
                        else:
                            temas_str = ", ".join(f"**{t}**" for t in missed[:-1]) + f" y **{missed[-1]}**"
                        return f"\n\n**Recordatorio de YELIA:** No olvides revisar y reforzar los temas que presentaron mayor dificultad en tu diagnóstico, especialmente {temas_str}."
                    else:
                        return "\n\n**Recordatorio de YELIA:** No olvides revisar y reforzar los temas de la materia para seguir avanzando con tu excelente desempeño en el diagnóstico."

            # Fallback: check if they have at least level_materia in progress
            cur.execute("SELECT nivel_materia FROM progreso WHERE LOWER(usuario) = LOWER(?);", (usuario,))
            row_p = cur.fetchone()
            if row_p and row_p["nivel_materia"] and row_p["nivel_materia"] != "Por diagnosticar":
                lvl = row_p["nivel_materia"]
                if lvl in ["Sin conocimientos", "Basico"]:
                    return "\n\n**Recordatorio de YELIA:** No olvides revisar y reforzar los temas que presentaron mayor dificultad en tu diagnóstico, especialmente **Clases y Objetos**."
                elif lvl == "Intermedio":
                    return "\n\n**Recordatorio de YELIA:** No olvides revisar y reforzar los temas que presentaron mayor dificultad en tu diagnóstico, especialmente **Herencia** y **Polimorfismo**."
                else:
                    return "\n\n**Recordatorio de YELIA:** No olvides revisar y reforzar los temas que presentaron mayor dificultad en tu diagnóstico, especialmente **Patrones de Diseño**."
    except Exception:
        pass

    return "\n\n**Recordatorio de YELIA:** No olvides realizar tu **Diagnóstico inicial** para identificar qué temas necesitas reforzar."


def _procesar_consulta_educativa_impl(
    pregunta: str,
    historial: List[Dict[str, Any]] | None,
    nivel_explicacion: str = "basica",
    usuario: Optional[str] = None,
    ciclo_academico: Optional[str] = None,
    estado_materia: Optional[str] = None,
    original_response: Optional[str] = None,
    unidad_actual: Optional[Any] = None,
) -> Dict[str, Any]:
    """Punto de entrada principal del motor NLP (siempre responde, incluso offline)."""
    # 1) Sanitización / normalización
    pregunta = (pregunta or "").strip()
    historial = normalizar_historial(historial or [])

    nivel_interno, nivel_label = _normalizar_nivel_explicacion(nivel_explicacion)

    # nivel_interno controla tokens/comportamiento; nivel_label se usa en el prompt
    nivel = nivel_label
    tema_identificado = "Programación Avanzada"

    if not pregunta:
        return {
            "ok": True,
            "respuesta": "No he recibido ninguna pregunta. Escríbeme tu duda de Programación Avanzada 😊",
            "reply": "No he recibido ninguna pregunta. Escríbeme tu duda de Programación Avanzada 😊",
            "tema": tema_identificado,
            "nivel": nivel,
            "proveedor": "local",
            "modo": "local",  # alias para frontend
            "modo_interaccion": "normal",
            "intencion": "otro",
            "proveedores_fallidos": [],
        }

    # 2) Límite de longitud
    max_len = max(int(os.getenv("CHAT_MAX_MESSAGE_LEN", "20000")), 20000)
    if len(pregunta) > max_len:
        pregunta = pregunta[:max_len] + " [...]"

    pregunta_lower = pregunta.lower()

    # 3) Detección modo + intención
    modo_interaccion = detectar_modo_interaccion(pregunta_lower)
    intencion_semantica = detectar_intencion_semantica(pregunta_lower)

    # 3.1) Continuación conversacional
    if intencion_semantica == "continuacion":
        pista = extraer_ultimo_tema_relevante(historial)
        tema_pista = identificar_tema_desde_texto(pista) if pista else None

        if tema_pista:
            pregunta = f"El estudiante pidió continuar. Continúa explicando sobre: {tema_pista}. Usa el historial."
        elif tema_identificado:
            pregunta = f"El estudiante pidió continuar. Continúa explicando sobre: {tema_identificado}. Usa el historial."
        else:
            pregunta = "El estudiante pidió continuar. Continúa con el tema anterior y haz una pregunta guía."
        pregunta_lower = pregunta.lower()

    # Saludo corto -> local
    if intencion_semantica == "saludo" and len(pregunta_lower) <= 40:
        r = respuesta_saludo_local(usuario)
        return {
            "ok": True,
            "respuesta": r,
            "reply": r,
            "tema": tema_identificado,
            "nivel": nivel,
            "proveedor": "local",
            "modo": "local",
            "modo_interaccion": "normal",
            "intencion": "saludo",
            "proveedores_fallidos": [],
        }

    # 4) Dominio
    dominio_status = match_domain(pregunta_lower)

    if intencion_semantica == "continuacion":
        dominio_status = "core"

    if (dominio_status == "off") and tiene_senal_materia(pregunta_lower):
        dominio_status = "core"
    if (dominio_status == "off") and es_ambigua_pero_probable_materia(pregunta_lower):
        dominio_status = "core"

    if dominio_status == "off":
        resp_fund = _try_fundamentos_respuesta(pregunta)
        if resp_fund:
            return {
                "ok": True,
                "respuesta": resp_fund,
                "reply": resp_fund,
                "tema": "Fundamentos",
                "nivel": nivel,
                "proveedor": "local",
                "modo": "core",
                "modo_interaccion": "normal",
                "intencion": "fundamentos",
                "proveedores_fallidos": [],
            }
        if re.fullmatch(r"[\W_0-9]+", pregunta_lower) or len(pregunta_lower) < 2:
            r = (
                "No te entendí 😅\n\n"
                "Escríbeme tu duda así: **¿Qué es ___?** o pega tu **error/código** "
                "y te ayudo paso a paso (POO, Java, UML, MVC, BD/ORM, etc.)."
            )
            return {
                "ok": True,
                "respuesta": r,
                "reply": r,
                "tema": tema_identificado,
                "nivel": nivel,
                "proveedor": "local",
                "modo": "offtopic",
                "modo_interaccion": "normal",
                "intencion": "otro",
                "proveedores_fallidos": [],
            }

        r = (
            "Estoy especializada en **Programación Avanzada** (POO, Java, UML/MVC, Archivos, BD/ORM, depuración).\n\n"
            "Si quieres, dime el tema exacto o pega tu código/error y te ayudo paso a paso ✅"
        )
        return {
            "ok": True,
            "respuesta": r,
            "reply": r,
            "tema": tema_identificado,
            "nivel": nivel,
            "proveedor": "local",
            "modo": "offtopic",
            "modo_interaccion": "normal",
            "intencion": "otro",
            "proveedores_fallidos": [],
        }

    # 5) Progreso (omitido aquí: igual que tu archivo)
    puntos = 0
    temas_aprendidos: List[str] = []

    if usuario:
        try:
            with db_session(write=False) as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT puntos, temas_aprendidos, ciclo_academico, estado_materia "
                    "FROM progreso WHERE usuario = ?",
                    (usuario,),
                )
                row = cur.fetchone()

            if row:
                puntos = row["puntos"] or 0

                try:
                    temas_aprendidos = json.loads(row["temas_aprendidos"]) if row["temas_aprendidos"] else []
                    if not isinstance(temas_aprendidos, list):
                        temas_aprendidos = []
                except json.JSONDecodeError:
                    temas_aprendidos = []

                if not ciclo_academico:
                    ciclo_academico = row["ciclo_academico"]
                if not estado_materia:
                    estado_materia = row["estado_materia"]

        except Exception as e:
            logger.warning("No se pudo leer el progreso del estudiante", usuario=usuario, error=str(e))
            puntos = 0
            temas_aprendidos = []

    # 5.5) Nickname (opcional) desde perfil avanzado
    usuario_display = usuario or "Estudiante"
    if isinstance(usuario_display, str) and usuario_display.startswith(("Anon-", "GUEST-")):
        usuario_display = "Invitado 1"
    try:
        from backend.repositories.student_profile_repo import get_profile
        prof = get_profile(usuario) if usuario else {}
        nick = (prof or {}).get("nickname")
        if isinstance(nick, str) and nick.strip():
            usuario_display = nick.strip()
    except Exception:
        pass

    # 6) Contexto
    contexto = construir_contexto_desde_historial(historial)
    ultimo_foco = extraer_ultimo_tema_relevante(historial)
    ciclo_academico = ciclo_academico or "Séptimo Semestre"
    estado_materia = estado_materia or "La estoy cursando actualmente"
    tema_identificado = identificar_tema_desde_texto(pregunta)

    if intencion_semantica == "continuacion" and ultimo_foco:
        try:
            tema_del_hilo = identificar_tema_desde_texto(ultimo_foco)
            if tema_del_hilo:
                tema_identificado = tema_del_hilo
        except Exception:
            pass

    # 7) Prompt
    prompt = build_prompt(
        usuario=usuario_display,
        ciclo_academico=ciclo_academico,
        estado_materia=estado_materia,
        puntos=puntos,
        temas_aprendidos=temas_aprendidos,
        nivel=nivel,
        tema_identificado=tema_identificado,
        modo_interaccion=modo_interaccion,
        intencion_semantica=intencion_semantica,
        dominio_status=dominio_status,
        contexto=contexto,
        ultimo_foco=ultimo_foco,
        original_response=original_response,
        unidad_actual=unidad_actual,
    )

    # 8) Cache key
    last_hint = extraer_ultima_pista_historial(historial)
    last_hint_hash = hash_texto_corto(last_hint, n=10) if last_hint else ""
    qhash = hash_texto_corto(pregunta, n=16)

    usuario_key = (usuario or "anon").strip() or "anon"
    cache_key = (
        f"{usuario_key}:{qhash}:{nivel}:{tema_identificado}:"
        f"{ciclo_academico}:{estado_materia}:"
        f"{modo_interaccion}:{intencion_semantica}:{last_hint_hash}"
    )

    if cache_key in cache:
        resultado_cache = cache[cache_key]
        resultado_cache.setdefault("ok", True)
        resultado_cache.setdefault("reply", resultado_cache.get("respuesta", ""))
        resultado_cache.setdefault("modo", resultado_cache.get("proveedor", "cache"))
        resultado_cache.setdefault("modo_interaccion", modo_interaccion)
        resultado_cache.setdefault("intencion", intencion_semantica)
        resultado_cache.setdefault("proveedor", resultado_cache.get("proveedor", "cache"))
        resultado_cache.setdefault("proveedores_fallidos", resultado_cache.get("proveedores_fallidos", []))
        return resultado_cache

    # 9) Tokens  
    pedir_largo = any(x in pregunta_lower for x in (
        "muy detallad",
        "extens",
        "no lo resumas",
        "no resumas",
        "sin resumir",
        "completo",
        "bien detallad",
        "minimo",
        "mínimo",
        "1200 palabras",
        "1000 palabras",
        "secciones",
        "uml",
        "plantuml",
        "tarea",
        "actividad",
        "taller",
        "ejercicio completo",
        "solucion",
        "solución",
        "codigo completo",
        "código completo",
        "implementacion completa",
        "implementación completa",
        "requisitos",
    ))

    if pedir_largo:
        max_tokens = 5000
    else:
        if modo_interaccion == "quiz":
            max_tokens = 2500
        elif modo_interaccion == "debug":
            max_tokens = 3500
        elif nivel_interno == "avanzada" or "explícame más" in pregunta_lower or "explicame mas" in pregunta_lower:
            max_tokens = 4000
        elif nivel_interno == "intermedia":
            max_tokens = 3000
        else:
            max_tokens = 3000

    # ============================================================
    # MODO HÍBRIDO (centralizado en provider_router) ...
    # ============================================================

    proveedores_fallidos: List[str] = []
    proveedor_usado = "local"

    try:
        out = seleccionar_proveedor(
            prompt_system=prompt,
            pregunta_user=pregunta,
            max_tokens=max_tokens,
            modo_interaccion=modo_interaccion,
            nivel=nivel,
        )
        respuesta = (out or {}).get("respuesta", "") or ""
        proveedor_usado = (out or {}).get("proveedor", "local") or "local"
        proveedores_fallidos = list((out or {}).get("proveedores_fallidos", []) or [])
    except Exception as e:
        logger.warning("Router NLP falló (fallback a offline)", error=str(e))
        respuesta = ""
        proveedor_usado = "local"
        proveedores_fallidos = ["router:exception"]

    if not respuesta:
        offline = _respuesta_offline_inteligente(
            pregunta=pregunta,
            tema_identificado=tema_identificado or "Programación Avanzada",
            nivel=nivel,
            modo_interaccion=modo_interaccion,
            intencion_semantica=intencion_semantica,
        )
        respuesta = offline["respuesta"]
        proveedor_usado = "local"

    # Recordatorio personalizado según el diagnóstico
    from backend.nlp.domain import es_tema_de_programacion_avanzada
    if respuesta and es_tema_de_programacion_avanzada(tema_identificado):
        recom = obtener_recordatorio_diagnostico(usuario)
        if recom and recom.strip() not in respuesta:
            respuesta = respuesta.strip() + recom

    resultado = {
        "ok": True,
        "respuesta": respuesta,
        "reply": respuesta,
        "tema": tema_identificado,
        "nivel": nivel,
        "proveedor": proveedor_usado,
        "modo": proveedor_usado,
        "modo_interaccion": modo_interaccion,
        "intencion": intencion_semantica,
        "proveedores_fallidos": proveedores_fallidos,
    }

    cache[cache_key] = resultado
    return resultado
