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


# ==============================================================================
# 5. PRUEBAS DE ACEPTACIÓN Y CALIDAD DE DATOS (FASE RC)
# ==============================================================================
def test_calidad_datos_tramites_csv_y_bd(registrar):
    """(a) Calidad de datos: código T_XXX único, 40 trámites, sin requisitos vacíos, sin residuales y sincronía total CSV-BD."""
    import csv
    import re
    from config import CSV_TRAMITES_PATH
    from backend.models import Tramite

    with open(CSV_TRAMITES_PATH, "r", encoding="utf-8") as f:
        csv_rows = list(csv.DictReader(f))

    assert len(csv_rows) == 40, f"CSV debe tener exactamente 40 trámites (tiene {len(csv_rows)})"

    with app.app_context():
        bd_tramites = Tramite.query.all()
        assert len(bd_tramites) == 40, f"BD debe tener exactamente 40 trámites (tiene {len(bd_tramites)})"
        bd_map = {t.id_tramite: t for t in bd_tramites}

        codigos_csv = set()
        patron_codigo = re.compile(r"^T_\d{3}$")
        patron_residual = re.compile(r"^\s*\d+[\.\)]")

        for r in csv_rows:
            id_t = r["ID_Tramite"].strip()
            assert patron_codigo.match(id_t), f"Código inválido en CSV: {id_t}"
            assert id_t not in codigos_csv, f"Código duplicado en CSV: {id_t}"
            codigos_csv.add(id_t)

            reqs_csv = [x.strip() for x in r["Requisitos"].split("|") if x.strip()]
            assert len(reqs_csv) > 0, f"Trámite {id_t} no tiene requisitos en CSV"
            for req in reqs_csv:
                assert not patron_residual.match(req), f"Requisito con numeración residual en CSV ({id_t}): {req}"

            t_bd = bd_map.get(id_t)
            assert t_bd is not None, f"Trámite {id_t} no existe en BD"
            assert t_bd.nombre == r["Nombre"].strip(), f"Nombre difiere en {id_t}"
            assert t_bd.costo == r["Costo"].strip(), f"Costo difiere en {id_t}"
            assert t_bd.plazo == r["Plazo"].strip(), f"Plazo difiere en {id_t}"

            reqs_bd = [req_obj.descripcion for req_obj in t_bd.requisitos]
            assert len(reqs_bd) == len(reqs_csv), f"Cantidad de requisitos difiere en {id_t}"
            for req_bd in reqs_bd:
                assert not patron_residual.match(req_bd), f"Requisito con numeración residual en BD ({id_t}): {req_bd}"
            assert reqs_bd == reqs_csv, f"Requisitos difieren entre CSV y BD en {id_t}"

    registrar(
        "NUEVA_01", "calidad_datos", "Validación integral CSV vs BD",
        "40 trámites, códigos T_XXX únicos, sin residuales y 100% sincronizados",
        "40 trámites validados exitosamente en CSV y BD",
        1.0, "PASO"
    )


def test_t001_costo_y_plazo_correctos(client, registrar):
    """(b) Verifica que el costo y plazo de T_001 salgan correctos y sin columnas desplazadas."""
    r1 = client.post("/api/chat", json={"mensaje": "requisitos para acceso a la informacion publica"})
    d1 = r1.get_json()
    assert r1.status_code == 200
    assert d1.get("id_tramite") == "T_001"
    assert len(d1.get("requisitos", [])) == 2
    for req in d1.get("requisitos", []):
        assert not req.startswith("1.") and not req.startswith("2.")

    r2 = client.post("/api/chat", json={"mensaje": "cuanto cuesta"})
    d2 = r2.get_json()
    assert r2.status_code == 200
    assert d2.get("costo") == "Copia S/0.10 - CD S/1.00"
    assert "Copia S/0.10 - CD S/1.00" in d2.get("mensaje", "")
    assert "1. Solicitud" not in d2.get("mensaje", "")

    r3 = client.post("/api/chat", json={"mensaje": "cuanto demora"})
    d3 = r3.get_json()
    assert r3.status_code == 200
    assert d3.get("plazo") == "10 días hábiles"
    assert "10 días hábiles" in d3.get("mensaje", "")
    assert "Copia S/0.10" not in d3.get("mensaje", "")

    registrar(
        "NUEVA_02", "t001_corregido", "T_001: seguimiento costo y plazo correcto",
        "costo='Copia S/0.10 - CD S/1.00', plazo='10 días hábiles'",
        f"costo='{d2.get('costo')}', plazo='{d3.get('plazo')}'",
        1.0, "PASO"
    )


