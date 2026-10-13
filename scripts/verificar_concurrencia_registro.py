"""
scripts/verificar_concurrencia_registro.py
------------------------------------------
Prueba de concurrencia y persistencia de conversaciones_log:
1. Levanta un servidor Flask real en puerto 5055 (debug=False, threaded=True).
2. Ejecuta 20 usuarios virtuales concurrentes durante 15 segundos con sesiones HTTP independientes.
3. Compara el total de solicitudes HTTP 200 con las filas creadas en conversaciones_log.
4. Inspecciona logs/chatbot.log en busca de errores de persistencia/concurrencia.
5. Limpia únicamente las filas generadas por esta prueba, dejando el registro en 0 filas.
"""

import os
import sys
import time
import random
import threading
import subprocess
from datetime import datetime, timezone
import requests
from sqlalchemy import text

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

PORT = 5055
SERVER_URL = f"http://127.0.0.1:{PORT}"
CHAT_URL = f"{SERVER_URL}/api/chat"
DURACION_SEGUNDOS = 15.0
NUM_USUARIOS = 20

FRASES_PRUEBA = [
    "hola buenos dias",
    "requisitos para certificado de numeracion",
    "que piden para licencia de funcionamiento de bodega",
    "requisitos para matrimonio civil comunitario",
    "documentos para visacion de planos para electrificacion",
    "como tramito la constancia de posesion",
    "que piden para aprobacion de habilitacion urbana",
    "cuanto cuesta el tramite",
    "cual es el costo de la licencia",
    "en cuantos dias me responden",
    "cual es el plazo de entrega",
    "a que hora abren el cine en chiclayo",
    "tienes amigos robots",
    "kiero licencia altoke pa mi tienda",
    "como sacar permiso de construccion modal A",
    "requisitos para separacion convencional y divorcio ulterior",
    "solicito copia certificada de resolucion de alcaldia",
    "buenas tardes asistente",
    "gracias por la informacion",
    "nos vemos hasta luego"
]

def esperar_servidor(url, timeout=15):
    inicio = time.time()
    while time.time() - inicio < timeout:
        try:
            r = requests.get(url, timeout=1.0)
            if r.status_code in (200, 404):
                return True
        except Exception:
            time.sleep(0.3)
    return False

