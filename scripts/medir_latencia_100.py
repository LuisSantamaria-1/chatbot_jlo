"""
scripts/medir_latencia_100.py
-----------------------------
Mide la latencia de /api/chat ejecutando exactamente 100 peticiones reales
sobre un servidor Flask con debug=False y threaded=True.
Limpia cualquier fila creada en conversaciones_log al finalizar.
"""

import sys
import os
import time
import subprocess
import requests
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

PORT = 5062
BASE_URL = f"http://127.0.0.1:{PORT}"
CHAT_URL = f"{BASE_URL}/api/chat"

CONSULTAS_100 = [
    # 25 Saludos y consultas generales
    "hola buenos dias", "buenas tardes", "hola que tal", "buen dia", "hola como estas",
    "hola deseo informacion", "buenos dias señorita", "hola chatbot", "buenas noches", "saludos cordiales",
    "hola", "buen dia asistente", "que tal", "buenas tardes necesito ayuda", "hola buenas tardes",
    "hola tengo una consulta", "buenos dias", "hola como te va", "hola amigo", "saludos",
    "buenas tardes muni", "buen dia munijlo", "hola asistente", "hola buenas", "buen dia a todos",
    
    # 35 Consultas de requisitos (requieren inferencia NLP y consulta a BD MySQL)
    "cuales son los requisitos para licencia de funcionamiento de riesgo bajo",
    "requisitos para matrimonio civil",
    "que necesito para duplicado de licencia de conducir",
    "requisitos para cambio de giro en licencia",
    "cuales son los requisitos para autorizacion de anuncio publicitario",
    "requisitos para constancia de posesion",
    "que documentos necesito para visacion de planos",
    "como solicito la prescripcion de deudas tributarias",
    "requisitos para separacion convencional y divorcio",
    "como empadrono mi mototaxi",
    "requisitos para certificado de numeracion",
    "que papeles piden para habilitacion urbana",
    "requisitos para subdivision de lote",
    "como pido autorizacion de eventos publicos",
    "requisitos para inspeccion tecnica de seguridad itse",
    "como saco carnet de sanidad",
    "requisitos para certificado domiciliario",
    "como solicito constancia de no adeudo",
    "requisitos para permiso de demolicion",
    "que piden para certificado de parametros urbanisticos",
    "requisitos para licencia de funcionamiento de riesgo medio",
    "como solicito copia certificada de resolucion de alcaldia",
    "requisitos para permiso de transporte escolar",
    "documentos para rectificacion de partida de nacimiento",
    "que piden para permiso de rotura de pavimento",
    "requisitos para licencia de edificacion modalidad A",
    "como registro mi marca comercial",
    "requisitos para renovar tarjeta de circulacion vehicular",
    "tramite para exoneracion de arbitrios para jubilados",
    "como reclamo por un cobro indebido de serenazgo",
    "requisitos para autorizacion de toldos y publicidad exterior",
    "que documentos piden para inscribir un recien nacido",
    "requisitos para certificado de defensa civil",
    "como solicito apertura de zanja para agua y desague",
    "requisitos para licencia temporal para ferias o eventos",

    # 20 Consultas de seguimiento (costo y plazo)
    "cuanto cuesta este tramite", "cual es el costo oficial", "dime la tasa a pagar",
    "cual es el precio de este tramite", "cuanto es el derecho de tramite",
    "en cuantos dias me responden", "cual es el plazo de entrega", "cuanto demora en salir",
    "cuantos dias habiles tarda", "cuando me entregan el documento",
    "cuanto cuesta", "cual es la tasa municipal", "es gratuito o tiene costo",
    "cuanto tiempo se demora", "plazo maximo de atencion", "cuanto hay que abonar",
    "en cuanto tiempo lo entregan", "cuanto se paga en caja", "cuanto tarda la aprobacion",
    "cuanto vale el tramite",

    # 20 Consultas fuera de dominio o combinadas
    "a que hora abre el cine en chiclayo", "cual es el numero del hospital las mercedes",
    "donde queda la clinica metropolitana", "quien es el presidente del peru",
    "venden comida dentro de la municipalidad", "a cuanto esta el dolar hoy",
    "cuando juega el juan aurich", "donde comprar pasajes para lima",
    "cual es el horario de misa en la iglesia", "que farmacias de turno hay en jlo",
    "como llego al aeropuerto desde moshoqueque", "clima en chiclayo manana",
    "receta para ceviche de pescado", "que canales transmiten el partido",
    "donde queda la comisarÃ­a de jlo", "cuanto cuesta un taxi al centro",
    "que empresas de luz atienden hoy", "a que hora pasa la basura por mi casa",
    "donde puedo pagar el telefono", "gracias por la ayuda hasta luego"
]