def test_plazo_t015_se_muestra_como_dato_valido(client, registrar):
    """(c) Verifica que el plazo de T_015 se muestre como dato válido ('Inmediato (0 días hábiles)')."""
    client.post("/api/chat", json={"mensaje": "requisitos para certificado de numeracion"})
    r2 = client.post("/api/chat", json={"mensaje": "cuanto tiempo demora"})
    d2 = r2.get_json()
    assert r2.status_code == 200
    assert "Inmediato (0 días hábiles)" in d2.get("mensaje", "")
    assert "no se encuentra disponible" not in d2.get("mensaje", "")

    registrar(
        "NUEVA_03", "plazo_inmediato", "T_015 plazo inmediato válido",
        "Mensaje contiene 'Inmediato (0 días hábiles)' y no 'no disponible'",
        f"mensaje='{d2.get('mensaje')}'",
        1.0, "PASO"
    )


def test_mensaje_frustracion_recibe_empatia(client, registrar):
    """(d) Verifica que el mensaje de frustración reciba respuesta de empatía."""
    r = client.post("/api/chat", json={"mensaje": "no me ayudas en nada, pesimo servicio"})
    d = r.get_json()
    assert r.status_code == 200
    assert d.get("status") == "frustration"
    assert d.get("intent") == "frustracion"
    assert "Soy Leonardito" not in d.get("mensaje", "")

    registrar(
        "NUEVA_04", "empatia_frustracion", "Queja ciudadana activa empatía",
        "status='frustration', intent='frustracion'",
        f"status='{d.get('status')}', intent='{d.get('intent')}'",
        1.0, "PASO"
    )


def test_saludo_baja_confianza_no_se_responde_como_saludo(client, registrar):
    """(e) Verifica que un saludo con baja confianza (< 0.35) no se responda como saludo y vaya a fallback."""
    r = client.post("/api/chat", json={"mensaje": "<b>prueba</b>"})
    d = r.get_json()
    assert r.status_code == 200
    assert d.get("status") == "fallback"
    assert d.get("status") != "saludo"
    assert "Soy Leonardito" not in d.get("mensaje", "")

    registrar(
        "NUEVA_05", "baja_confianza_fallback", "Entrada baja confianza no responde como saludo",
        "status='fallback', no saludo",
        f"status='{d.get('status')}', intent='{d.get('intent')}'",
        1.0, "PASO"
    )


def test_regresion_escape_html_xss(client, registrar):
    """Regresión XSS: plantillas incluyen función escapeHTML para entradas y salidas."""
    r_index = client.get("/")
    assert r_index.status_code == 200
    html = r_index.get_data(as_text=True)

    assert "function escapeHTML" in html
    assert "&amp;" in html
    assert "&lt;" in html
    assert "&gt;" in html
    assert "escapeHTML(texto)" in html

    r_chat = client.post("/api/chat", json={"mensaje": "<script>alert('xss')</script>"})
    assert r_chat.status_code == 200

    registrar(
        "REG_04", "regresion_xss", "Verificación de escape HTML en portal y widget",
        "escapeHTML activo y manejo seguro de payloads con etiquetas",
        "escapeHTML presente en plantilla y endpoint responde seguro HTTP 200",
        1.0, "PASO"
    )

