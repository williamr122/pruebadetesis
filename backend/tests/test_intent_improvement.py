import json
import pytest
from backend.db.session import db_session, init_db
from backend.nlp.intent import es_consulta_ventajas_utilidad, detectar_intencion_semantica
from backend.nlp.domain import (
    es_tema_de_programacion_avanzada,
    tiene_tema_de_las_4_unidades,
    es_pregunta_ventajas_utilidad_unidades,
    match_domain
)
from backend.nlp.core import obtener_recordatorio_diagnostico, procesar_consulta_educativa

# Initialize the test DB schema
init_db()


def test_es_consulta_ventajas_utilidad():
    # Test cases that should match
    assert es_consulta_ventajas_utilidad("ventajas de la herencia") is True
    assert es_consulta_ventajas_utilidad("beneficios del polimorfismo") is True
    assert es_consulta_ventajas_utilidad("para qué sirve el encapsulamiento") is True
    assert es_consulta_ventajas_utilidad("cuál es la utilidad de los constructores") is True
    assert es_consulta_ventajas_utilidad("por qué es importante el mvc") is True
    assert es_consulta_ventajas_utilidad("qué aporta el diagrama de secuencia") is True
    assert es_consulta_ventajas_utilidad("en qué ayudan las interfaces") is True
    assert es_consulta_ventajas_utilidad("en qué ayuda la persistencia") is True
    assert es_consulta_ventajas_utilidad("dime los beneficios de usar colecciones") is True

    # Test cases that should NOT match
    assert es_consulta_ventajas_utilidad("qué es la herencia") is False
    assert es_consulta_ventajas_utilidad("hola yelia") is False
    assert es_consulta_ventajas_utilidad("hazme un ejemplo de código en java") is False


def test_detectar_intencion_semantica():
    assert detectar_intencion_semantica("ventajas de herencia") == "teoria"
    assert detectar_intencion_semantica("para que sirve poo") == "teoria"


def test_es_tema_de_programacion_avanzada():
    assert es_tema_de_programacion_avanzada("Clases y Objetos") is True
    assert es_tema_de_programacion_avanzada("Herencia") is True
    assert es_tema_de_programacion_avanzada("Patrón MVC") is True
    assert es_tema_de_programacion_avanzada("Bases de Datos y ORM") is True
    assert es_tema_de_programacion_avanzada("Programación Avanzada") is True
    assert es_tema_de_programacion_avanzada("Cocina Italiana") is False


def test_tiene_tema_de_las_4_unidades():
    assert tiene_tema_de_las_4_unidades("herencia en java") is True
    assert tiene_tema_de_las_4_unidades("diagrama de clases") is True
    assert tiene_tema_de_las_4_unidades("persistencia con hibernate") is True
    assert tiene_tema_de_las_4_unidades("historia universal") is False


def test_es_pregunta_ventajas_utilidad_unidades():
    assert es_pregunta_ventajas_utilidad_unidades("ventajas de la herencia") is True
    assert es_pregunta_ventajas_utilidad_unidades("cuál es la utilidad de los constructores") is True
    assert es_pregunta_ventajas_utilidad_unidades("ventajas de cocinar pasta") is False


def test_match_domain():
    assert match_domain("ventajas de la herencia") == "core"
    assert match_domain("en qué ayuda la persistencia") == "core"
    assert match_domain("ventajas de cocinar pasta") == "off"


def test_obtener_recordatorio_diagnostico_no_user(monkeypatch):
    recom = obtener_recordatorio_diagnostico("")
    assert "Diagnóstico inicial" in recom


def test_obtener_recordatorio_diagnostico_with_db(monkeypatch):
    test_user = "test_student_diagnostico_1"
    from backend.routes.diagnostic_routes import _ensure_attempts_table
    _ensure_attempts_table()
    
    with db_session(write=True) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM diagnostic_attempts WHERE LOWER(usuario) = ?;", (test_user,))
        cur.execute("DELETE FROM progreso WHERE LOWER(usuario) = ?;", (test_user,))
        conn.commit()

    recom = obtener_recordatorio_diagnostico(test_user)
    assert "Diagnóstico inicial" in recom

    with db_session(write=True) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO progreso (usuario, nivel_materia) VALUES (?, ?);", (test_user, "Intermedio"))
        conn.commit()
    recom = obtener_recordatorio_diagnostico(test_user)
    assert "especialmente **Herencia** y **Polimorfismo**" in recom

    with db_session(write=True) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM progreso WHERE LOWER(usuario) = ?;", (test_user,))
        answers = [
            {"id": "poo-01", "topic": "Clases y Objetos", "correct": False},
            {"id": "poo-02", "topic": "Encapsulamiento", "correct": False},
            {"id": "poo-03", "topic": "Herencia", "correct": True}
        ]
        cur.execute(
            "INSERT INTO diagnostic_attempts (usuario, alias, answers_json, feedback) VALUES (?, ?, ?, ?);",
            (test_user, "TestStudent", json.dumps(answers), "feedback_text")
        )
        conn.commit()

    recom = obtener_recordatorio_diagnostico(test_user)
    assert "especialmente **Clases y Objetos** y **Encapsulamiento**" in recom

    with db_session(write=True) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM diagnostic_attempts WHERE LOWER(usuario) = ?;", (test_user,))
        answers = [
            {"id": "poo-01", "topic": "Clases y Objetos", "correct": True}
        ]
        cur.execute(
            "INSERT INTO diagnostic_attempts (usuario, alias, answers_json, feedback) VALUES (?, ?, ?, ?);",
            (test_user, "TestStudent", json.dumps(answers), "feedback_text")
        )
        conn.commit()
    recom = obtener_recordatorio_diagnostico(test_user)
    assert "excelente desempeño en el diagnóstico" in recom

    with db_session(write=True) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM diagnostic_attempts WHERE LOWER(usuario) = ?;", (test_user,))
        cur.execute("DELETE FROM progreso WHERE LOWER(usuario) = ?;", (test_user,))
        conn.commit()


def test_procesar_consulta_educativa_integration(monkeypatch):
    def fake_seleccionar_proveedor(*args, **kwargs):
        return {"respuesta": "La herencia es un concepto de POO.", "proveedor": "local"}
    monkeypatch.setattr("backend.nlp.core.seleccionar_proveedor", fake_seleccionar_proveedor)

    res = procesar_consulta_educativa(
        pregunta="ventajas de la herencia",
        historial=[],
        nivel_explicacion="basica",
        usuario="test_student_integration"
    )
    assert res["ok"] is True
    assert "La herencia es un concepto de POO." in res["respuesta"]
    assert "Diagnóstico inicial" in res["respuesta"]
