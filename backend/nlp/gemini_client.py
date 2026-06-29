"""
Proyecto: YELIA4AP
Archivo: backend/nlp/gemini_client.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
from __future__ import annotations

"""
Archivo: backend/nlp/gemini_client.py
Proyecto: YELIA4AP
Última revisión: 2026-02-10

Componentes de procesamiento de lenguaje natural (NLU/NLP) del backend.

Convenciones:
- Funciones pequeñas, nombres descriptivos y manejo de errores explícito.
- Evitar prints en producción: usar logging si aplica.
"""


#
# Archivo: backend/nlp/gemini_client.py
# Rol: Módulo del backend (Flask) de YELIA4AP.


"""Gemini Client
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.

backend/nlp/gemini_client.py

Cliente Gemini (Google) — YELIA

Objetivo:
- Soportar 2 SDKs distintos (porque en PCs / labs a veces hay uno u otro):
  1) SDK NUEVO:   google-genai     -> from google import genai; client.models.generate_content(...)
  2) SDK CLÁSICO: google-generativeai -> import google.generativeai as genai; GenerativeModel(...).generate_content(...)

- Si no hay SDK o no hay API key, retorna "" (cadena vacía) para que el router use fallback.
"""
# =====================================
# Imports
# =====================================


import logging
from typing import Optional, Any


# =====================================
# Configuración / Constantes
# =====================================
from .config import GEMINI_API_KEY, GEMINI_MODEL

_logger = logging.getLogger(__name__)

# Flags de disponibilidad
_enabled: bool = False
_mode: str = "none"  # "google-genai" | "google-generativeai" | "none"

# Cliente / modelo (dependiendo del SDK)
_client: Optional[Any] = None
_model_obj: Optional[Any] = None

# ------------------------------------------------------
# Intento 1: SDK NUEVO (google-genai)
# ------------------------------------------------------
try:
    # Requiere: pip install google-genai
    from google import genai  # type: ignore
    from google.genai import types  # type: ignore

    if GEMINI_API_KEY:
        _client = genai.Client(api_key=GEMINI_API_KEY)
        _enabled = True
        _mode = "google-genai"
        _logger.info("Gemini listo (google-genai) | model=%s", GEMINI_MODEL)
    else:
        _logger.info("Gemini deshabilitado (GEMINI_API_KEY ausente)")

except Exception:
    # Si falla import o algo del SDK nuevo, probamos el clásico
    _client = None

# ------------------------------------------------------
# Intento 2: SDK CLÁSICO (google-generativeai)
# ------------------------------------------------------
if not _enabled:
    try:
        # Requiere: pip install google-generativeai
        import google.generativeai as genai_old  # type: ignore

        if GEMINI_API_KEY:
            genai_old.configure(api_key=GEMINI_API_KEY)
            _model_obj = genai_old.GenerativeModel(GEMINI_MODEL)
            _enabled = True
            _mode = "google-generativeai"
            _logger.info("Gemini listo (google-generativeai) | model=%s", GEMINI_MODEL)
        else:
            _logger.info("Gemini deshabilitado (GEMINI_API_KEY ausente)")

    except Exception:
        _model_obj = None
# =====================================
# Funciones / Clases
# =====================================



def llamar_gemini(
    prompt_system: str,
    pregunta_user: str,
    max_tokens: int,
    temperature: float = 0.3,
) -> str:
    """
    Retorna texto generado por Gemini.
    Devuelve "" si:
    - no está disponible Gemini (sin SDK o sin API key), o
    - hubo error al llamar al proveedor.
    """
    if not _enabled:
        return ""

    model_to_use = GEMINI_MODEL or "gemini-2.5-pro"

    # Intento 1: Modelo principal
    try:
        _logger.info("Usando Gemini: %s", model_to_use)
        res = _llamar_api_con_modelo(model_to_use, prompt_system, pregunta_user, max_tokens, temperature)
        if res:
            _logger.info("Gemini respondió con modelo: %s", model_to_use)
        return res
    except Exception as e:
        _logger.warning("Error llamando Gemini con %s: %s", model_to_use, str(e))
        # Intento 2: Fallback automático a gemini-2.5-flash
        if model_to_use != "gemini-2.5-flash":
            fallback_model = "gemini-2.5-flash"
            _logger.info("Fallo con %s. Realizando fallback automáticamente a %s", model_to_use, fallback_model)
            _logger.info("Usando Gemini: %s", fallback_model)
            try:
                res = _llamar_api_con_modelo(fallback_model, prompt_system, pregunta_user, max_tokens, temperature)
                if res:
                    _logger.info("Gemini respondió con modelo: %s", fallback_model)
                return res
            except Exception as ex:
                _logger.exception("Error llamando Gemini con fallback %s: %s", fallback_model, str(ex))
                return ""
        else:
            return ""


def _llamar_api_con_modelo(
    model_name: str,
    prompt_system: str,
    pregunta_user: str,
    max_tokens: int,
    temperature: float,
) -> str:
    if _mode == "google-genai":
        # SDK NUEVO
        from google.genai import types  # type: ignore

        if _client is None:
            raise RuntimeError("Client is not initialized")

        resp = _client.models.generate_content(
            model=model_name,
            contents=pregunta_user,
            config=types.GenerateContentConfig(
                system_instruction=prompt_system,
                temperature=float(temperature),
                max_output_tokens=int(max_tokens),
                top_p=0.9,
            ),
        )
        text = getattr(resp, "text", "") or ""
        return str(text).strip()

    elif _mode == "google-generativeai":
        # SDK CLÁSICO
        import google.generativeai as genai_old  # type: ignore

        model_obj = genai_old.GenerativeModel(model_name)
        prompt = f"{prompt_system}\n\nUsuario:\n{pregunta_user}".strip()
        resp = model_obj.generate_content(
            prompt,
            generation_config={
                "temperature": float(temperature),
                "max_output_tokens": int(max_tokens),
                "top_p": 0.9,
            },
        )
        text = getattr(resp, "text", "") or ""
        return str(text).strip()

    raise RuntimeError("No Gemini mode active")
