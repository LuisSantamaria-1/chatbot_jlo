"""
scripts/ejecutar_aceptacion.py
------------------------------
Ejecuta las pruebas de aceptación del Chatbot Ciudadano (AC-01 a AC-18)
usando Flask test_client() con sesiones aisladas por escenario.
Genera 'aceptacion_api_resultados.csv' y limpia la base de datos al finalizar.
"""

import os
import sys
import csv
import json

# Asegurar path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configurar clave temporal si no está en entorno
if not os.environ.get("SECRET_KEY"):
    import secrets
    os.environ["SECRET_KEY"] = secrets.token_hex(32)

from app import app
from backend.models import db, Tramite, ConversacionLog

app.config["TESTING"] = True

casos_resultados = []

def registrar(caso_id, mensaje, res):
    data = res.get_json(silent=True) or {}
    status = data.get("status", f"HTTP_{res.status_code}")
    intencion = data.get("intent", "N/A")
    confianza = data.get("confianza", "N/A")
    if isinstance(confianza, (int, float)):
        confianza_str = f"{confianza:.4f}"
    else:
        confianza_str = str(confianza)
    msg_devuelto = data.get("mensaje", "")
    msg_resumido = (msg_devuelto[:117] + "...") if len(msg_devuelto) > 120 else msg_devuelto

    casos_resultados.append({
        "id": caso_id,
        "mensaje": mensaje,
        "status": status,
        "intencion": intencion,
        "confianza": confianza_str,
        "mensaje_devuelto": msg_devuelto,
        "mensaje_resumido": msg_resumido
    })
    print(f"[{caso_id}] {mensaje} -> status={status}, intent={intencion}, conf={confianza_str}")

def main():
    print("Iniciando pruebas de aceptación...")

    # AC-01: "hola buenos dias" (sesión nueva)
    with app.test_client() as c:
        r = c.post("/api/chat", json={"mensaje": "hola buenos dias"})
        registrar("AC-01", "hola buenos dias", r)

    # AC-02, AC-03, AC-04: Cadena de requisitos y seguimiento de costo y plazo
    with app.test_client() as c:
        r2 = c.post("/api/chat", json={"mensaje": "requisitos para certificado de numeracion"})
        registrar("AC-02", "requisitos para certificado de numeracion", r2)

        r3 = c.post("/api/chat", json={"mensaje": "cuanto cuesta"})
        registrar("AC-03", "cuanto cuesta", r3)

        r4 = c.post("/api/chat", json={"mensaje": "cuanto tiempo demora"})
        registrar("AC-04", "cuanto tiempo demora", r4)

    # AC-05 y AC-06: Zona de duda y confirmación positiva "si"
    with app.test_client() as c:
        r5 = c.post("/api/chat", json={"mensaje": "ola qiero un permiso para mi bodega q hago"})
        registrar("AC-05", "ola qiero un permiso para mi bodega q hago", r5)

        r6 = c.post("/api/chat", json={"mensaje": "si"})
        registrar("AC-06", "si", r6)

    # AC-07: Zona de duda y confirmación negativa "no"
    with app.test_client() as c:
        c.post("/api/chat", json={"mensaje": "ola qiero un permiso para mi bodega q hago"})
        r7 = c.post("/api/chat", json={"mensaje": "no"})
        registrar("AC-07", "no", r7)

    # AC-08 y AC-09: Macrointención "licencia" y opción "a"
    with app.test_client() as c:
        r8 = c.post("/api/chat", json={"mensaje": "licencia"})
        registrar("AC-08", "licencia", r8)

        r9 = c.post("/api/chat", json={"mensaje": "a"})
        registrar("AC-09", "a", r9)

    # AC-10: Macrointención "licencia" y opción "no se"
    with app.test_client() as c:
        c.post("/api/chat", json={"mensaje": "licencia"})
        r10 = c.post("/api/chat", json={"mensaje": "no se"})
        registrar("AC-10", "no se", r10)

    # AC-11: "no, ese no" tras consultar un trámite
    with app.test_client() as c:
        c.post("/api/chat", json={"mensaje": "requisitos para certificado de numeracion"})
        r11 = c.post("/api/chat", json={"mensaje": "no, ese no"})
        registrar("AC-11", "no, ese no", r11)

    # AC-12: "no gracias, adios" tras consultar un trámite
    with app.test_client() as c:
        c.post("/api/chat", json={"mensaje": "requisitos para certificado de numeracion"})
        r12 = c.post("/api/chat", json={"mensaje": "no gracias, adios"})
        registrar("AC-12", "no gracias, adios", r12)

    # AC-13: "cual es el sueldo del alcalde"
    with app.test_client() as c:
        r13 = c.post("/api/chat", json={"mensaje": "cual es el sueldo del alcalde"})
        registrar("AC-13", "cual es el sueldo del alcalde", r13)

    # AC-14: "quiero saber el estado de mi expediente"
    with app.test_client() as c:
        r14 = c.post("/api/chat", json={"mensaje": "quiero saber el estado de mi expediente"})
        registrar("AC-14", "quiero saber el estado de mi expediente", r14)

    # AC-15: "cuanto cuesta" en sesión nueva
    with app.test_client() as c:
        r15 = c.post("/api/chat", json={"mensaje": "cuanto cuesta"})
        registrar("AC-15", "cuanto cuesta", r15)

    # AC-16: "no me ayudas en nada, pesimo servicio"
    with app.test_client() as c:
        r16 = c.post("/api/chat", json={"mensaje": "no me ayudas en nada, pesimo servicio"})
        registrar("AC-16", "no me ayudas en nada, pesimo servicio", r16)

    # AC-17: Cadena de acceso a la información pública
    with app.test_client() as c:
        r17a = c.post("/api/chat", json={"mensaje": "requisitos para acceso a la informacion publica"})
        registrar("AC-17a", "requisitos para acceso a la informacion publica", r17a)

        r17b = c.post("/api/chat", json={"mensaje": "cuanto cuesta"})
        registrar("AC-17b", "cuanto cuesta", r17b)

        r17c = c.post("/api/chat", json={"mensaje": "cuanto demora"})
        registrar("AC-17c", "cuanto demora", r17c)

    # AC-18: Mensaje con inyección HTML "<b>prueba</b>"
    with app.test_client() as c:
        r18 = c.post("/api/chat", json={"mensaje": "<b>prueba</b>"})
        registrar("AC-18", "<b>prueba</b>", r18)

    # Guardar CSV
    csv_file = "aceptacion_api_resultados.csv"
    with open(csv_file, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "mensaje", "status", "intencion", "confianza", "mensaje_devuelto"])
        for c in casos_resultados:
            writer.writerow([c["id"], c["mensaje"], c["status"], c["intencion"], c["confianza"], c["mensaje_devuelto"]])

    print(f"\nGuardados {len(casos_resultados)} casos en {csv_file}")

    # Limpiar conversaciones_log y verificar conteos en BD
    with app.app_context():
        filas_borradas = ConversacionLog.query.delete()
        db.session.commit()
        total_conv = ConversacionLog.query.count()
        total_tram = Tramite.query.count()
        print(f"Limpieza post-aceptación: {filas_borradas} filas eliminadas de conversaciones_log.")
        print(f"Estado BD: conversaciones_log={total_conv} filas, tramites={total_tram} filas.")

if __name__ == "__main__":
    main()
