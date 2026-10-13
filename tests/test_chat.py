import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ==============================================================================
# GRUPO D: MANEJO DE CONTEXTO Y DIÁLOGO GUIADO (6 CASOS)
# ==============================================================================
def test_contexto_confirmacion_si(client, registrar):
    # Activar zona de duda primero
    r1 = client.post("/api/chat", json={"mensaje": "ola qiero un permiso para mi bodega q hago"})
    d1 = r1.get_json()
    assert d1.get("status") == "clarification"

    # Responder "si"
    r2 = client.post("/api/chat", json={"mensaje": "si"})
    d2 = r2.get_json()
    obtenido = d2.get("status")
    confianza = d2.get("confianza", 1.0)
    estado = "PASO" if obtenido == "success" and d2.get("id_tramite") == "T_003" else "FALLO"
    registrar("CHAT_D01", "contexto_dialogo", "confirmacion_si", "status=success", f"status={obtenido}", confianza, estado)
    assert obtenido == "success"
    assert d2.get("id_tramite") == "T_003"


def test_contexto_confirmacion_no(client, registrar):
    # Activar zona de duda primero
    r1 = client.post("/api/chat", json={"mensaje": "ola qiero un permiso para mi bodega q hago"})
    d1 = r1.get_json()
    assert d1.get("status") == "clarification"

    # Responder "no"
    r2 = client.post("/api/chat", json={"mensaje": "no"})
    d2 = r2.get_json()
    obtenido = d2.get("status")
    confianza = d2.get("confianza", 1.0)
    estado = "PASO" if obtenido == "clarification_rejected" else "FALLO"
    registrar("CHAT_D02", "contexto_dialogo", "confirmacion_no", "status=clarification_rejected", f"status={obtenido}", confianza, estado)
    assert obtenido == "clarification_rejected"


def test_contexto_correccion_no_ese_no(client, registrar):
    # Establecer trámite en sesión
    client.post("/api/chat", json={"mensaje": "requisitos para certificado de numeracion"})
    
    # Responder corrección
    r = client.post("/api/chat", json={"mensaje": "no, ese no"})
    d = r.get_json()
    obtenido = d.get("status")
    confianza = d.get("confianza", 0.0)
    estado = "PASO" if obtenido == "correction" else "FALLO"
    registrar("CHAT_D03", "contexto_dialogo", "no, ese no (con tramite activo)", "status=correction", f"status={obtenido}", confianza, estado)
    assert obtenido == "correction"


def test_contexto_despedida_real(client, registrar):
    # Establecer trámite en sesión
    client.post("/api/chat", json={"mensaje": "requisitos para certificado de numeracion"})

    # Responder despedida real
    r = client.post("/api/chat", json={"mensaje": "no gracias, adios"})
    d = r.get_json()
    obtenido = d.get("status")
    confianza = d.get("confianza", 0.0)
    estado = "PASO" if obtenido == "despedida" else "FALLO"
    registrar("CHAT_D04", "contexto_dialogo", "no gracias, adios (con tramite activo)", "status=despedida", f"status={obtenido}", confianza, estado)
    assert obtenido == "despedida"


def test_contexto_macrointencion_opcion_a(client, registrar):
    # Activar macrointención de divorcio
    r1 = client.post("/api/chat", json={"mensaje": "iniciar tramite de separacion mutua y divorcio rapido"})
    d1 = r1.get_json()
    # Si entra a macrointención o trámite directo
    with client.session_transaction() as sess:
        sess["macro_pendiente"] = "consultar_divorcio"

    # Responder opción 'a'
    r2 = client.post("/api/chat", json={"mensaje": "a"})
    d2 = r2.get_json()
    obtenido = d2.get("status")
    confianza = d2.get("confianza", 1.0)
    estado = "PASO" if obtenido == "success" and d2.get("id_tramite") == "T_009" else "FALLO"
    registrar("CHAT_D05", "contexto_dialogo", "opcion 'a' en macrointencion", "status=success, id=T_009", f"status={obtenido}, id={d2.get('id_tramite')}", confianza, estado)
    assert obtenido == "success"
    assert d2.get("id_tramite") == "T_009"


def test_contexto_macrointencion_no_se(client, registrar):
    with client.session_transaction() as sess:
        sess["macro_pendiente"] = "consultar_divorcio"

    r = client.post("/api/chat", json={"mensaje": "no se"})
    d = r.get_json()
    obtenido = d.get("status")
    confianza = d.get("confianza", 1.0)
    estado = "PASO" if obtenido == "derivacion" else "FALLO"
    registrar("CHAT_D06", "contexto_dialogo", "no se en macrointencion", "status=derivacion", f"status={obtenido}", confianza, estado)
    assert obtenido == "derivacion"


# ==============================================================================
# GRUPO E: /api/chat EXTREMO A EXTREMO Y VALORES DE STATUS (10 CASOS)
# ==============================================================================
def test_api_chat_saludo(client, registrar):
    r = client.post("/api/chat", json={"mensaje": "hola buenos dias"})
    d = r.get_json()
    obtenido = d.get("status")
    confianza = d.get("confianza", 0.0)
    estado = "PASO" if obtenido == "saludo" and r.status_code == 200 else "FALLO"
    registrar("CHAT_E01", "endpoint_chat", "hola buenos dias", "status=saludo", f"status={obtenido}", confianza, estado)
    assert r.status_code == 200
    assert obtenido == "saludo"


