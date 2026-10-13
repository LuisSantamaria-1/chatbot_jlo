import os
import sys
import pytest
import pandas as pd

import secrets

# Asegurar raíz del proyecto en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configurar SECRET_KEY dinámicamente en memoria para el entorno de pruebas si no existe
if not os.environ.get("SECRET_KEY"):
    os.environ["SECRET_KEY"] = secrets.token_hex(32)

# Sincronizar ADMIN_PASSWORD desde el registro si la consola actual no lo tiene cargado
if not os.environ.get("ADMIN_PASSWORD") and sys.platform.startswith("win"):
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment")
        reg_val, _ = winreg.QueryValueEx(key, "ADMIN_PASSWORD")
        if reg_val:
            os.environ["ADMIN_PASSWORD"] = reg_val
    except Exception:
        pass

# Registro centralizado de resultados para pruebas_resultados.csv
_RESULTADOS = []


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
    """
    Guarda el id máximo existente en conversaciones_log al inicio de pytest
    y al finalizar elimina únicamente las filas generadas durante la ejecución (id > max_id_inicio).
    """
    max_id_inicio = 0
    try:
        from app import app
        from backend.models import db, ConversacionLog
        from sqlalchemy import func
        with app.app_context():
            res = db.session.query(func.max(ConversacionLog.id)).scalar()
            max_id_inicio = res or 0
    except Exception as e:
        print(f"\n[conftest] Error obteniendo max_id inicial: {e}")

    yield

    try:
        from app import app
        from backend.models import db
        from sqlalchemy import text
        with app.app_context():
            with db.engine.begin() as conn:
                res = conn.execute(text(f"DELETE FROM conversaciones_log WHERE id > {max_id_inicio}"))
                filas = res.rowcount
            print(f"\n[conftest] Eliminadas {filas} filas de conversaciones_log generadas en las pruebas (id > {max_id_inicio}).")
    except Exception as e:
        print(f"\n[conftest] Error en limpieza post-sesion: {e}")


def pytest_sessionfinish(session, exitstatus):
    if _RESULTADOS:
        csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "pruebas_resultados.csv"))
        df_nuevos = pd.DataFrame(_RESULTADOS)
        if os.path.exists(csv_path):
            try:
                df_previo = pd.read_csv(csv_path)
                # Concatenar y deduplicar por id preservando el registro más reciente
                df_combinado = pd.concat([df_previo, df_nuevos], ignore_index=True)
                df_combinado = df_combinado.drop_duplicates(subset=["id"], keep="last")
                df_combinado.to_csv(csv_path, index=False, encoding="utf-8")
                print(f"\n[conftest] Guardados {len(df_combinado)} casos acumulados en: {csv_path}")
            except Exception as e:
                print(f"[conftest] Advertencia leyendo CSV previo: {e}")
        else:
            df_nuevos.to_csv(csv_path, index=False, encoding="utf-8")
            print(f"\n[conftest] Guardados {len(_RESULTADOS)} casos en: {csv_path}")
