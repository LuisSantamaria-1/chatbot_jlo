import os
import sys
import csv
from pathlib import Path
import pytest

import secrets

# Todas las pruebas usan una BD efímera; jamás el catálogo o logs de MySQL.
# Debe configurarse ANTES de importar app/config durante la colección.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ADMIN_PASSWORD"] = secrets.token_urlsafe(24)
os.environ["ADMIN_INITIAL_PASSWORD"] = os.environ["ADMIN_PASSWORD"]
# La carga pesada opcional se verifica por separado, no en cada proceso pytest.
os.environ["CHAT_SEMANTICA"] = "0"

# Asegurar raíz del proyecto en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configurar SECRET_KEY dinámicamente en memoria para el entorno de pruebas si no existe
if not os.environ.get("SECRET_KEY"):
    os.environ["SECRET_KEY"] = secrets.token_hex(32)

# Registro en memoria; el CSV solo se genera al pedir --reporte-csv RUTA.
_RESULTADOS = []


def pytest_addoption(parser):
    parser.addoption("--reporte-csv", metavar="RUTA", help="Exportar los casos registrados a un CSV.")


@pytest.fixture(autouse=True)
def _limpiar_limite_intentos_login():
    """Reinicia el contador de intentos fallidos antes y después de cada prueba."""
    from backend.admin.seguridad import reset_intentos_login
    reset_intentos_login()
    yield
    reset_intentos_login()


def registrar_caso(test_id, grupo, entrada, esperado, obtenido, confianza, estado):
    _RESULTADOS.append({
        "id": test_id,
        "grupo": grupo,
        "entrada": str(entrada),
        "esperado": str(esperado),
        "obtenido": str(obtenido),
        "confianza": f"{confianza:.4f}" if isinstance(confianza, (int, float)) else str(confianza),
        "estado": estado
    })


@pytest.fixture
def registrar():
    return registrar_caso


@pytest.fixture(scope="session", autouse=True)
def limpiar_conversaciones_test_session():
    """Carga el CSV completo en SQLite en memoria y lo descarta al terminar."""
    from app import app
    from backend.models import db
    from backend.models.poblado import inicializar_bd
    app.config["TESTING"] = True
    # La auditoría se comprueba en SQLite/caplog. No rotar el archivo que usa
    # el servidor real de Windows mientras se ejecutan pruebas en paralelo.
    import logging
    from logging.handlers import RotatingFileHandler
    for logger in (logging.getLogger('backend'), app.logger):
        for handler in list(logger.handlers):
            if isinstance(handler, RotatingFileHandler):
                logger.removeHandler(handler)
                handler.close()
    with app.app_context():
        inicializar_bd()
        yield
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


def pytest_sessionfinish(session, exitstatus):
    ruta = session.config.getoption("--reporte-csv")
    if ruta and _RESULTADOS:
        csv_path = Path(ruta).expanduser().resolve()
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with csv_path.open("w", newline="", encoding="utf-8") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=list(_RESULTADOS[0]))
            escritor.writeheader()
            escritor.writerows(_RESULTADOS)
        print(f"\n[conftest] Guardados {len(_RESULTADOS)} casos en: {csv_path}")
