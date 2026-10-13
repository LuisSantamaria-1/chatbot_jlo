"""
tests/test_log.py
-----------------
Batería de pruebas unitarias y de integración para el registro de conversaciones (logs),
persistencia de auditoría y trazabilidad anónima (RF08).
"""

import os
import pytest
from app import app
from backend.models import db, ConversacionLog


def _get_admin_password():
    pwd = os.environ.get("ADMIN_PASSWORD") or os.environ.get("TEST_ADMIN_PASSWORD")
    assert pwd, "La variable de entorno ADMIN_PASSWORD debe estar configurada."
    return pwd


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture
def auth_client():
    app.config["TESTING"] = True
    pwd = _get_admin_password()
    with app.test_client() as c:
        c.post("/api/admin/login", json={"usuario": "admin", "password": pwd})
        yield c


def test_log_creado_tras_consulta(client, registrar):
    """LOG_01: Verifica que se cree un registro en conversaciones_log tras una consulta al chatbot."""
    registro_id = None
    try:
        res = client.post("/api/chat", json={"mensaje": "requisitos para certificado de numeracion"})
        data = res.get_json() or {}
        assert res.status_code == 200

        ultimo = ConversacionLog.query.order_by(ConversacionLog.id.desc()).first()
        assert ultimo is not None
        registro_id = ultimo.id

        estado = "PASO" if ultimo.intencion_predicha == "T_015" and ultimo.tipo_respuesta == "success" else "FALLO"
        registrar(
            "LOG_01", "registro_conversaciones", "requisitos para certificado de numeracion",
            "ConversacionLog creado (T_015, success)", f"id={ultimo.id}, intent={ultimo.intencion_predicha}, tipo={ultimo.tipo_respuesta}",
            1.0, estado
        )

        assert ultimo.intencion_predicha == "T_015"
        assert ultimo.tipo_respuesta == "success"
        assert ultimo.id_tramite == "T_015"

    finally:
        if registro_id:
            ConversacionLog.query.filter_by(id=registro_id).delete()
            db.session.commit()


def test_log_campos_correctos_y_anonimizacion(client, registrar):
    """LOG_02: Verifica formato y anonimización de sesion_id, latencia_ms y longitud máxima del mensaje."""
    registro_id = None
    try:
        texto_largo = "requisitos para certificado de numeracion " + ("x" * 600)
        res = client.post("/api/chat", json={"mensaje": texto_largo})
        assert res.status_code == 200

        ultimo = ConversacionLog.query.order_by(ConversacionLog.id.desc()).first()
        assert ultimo is not None
        registro_id = ultimo.id

        # Comprobar propiedades de seguridad y formato
        sesion_valida = len(ultimo.sesion_id) == 64 and all(c in "0123456789abcdef" for c in ultimo.sesion_id)
        mensaje_truncado = len(ultimo.mensaje_usuario) <= 500
        latencia_valida = isinstance(ultimo.latencia_ms, int) and ultimo.latencia_ms >= 0

        estado = "PASO" if (sesion_valida and mensaje_truncado and latencia_valida) else "FALLO"
        registrar(
            "LOG_02", "registro_conversaciones", "mensaje_largo_600_caracteres",
            "sesion_id sha256 64 chars, len<=500, latencia>=0",
            f"len(sesion)={len(ultimo.sesion_id)}, len(msg)={len(ultimo.mensaje_usuario)}, latencia={ultimo.latencia_ms}ms",
            1.0, estado
        )

        assert sesion_valida
        assert mensaje_truncado
        assert latencia_valida

    finally:
        if registro_id:
            ConversacionLog.query.filter_by(id=registro_id).delete()
            db.session.commit()


def test_log_falla_no_interrumpe_respuesta_ciudadano(client, registrar, monkeypatch):
    """LOG_03: Verifica que si la BD de logs falla, la respuesta al ciudadano no se interrumpa (alta disponibilidad)."""
    def _mock_commit_error():
        raise RuntimeError("Falla simulada en la base de datos de auditoría")

    monkeypatch.setattr(db.session, "commit", _mock_commit_error)

    res = client.post("/api/chat", json={"mensaje": "hola buenos dias"})
    data = res.get_json() or {}

    # Debe seguir respondiendo HTTP 200 y status 'saludo'
    estado = "PASO" if res.status_code == 200 and data.get("status") == "saludo" else "FALLO"
    registrar(
        "LOG_03", "tolerancia_fallos", "falla en commit de ConversacionLog",
        "HTTP 200 status=saludo sin interrupción", f"HTTP {res.status_code} status={data.get('status')}",
        1.0, estado
    )

    assert res.status_code == 200
    assert data.get("status") == "saludo"
    assert "mensaje" in data


def test_admin_conversaciones_requiere_autenticacion(client, registrar):
    """LOG_04: Verifica que GET /api/admin/conversaciones sin sesión responda 401 No autorizado."""
    res = client.get("/api/admin/conversaciones")
    data = res.get_json() or {}

    estado = "PASO" if res.status_code == 401 and data.get("status") == "error" else "FALLO"
    registrar(
        "LOG_04", "proteccion_rutas", "GET /api/admin/conversaciones sin sesion",
        "HTTP 401 No autorizado", f"HTTP {res.status_code} status={data.get('status')}",
        1.0, estado
    )

    assert res.status_code == 401
    assert data.get("status") == "error"


def test_admin_conversaciones_con_sesion_paginado(auth_client, registrar):
    """LOG_05: Verifica consulta paginada de conversaciones con sesión administrativa activa."""
    # Insertar un registro temporal
    registro_temp = ConversacionLog(
        sesion_id="a" * 64,
        mensaje_usuario="prueba de auditoria temporal",
        intencion_predicha="T_015",
        confianza=0.95,
        tipo_respuesta="success",
        id_tramite="T_015",
        latencia_ms=45,
    )
    db.session.add(registro_temp)
    db.session.commit()
    registro_id = registro_temp.id

    try:
        res = auth_client.get("/api/admin/conversaciones?page=1&limit=10")
        data = res.get_json() or {}

        estado = "PASO" if res.status_code == 200 and data.get("status") == "success" and "conversaciones" in data else "FALLO"
        registrar(
            "LOG_05", "admin_conversaciones", "GET /api/admin/conversaciones?page=1&limit=10",
            "HTTP 200 status=success con lista y metadatos", f"HTTP {res.status_code} status={data.get('status')}, total={data.get('total')}",
            1.0, estado
        )

        assert res.status_code == 200
        assert data.get("status") == "success"
        assert "total" in data
        assert "conversaciones" in data
        assert isinstance(data["conversaciones"], list)

    finally:
        ConversacionLog.query.filter_by(id=registro_id).delete()
        db.session.commit()