def iniciar_servidor():
    runner_script = os.path.join(os.path.dirname(__file__), "server_runner.py")
    cmd = [sys.executable, runner_script, str(PORT)]
    env = os.environ.copy()
    if not env.get("SECRET_KEY"):
        import secrets
        env["SECRET_KEY"] = secrets.token_hex(32)
    proc = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for _ in range(40):
        time.sleep(0.2)
        try:
            r = requests.get(f"{BASE_URL}/", timeout=1)
            if r.status_code == 200:
                return proc
        except Exception:
            pass

    proc.terminate()
    raise RuntimeError(f"No se pudo iniciar el servidor en el puerto {PORT}")


def main():
    print(f"Levantando servidor de prueba en puerto {PORT} (debug=False, threaded=True)...")
    server_proc = iniciar_servidor()

    try:
        session = requests.Session()

        # Warm-up (3 peticiones para inicializar caches y modelos)
        for _ in range(3):
            session.post(CHAT_URL, json={"mensaje": "hola"}, timeout=5)

        print(f"Ejecutando 100 consultas reales contra /api/chat...")
        latencias = []
        errores = 0

        for i, msg in enumerate(CONSULTAS_100, 1):
            t0 = time.perf_counter()
            try:
                resp = session.post(CHAT_URL, json={"mensaje": msg}, timeout=10)
                lat_ms = (time.perf_counter() - t0) * 1000
                if resp.status_code != 200:
                    errores += 1
            except Exception as e:
                lat_ms = (time.perf_counter() - t0) * 1000
                errores += 1

            latencias.append(lat_ms)

        arr = np.array(latencias)
        cumple_5s = np.all(arr < 5000)

        print("\n" + "=" * 60)
        print("     MEDICIÓN DE LATENCIA DE /api/chat (100 CONSULTAS REALES)")
        print("=" * 60)
        print(f"Total consultas ejecutadas: {len(arr)}")
        print(f"Total errores HTTP (!= 200): {errores}")
        print(f"Latencia Mínima:             {np.min(arr):.2f} ms ({np.min(arr)/1000:.4f} s)")
        print(f"Latencia Promedio:           {np.mean(arr):.2f} ms ({np.mean(arr)/1000:.4f} s)")
        print(f"Latencia Mediana (P50):      {np.median(arr):.2f} ms ({np.median(arr)/1000:.4f} s)")
        print(f"Percentil 90 (P90):          {np.percentile(arr, 90):.2f} ms ({np.percentile(arr, 90)/1000:.4f} s)")
        print(f"Percentil 95 (P95):          {np.percentile(arr, 95):.2f} ms ({np.percentile(arr, 95)/1000:.4f} s)")
        print(f"Percentil 99 (P99):          {np.percentile(arr, 99):.2f} ms ({np.percentile(arr, 99)/1000:.4f} s)")
        print(f"Latencia Máxima:             {np.max(arr):.2f} ms ({np.max(arr)/1000:.4f} s)")
        print(f"Cumple SLA (< 5.0 s):        {'SÍ (< 5s)' if cumple_5s else 'NO'}")
        print("=" * 60)

    finally:
        server_proc.terminate()
        server_proc.wait(timeout=3)
        print("Servidor de pruebas detenido.")

        # Limpiar filas creadas en conversaciones_log para mantener conteo en 0
        from backend.models import db, ConversacionLog
        from app import app
        with app.app_context():
            borradas = ConversacionLog.query.delete()
            db.session.commit()
            total_post = ConversacionLog.query.count()
            print(f"Limpieza post-prueba: {borradas} filas eliminadas de conversaciones_log. Conteo actual: {total_post}")


if __name__ == "__main__":
    main()