def test_api_chat_requisitos_tramite(client, registrar):
    r = client.post("/api/chat", json={"mensaje": "requisitos para certificado de numeracion municipal"})
    d = r.get_json()
    obtenido = d.get("status")
    confianza = d.get("confianza", 0.0)
    estado = "PASO" if obtenido == "success" and d.get("id_tramite") == "T_015" else "FALLO"
    registrar("CHAT_E02", "endpoint_chat", "requisitos para certificado de numeracion", "status=success", f"status={obtenido}", confianza, estado)
    assert r.status_code == 200
    assert obtenido == "success"
    assert d.get("id_tramite") == "T_015"


def test_api_chat_seguimiento_costo(client, registrar):
    client.post("/api/chat", json={"mensaje": "requisitos para certificado de numeracion"})
    r = client.post("/api/chat", json={"mensaje": "cuanto cuesta"})
    d = r.get_json()
    obtenido = d.get("status")
    confianza = d.get("confianza", 0.0)
    costo = d.get("costo")
    estado = "PASO" if obtenido == "success" and costo is not None else "FALLO"
    registrar("CHAT_E03", "endpoint_chat", "cuanto cuesta (seguimiento)", "status=success con costo", f"status={obtenido}, costo={costo}", confianza, estado)
    assert r.status_code == 200
    assert obtenido == "success"
    assert costo is not None


def test_api_chat_seguimiento_plazo(client, registrar):
    client.post("/api/chat", json={"mensaje": "requisitos para certificado de numeracion"})
    r = client.post("/api/chat", json={"mensaje": "cuanto tiempo demora"})
    d = r.get_json()
    obtenido = d.get("status")
    confianza = d.get("confianza", 0.0)
    plazo = d.get("plazo")
    estado = "PASO" if obtenido == "success" and plazo is not None else "FALLO"
    registrar("CHAT_E04", "endpoint_chat", "cuanto tiempo demora (seguimiento)", "status=success con plazo", f"status={obtenido}, plazo={plazo}", confianza, estado)
    assert r.status_code == 200
    assert obtenido == "success"
    assert plazo is not None


def test_api_chat_fuera_de_dominio(client, registrar):
    r = client.post("/api/chat", json={"mensaje": "cual es el sueldo del alcalde"})
    d = r.get_json()
    obtenido = d.get("status")
    confianza = d.get("confianza", 0.0)
    estado = "PASO" if obtenido == "fallback" and r.status_code == 200 else "FALLO"
    registrar("CHAT_E05", "endpoint_chat", "cual es el sueldo del alcalde", "status=fallback", f"status={obtenido}", confianza, estado)
    assert r.status_code == 200
    assert obtenido == "fallback"


def test_api_chat_mensaje_vacio(client, registrar):
    r = client.post("/api/chat", json={"mensaje": ""})
    d = r.get_json()
    obtenido = d.get("status")
    estado = "PASO" if obtenido == "fallback" and r.status_code == 400 else "FALLO"
    registrar("CHAT_E06", "endpoint_chat", "mensaje vacio", "status=fallback (400)", f"status={obtenido} ({r.status_code})", 0.0, estado)
    assert r.status_code == 400
    assert obtenido == "fallback"


def test_api_chat_payload_invalido(client, registrar):
    r = client.post("/api/chat", json={})
    d = r.get_json()
    obtenido = d.get("status")
    estado = "PASO" if obtenido == "error" and r.status_code == 400 else "FALLO"
    registrar("CHAT_E07", "endpoint_chat", "payload sin 'mensaje'", "status=error (400)", f"status={obtenido} ({r.status_code})", 0.0, estado)
    assert r.status_code == 400
    assert obtenido == "error"


def test_api_chat_charla_casual(client, registrar):
    r = client.post("/api/chat", json={"mensaje": "como te llamas"})
    d = r.get_json()
    obtenido = d.get("status")
    confianza = d.get("confianza", 0.0)
    estado = "PASO" if obtenido == "charla_casual" and r.status_code == 200 else "FALLO"
    registrar("CHAT_E08", "endpoint_chat", "como te llamas", "status=charla_casual", f"status={obtenido}", confianza, estado)
    assert r.status_code == 200
    assert obtenido == "charla_casual"


def test_api_chat_zona_duda_clarification(client, registrar):
    r = client.post("/api/chat", json={"mensaje": "ola qiero un permiso para mi bodega q hago"})
    d = r.get_json()
    obtenido = d.get("status")
    confianza = d.get("confianza", 0.0)
    estado = "PASO" if obtenido == "clarification" and r.status_code == 200 else "FALLO"
    registrar("CHAT_E09", "endpoint_chat", "ola qiero un permiso para mi bodega q hago", "status=clarification", f"status={obtenido}", confianza, estado)
    assert r.status_code == 200
    assert obtenido == "clarification"


def test_api_chat_macrointencion_clarification(client, registrar):
    r = client.post("/api/chat", json={"mensaje": "licencia"})
    d = r.get_json()
    obtenido = d.get("status")
    confianza = d.get("confianza", 0.0)
    estado = "PASO" if obtenido == "clarification" and r.status_code == 200 else "FALLO"
    registrar("CHAT_E10", "endpoint_chat", "licencia", "status=clarification", f"status={obtenido}", confianza, estado)
    assert r.status_code == 200
    assert obtenido == "clarification"
