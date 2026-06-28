"""
Proyecto: YELIA4AP
Archivo: backend/tests/conftest.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
from __future__ import annotations

"""
Configuración compartida de pruebas automatizadas.

Este archivo define fixtures comunes utilizadas por pytest
para inicializar el backend de YELIA4AP en un entorno de pruebas.
"""

# =====================================
# Imports
# =====================================

import os
import sys
import tempfile
import pytest

# Force a clean, isolated temporary database for all test runs
test_db_path = os.path.join(tempfile.gettempdir(), "test_yelia_isolated.db")
if os.path.exists(test_db_path):
    try:
        os.remove(test_db_path)
    except Exception:
        pass
os.environ["DATABASE_PATH"] = test_db_path
os.environ["DB_PATH"] = test_db_path
os.environ["FLASK_ENV"] = "testing"

# Asegura que la raíz del proyecto esté disponible en el PYTHONPATH
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import create_app


@pytest.fixture()
# =====================================
# Funciones / Clases
# =====================================

def client(tmp_path):
    """
    Crea un cliente de pruebas para la aplicación Flask.

    - Inicializa la aplicación en modo testing.
    - Usa una base de datos temporal para evitar afectar datos reales.
    """
    os.environ.setdefault("FLASK_ENV", "testing")

    # Base de datos temporal para las pruebas
    test_db = tmp_path / "test_yelia.db"

    app = create_app()
    app.config.update(
        TESTING=True,
        DATABASE_PATH=str(test_db),
    )
    return app.test_client()