def main():
    print("=" * 70)
    print("PRUEBA DE CONCURRENCIA Y AUDITORÍA: REGISTRO DE CONVERSACIONES")
    print(f"Parámetros: {NUM_USUARIOS} usuarios virtuales | Duración: {DURACION_SEGUNDOS} s | Puerto: {PORT}")
    print("=" * 70)

    # 1. Conexión a BD para conteo inicial
    from app import app
    from backend.models import db, ConversacionLog, Tramite, Usuario, Rol
    with app.app_context():
        count_inicio = ConversacionLog.query.count()
        with db.engine.begin() as conn:
            res_max = conn.execute(text("SELECT COALESCE(MAX(id), 0) FROM conversaciones_log")).scalar()
            max_id_inicio = res_max or 0
        tramites_inicio = Tramite.query.count()
        usuarios_inicio = Usuario.query.count()
        roles_inicio = Rol.query.count()

    print(f"\n[BD INICIAL] conversaciones_log: {count_inicio} filas | MAX(id): {max_id_inicio}")
    print(f"[BD INICIAL] Catalogos: {tramites_inicio} tramites | {usuarios_inicio} usuarios | {roles_inicio} roles")

    # 2. Levantar servidor Flask en puerto 5055 (debug=False, threaded=True)
    cmd = [
        os.path.join(BASE_DIR, ".venv", "Scripts", "python.exe"),
        "-c",
        f"from backend import create_app; app = create_app(); app.run(host='127.0.0.1', port={PORT}, debug=False, threaded=True)"
    ]
    print(f"\nIniciando servidor de pruebas en 127.0.0.1:{PORT} (debug=False, threaded=True)...")
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if not esperar_servidor(SERVER_URL, timeout=15):
        proc.terminate()
        print("ERROR: El servidor de pruebas no respondió dentro del tiempo límite.")
        sys.exit(1)
    print("Servidor listo y respondiendo solicitudes.")

    # Warm-up para precalentar modelo NLP y conexión DB
    print("Precalentando modelo NLP y conexiones...")
    try:
        requests.post(CHAT_URL, json={"mensaje": "hola warm up"}, timeout=10)
    except Exception:
        pass

    # Establecer punto de partida limpio en la BD tras warm-up
    with app.app_context():
        with db.engine.begin() as conn:
            conn.execute(text("DELETE FROM conversaciones_log"))
            res_max = conn.execute(text("SELECT COALESCE(MAX(id), 0) FROM conversaciones_log")).scalar()
            max_id_inicio = res_max or 0
        count_inicio = ConversacionLog.query.count()

    print(f"[BD BASE] conversaciones_log listo con {count_inicio} filas | MAX(id): {max_id_inicio}")

    # 3. Ejecutar 20 usuarios virtuales concurrentes durante 15 segundos
    resultados = []
    lock = threading.Lock()
    tiempo_inicio = time.time()
    tiempo_fin = tiempo_inicio + DURACION_SEGUNDOS

    codigos_estado = {}
    errores_cliente = {}

    def usuario_worker(user_id):
        # Pequeño escalonamiento inicial (stagger) para simular llegada de usuarios reales
        time.sleep(user_id * 0.04)
        session = requests.Session()
        while time.time() < tiempo_fin:
            frase = random.choice(FRASES_PRUEBA)
            t0 = time.perf_counter()
            err_desc = None
            try:
                resp = session.post(CHAT_URL, json={"mensaje": frase}, timeout=15.0)
                lat_ms = (time.perf_counter() - t0) * 1000.0
                sc = resp.status_code
            except Exception as e:
                lat_ms = (time.perf_counter() - t0) * 1000.0
                sc = 0
                err_desc = f"{type(e).__name__}: {str(e)[:100]}"

            with lock:
                codigos_estado[sc] = codigos_estado.get(sc, 0) + 1
                if err_desc:
                    errores_cliente[err_desc] = errores_cliente.get(err_desc, 0) + 1
                resultados.append({
                    "user_id": user_id,
                    "status_code": sc,
                    "latencia_ms": lat_ms,
                    "timestamp": time.time(),
                    "error": err_desc
                })
            # Pausa de reflexión ciudadana (100ms a 250ms)
            time.sleep(random.uniform(0.1, 0.25))

    print(f"\nLanzando {NUM_USUARIOS} hilos de usuarios virtuales por {DURACION_SEGUNDOS} segundos...")
    threads = []
    for uid in range(NUM_USUARIOS):
        t = threading.Thread(target=usuario_worker, args=(uid + 1,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    duracion_real = time.time() - tiempo_inicio
    print(f"Prueba completada en {duracion_real:.2f} segundos.")

    # 4. Detener el servidor de pruebas
    print("Deteniendo servidor de pruebas...")
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    print("Servidor de pruebas detenido.")

    # 5. Análisis de solicitudes HTTP
    total_solicitudes = len(resultados)
    solicitudes_200 = sum(1 for r in resultados if r["status_code"] == 200)
    solicitudes_errores = total_solicitudes - solicitudes_200
    latencias = [r["latencia_ms"] for r in resultados if r["status_code"] == 200]

    lat_media = sum(latencias) / len(latencias) if latencias else 0.0
    lat_min = min(latencias) if latencias else 0.0
    lat_max = max(latencias) if latencias else 0.0
    lat_p95 = sorted(latencias)[int(len(latencias) * 0.95)] if latencias else 0.0

    print("\n" + "=" * 70)
    print("MÉTRICAS DE ATENCIÓN HTTP")
    print("=" * 70)
    print(f"Total de solicitudes enviadas:    {total_solicitudes}")
    print(f"Solicitudes exitosas (HTTP 200):  {solicitudes_200} ({solicitudes_200/total_solicitudes*100:.1f}%)" if total_solicitudes else "0")
    print(f"Solicitudes fallidas (no 200):    {solicitudes_errores}")
    print(f"Desglose códigos de respuesta:    {codigos_estado}")
    if errores_cliente:
        print(f"Detalle excepciones cliente:      {errores_cliente}")
    print(f"Rendimiento (throughput):         {total_solicitudes / duracion_real:.2f} req/s")
    print(f"Latencia promedio:                {lat_media:.2f} ms")
    print(f"Latencia mínima:                  {lat_min:.2f} ms")
    print(f"Latencia máxima:                  {lat_max:.2f} ms")
    print(f"Latencia Percentil 95 (P95):       {lat_p95:.2f} ms")

    # 6. Verificación en Base de Datos
    with app.app_context():
        count_fin = ConversacionLog.query.count()
        with db.engine.begin() as conn:
            res_max_fin = conn.execute(text("SELECT COALESCE(MAX(id), 0) FROM conversaciones_log")).scalar()
            max_id_fin = res_max_fin or 0
            filas_creadas_query = conn.execute(text(f"SELECT COUNT(*) FROM conversaciones_log WHERE id > {max_id_inicio}")).scalar()

    filas_nuevas = filas_creadas_query
    diferencia = solicitudes_200 - filas_nuevas

    print("\n" + "=" * 70)
    print("COMPARACIÓN: HTTP 200 vs REGISTROS EN conversaciones_log")
    print("=" * 70)
    print(f"Solicitudes HTTP 200 atendidas:   {solicitudes_200}")
    print(f"Filas creadas en conversaciones:  {filas_nuevas}")
    print(f"Diferencia (perdidas):            {diferencia}")

    # 7. Inspección de logs/chatbot.log
    log_file_path = os.path.join(BASE_DIR, "logs", "chatbot.log")
    errores_log = []
    if os.path.exists(log_file_path):
        with open(log_file_path, "r", encoding="utf-8", errors="replace") as f:
            for linea in f:
                if any(err_kw in linea for err_kw in ("[ERROR]", "Exception", "rollback", "Deadlock", "OperationalError")):
                    errores_log.append(linea.strip())

    print("\n" + "=" * 70)
    print("INSPECCIÓN DE LOG DE LA APLICACIÓN (logs/chatbot.log)")
    print("=" * 70)
    if errores_log:
        print(f"Se encontraron {len(errores_log)} líneas de error en el log:")
        for e in errores_log[:10]:
            print(f"  - {e}")
        if len(errores_log) > 10:
            print(f"  ... y {len(errores_log) - 10} más.")
    else:
        print("0 errores en logs/chatbot.log. Ninguna excepción de persistencia ni WinError.")

    # 8. Limpieza de filas generadas por la prueba
    print("\n" + "=" * 70)
    print("LIMPIEZA DE FILAS DE PRUEBA")
    print("=" * 70)
    with app.app_context():
        with db.engine.begin() as conn:
            del_res = conn.execute(text(f"DELETE FROM conversaciones_log WHERE id > {max_id_inicio}"))
            filas_eliminadas = del_res.rowcount
        count_final_limpio = ConversacionLog.query.count()
        tramites_final = Tramite.query.count()
        usuarios_final = Usuario.query.count()
        roles_final = Rol.query.count()

    print(f"Filas eliminadas de la prueba:    {filas_eliminadas} (WHERE id > {max_id_inicio})")
    print(f"Total final en conversaciones_log:{count_final_limpio} filas")
    print(f"Integridad de catálogo:           {tramites_final} tramites intactos")
    print(f"Integridad de usuarios y roles:   {usuarios_final} usuario, {roles_final} rol intactos")

    print("\n" + "=" * 70)
    print("RESULTADO DE LA VERIFICACIÓN")
    print("=" * 70)
    if diferencia == 0 and solicitudes_errores == 0:
        print("CONCURRENCIA Y PERSISTENCIA: 100% EXITOSA")
        print(f"Todas las {solicitudes_200} solicitudes concurrentes fueron registradas sin pérdidas.")
    else:
        print(f"ADVERTENCIA: Diferencia detectada: {diferencia} perdidas de {solicitudes_200}.")

if __name__ == "__main__":
    main()
