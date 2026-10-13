"""
scripts/prueba_carga.py
-----------------------
Suite de pruebas de rendimiento, latencia y carga concurrente para el Chatbot MDJLO.
Verifica el cumplimiento del requisito no funcional: Latencia < 5000 ms (p95 < 5 s) y 0 errores.

Ejecuta:
1. Medición de arranque en frío y warm-up.
2. Medición aislada del modelo NLP (predecir_intencion).
3. Latencia base secuencial (1 usuario, 200 peticiones por tipo: saludo, requisitos, costo, fallback, duda, macro).
4. Carga concurrente escalonada (1, 5, 10, 25, 50 usuarios virtuales x 60 segundos con sesiones independientes).
5. Exportación de métricas a rendimiento_resultados.csv y datos crudos a rendimiento_detalle.csv.
"""

import os
import sys
import time
import random
import threading
import subprocess
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import requests
import numpy as np
import pandas as pd

# Raíz del proyecto
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from backend.nlp import predecir_intencion

# Configuración del servidor de pruebas
PORT = 5055
SERVER_URL = f"http://127.0.0.1:{PORT}"
CHAT_URL = f"{SERVER_URL}/api/chat"

# Archivos de salida
CSV_RESULTADOS = os.path.join(BASE_DIR, "rendimiento_resultados.csv")
CSV_DETALLE = os.path.join(BASE_DIR, "rendimiento_detalle.csv")

# ==============================================================================
# BANCOS DE FRASES VARIADAS PARA PRUEBAS REALISTAS
# ==============================================================================
FRASES_SALUDO = [
    "hola buenos dias", "que tal", "buenas tardes asistente", "como te va",
    "hola leonardito", "buen dia", "saludos cordiales", "hola asistente municipal",
    "que tal como estas", "hola buenas", "buenos dias", "buenas noches",
    "hola estimado", "hola amigo", "saludos leonardito", "hola que tal",
    "buenas", "hola como vas", "buen dia municipalidad", "hola que tal buen dia"
]

FRASES_REQUISITOS = [
    "requisitos para certificado de numeracion",
    "que piden para licencia de funcionamiento de bodega",
    "requisitos para matrimonio civil comunitario",
    "documentos para visacion de planos para electrificacion",
    "como tramito la constancia de posesion",
    "que piden para aprobacion de habilitacion urbana",
    "documentos para duplicado de carnet de conductor de mototaxi",
    "requisitos para cambio de giro comercial",
    "que necesito para instalar agua potable y desague",
    "requisitos para separacion convencional y divorcio ulterior",
    "solicito copia certificada de resolucion de alcaldia",
    "como sacar permiso de construccion modal A",
    "que piden para autorizacion de rotura de pavimento",
    "requisitos para autorizacion de publicidad en la via publica",
    "como registro mi mototaxi en el padron municipal",
    "que papeles piden para transferir mi puesto en el mercado",
    "requisitos para inspeccion tecnica de seguridad itse",
    "como obtener carnet de sanidad para manipulador de alimentos",
    "documentos para prescripcion de deuda tributaria",
    "requisitos para constancia de no adeudo tributario municipal"
]

FRASES_COSTO = [
    "cuanto cuesta", "cual es el costo", "cuanto es la tasa municipal",
    "cual es el precio del tramite", "cuanto tengo que pagar en caja",
    "dime la tasa por favor", "cuanto vale este tramite", "costo del tramite",
    "cual es el monto a cancelar", "cuanto cobran por esto", "precio de este tramite",
    "cuanto me va a costar", "tarifa oficial", "cual es la tasa administrativa",
    "cuanto sale tramitar esto", "cuanto es el derecho de tramite", "costo administrativo",
    "cual es el valor de la tasa", "cuanto cuesta el tramite municipal", "monto de la tasa"
]

FRASES_PLAZO = [
    "cuanto tiempo demora", "en cuantos dias me responden", "cual es el plazo de atencion",
    "cuanto demora este tramite", "cuando me entregan mi documento", "plazo de respuesta",
    "cuantos dias habiles tarda", "cuanto tardan en resolver", "tiempo estimado de entrega",
    "demora mucho el tramite", "cuantos dias son para la respuesta", "tiempo de aprobacion",
    "cual es la duracion del tramite", "en que tiempo me dan resolucion", "plazo legal de atencion"
]

FRASES_FALLBACK = [
    "a que hora abren el cine en chiclayo", "cual es el sueldo del alcalde",
    "donde puedo almorzar un ceviche rico", "quien gano el partido de futbol",
    "como preparo una causa rellena", "a cuanto esta el dolar hoy",
    "donde venden repuestos de moto en lima", "como hackear una cuenta de red social",
    "pronostico del clima para chiclayo manana", "quien es el presidente de francia",
    "donde puedo comprar una bicicleta de carrera", "recomiendame una pelicula de accion",
    "a que hora sale el vuelo a lima", "como tocar guitarra acustica",
    "receta para hornear un pastel de chocolate", "cual es la capital de australia",
    "como reparar una llanta pinchada", "cuanto cuesta un pasaje a cusco",
    "canciones populares de cumbia", "como redactar una carta de amor"
]

FRASES_ZONA_DUDA = [
    "ola qiero un permiso para mi bodega q hago",
    "licencia para negocio",
    "quiero abrir una bodega",
    "permiso provisional",
    "licencia bodega",
    "permiso para poner tienda",
    "abrir negocio de abarrotes",
    "licencia local comercial",
    "autorizacion para venta",
    "permiso para mi tiendita",
    "licencia de tienda pequena",
    "tramite para bodega familiar",
    "abrir bodeguita en mi casa",
    "sacar permiso de bodega rapido",
    "licencia provisoria de negocio",
    "autorizacion para vender abarrotes",
    "licencia de funcionamiento bodega",
    "tramite bodega de barrio",
    "permiso provisional para tienda",
    "licencia de bodega sin inspeccion previa"
]

FRASES_MACRO = [
    "licencia",
    "quiero casarme",
    "matrimonio",
    "divorcio",
    "tramite vehicular",
    "permiso de mototaxi",
    "conexion de agua",
    "habilitacion de terreno",
    "flota de mototaxis",
    "matrimonio civil",
    "divorcio rapido",
    "agua y desague",
    "subdivision de lote",
    "renovacion de flota",
    "separacion mutua",
    "gestion de licencia",
    "asociacion de mototaxis",
    "agua potable",
    "licencia comercial",
    "boda civil"
]


# ==============================================================================
# MONITOR DE PROCESO (CPU Y RAM)
# ==============================================================================
class ResourceMonitor:
    def __init__(self, pid, intervalo=0.5):
        self.pid = pid
        self.intervalo = intervalo
        self.running = False
        self.thread = None
        self.cpu_samples = []
        self.mem_samples = []

    def start(self):
        self.running = True
        self.cpu_samples = []
        self.mem_samples = []
        self.thread = threading.Thread(target=self._monitor, daemon=True)
        self.thread.start()

    def _monitor(self):
        try:
            proc = psutil.Process(self.pid)
            # Primer sample de cpu para calibrar
            proc.cpu_percent(interval=None)
            while self.running:
                try:
                    cpu = proc.cpu_percent(interval=None)
                    mem_mb = proc.memory_info().rss / (1024 * 1024)
                    self.cpu_samples.append(cpu)
                    self.mem_samples.append(mem_mb)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break
                time.sleep(self.intervalo)
        except Exception:
            pass

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        avg_cpu = round(float(np.mean(self.cpu_samples)), 2) if self.cpu_samples else 0.0
        max_cpu = round(float(np.max(self.cpu_samples)), 2) if self.cpu_samples else 0.0
        avg_mem = round(float(np.mean(self.mem_samples)), 2) if self.mem_samples else 0.0
        max_mem = round(float(np.max(self.mem_samples)), 2) if self.mem_samples else 0.0
        return {
            "avg_cpu_pct": avg_cpu,
            "max_cpu_pct": max_cpu,
            "avg_mem_mb": avg_mem,
            "max_mem_mb": max_mem
        }


# ==============================================================================
# GESTIÓN DEL SERVIDOR
# ==============================================================================
def iniciar_servidor():
    """Inicia el servidor Flask en modo producción threaded en un subproceso."""
    runner_script = os.path.join(BASE_DIR, "scripts", "server_runner.py")
    cmd = [sys.executable, runner_script, str(PORT)]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Esperar a que el servidor responda
    inicio = time.perf_counter()
    servidor_listo = False
    for _ in range(30):
        time.sleep(0.2)
        try:
            r = requests.get(SERVER_URL, timeout=1)
            if r.status_code == 200:
                servidor_listo = True
                break
        except Exception:
            pass

    tiempo_arranque_ms = round((time.perf_counter() - inicio) * 1000, 2)
    if not servidor_listo:
        proc.terminate()
        raise RuntimeError("No se pudo iniciar el servidor en el puerto " + str(PORT))

    return proc, tiempo_arranque_ms


# ==============================================================================
# EJECUCIÓN PRINCIPAL DE PRUEBAS
# ==============================================================================
def main():
    print("=" * 80)
    print("INICIANDO BATERÍA DE PRUEBAS DE RENDIMIENTO Y CARGA (MDJLO CHATBOT)")
    print("=" * 80)
    print(f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version.split()[0]} | Sistema Operativo: {sys.platform}")
    print(f"Puerto de pruebas: {PORT} (threaded=True, debug=False)")

    # Iniciar servidor
    print("\n[PASO 1] Levantando servidor Flask aislado...")
    server_proc, arranque_ms = iniciar_servidor()
    server_pid = server_proc.pid
    print(f"-> Servidor levantado exitosamente (PID={server_pid}).")
    print(f"-> Tiempo de arranque en frío del proceso: {arranque_ms:.2f} ms")

    monitor = ResourceMonitor(server_pid)

    registros_resultados = []
    registros_detalle = []

    try:
        # ----------------------------------------------------------------------
        # PASO 2: ARRANQUE EN FRÍO Y WARM-UP DE /api/chat
        # ----------------------------------------------------------------------
        print("\n[PASO 2] Evaluando latencia de arranque en frío vs. warm-up en /api/chat...")
        warmup_session = requests.Session()
        latencias_warmup = []
        for i in range(6):
            t0 = time.perf_counter()
            r = warmup_session.post(CHAT_URL, json={"mensaje": "hola buenos dias"}, timeout=10)
            lat = (time.perf_counter() - t0) * 1000
            latencias_warmup.append(lat)
            print(f"   Petición {i+1}: {lat:.2f} ms (HTTP {r.status_code})")

        t_primera = latencias_warmup[0]
        t_posteriores_avg = np.mean(latencias_warmup[1:])
        print(f"-> Primera consulta (fría con carga de modelo/DB): {t_primera:.2f} ms")
        print(f"-> Promedio consultas siguientes (calientes): {t_posteriores_avg:.2f} ms")
        print(f"-> Factor de reducción de latencia post-arranque: {t_primera / t_posteriores_avg:.2f}x")

        # ----------------------------------------------------------------------
        # PASO 3: INFERENCIA NLP AISLADA (predecir_intencion solo)
        # ----------------------------------------------------------------------
        print("\n[PASO 3] Evaluando inferencia NLP aislada (predecir_intencion sin HTTP ni BD)...")
        pool_frases_nlp = (FRASES_SALUDO + FRASES_REQUISITOS + FRASES_FALLBACK +
                           FRASES_ZONA_DUDA + FRASES_MACRO)
        latencias_nlp = []
        for _ in range(200):
            frase = random.choice(pool_frases_nlp)
            t0 = time.perf_counter()
            _ = predecir_intencion(frase)
            latencias_nlp.append((time.perf_counter() - t0) * 1000)

        lat_nlp_arr = np.array(latencias_nlp)
        p95_nlp = np.percentile(lat_nlp_arr, 95)
        avg_nlp = np.mean(lat_nlp_arr)
        med_nlp = np.median(lat_nlp_arr)
        p90_nlp = np.percentile(lat_nlp_arr, 90)
        p99_nlp = np.percentile(lat_nlp_arr, 99)
        max_nlp = np.max(lat_nlp_arr)
        rps_nlp = 1000.0 / avg_nlp if avg_nlp > 0 else 0

        print(f"   Inferencia NLP (200 consultas):")
        print(f"   Promedio={avg_nlp:.2f}ms | Mediana={med_nlp:.2f}ms | p90={p90_nlp:.2f}ms | "
              f"p95={p95_nlp:.2f}ms | p99={p99_nlp:.2f}ms | Máx={max_nlp:.2f}ms | Capacidad={rps_nlp:.1f} preds/s")

        registros_resultados.append({
            "escenario": "inferencia_nlp_aislada",
            "usuarios": 1,
            "solicitudes": 200,
            "errores": 0,
            "promedio_ms": round(float(avg_nlp), 2),
            "mediana_ms": round(float(med_nlp), 2),
            "p90_ms": round(float(p90_nlp), 2),
            "p95_ms": round(float(p95_nlp), 2),
            "p99_ms": round(float(p99_nlp), 2),
            "max_ms": round(float(max_nlp), 2),
            "rps": round(float(rps_nlp), 2)
        })

        # ----------------------------------------------------------------------
        # PASO 4: LATENCIA BASE SECUENCIAL (1 usuario, 200 reqs por tipo)
        # ----------------------------------------------------------------------
        print("\n[PASO 4] Evaluando latencia base secuencial (1 usuario, 200 peticiones x 6 tipos = 1,200 reqs)...")
        tipos_base = [
            ("saludo", FRASES_SALUDO),
            ("requisitos", FRASES_REQUISITOS),
            ("costo_contexto", FRASES_COSTO),
            ("fallback", FRASES_FALLBACK),
            ("zona_duda", FRASES_ZONA_DUDA),
            ("macrointencion", FRASES_MACRO),
        ]

        base_session = requests.Session()

        for nombre_tipo, frases in tipos_base:
            latencias = []
            errores = 0
            t_inicio_escenario = time.perf_counter()

            for i in range(200):
                frase = frases[i % len(frases)]
                # Para costo_contexto, primero seteamos un trámite si no hay sesión iniciada
                if nombre_tipo == "costo_contexto" and i % 10 == 0:
                    base_session.post(CHAT_URL, json={"mensaje": "requisitos para certificado de numeracion"}, timeout=5)

                t0 = time.perf_counter()
                try:
                    resp = base_session.post(CHAT_URL, json={"mensaje": frase}, timeout=5)
                    lat = (time.perf_counter() - t0) * 1000
                    exito = (resp.status_code == 200)
                    if not exito:
                        errores += 1
                except Exception:
                    lat = (time.perf_counter() - t0) * 1000
                    exito = False
                    errores += 1

                latencias.append(lat)
                registros_detalle.append({
                    "timestamp": datetime.now().isoformat(),
                    "escenario": f"base_{nombre_tipo}",
                    "usuario_id": 1,
                    "tipo": nombre_tipo,
                    "latencia_ms": round(lat, 2),
                    "status_code": resp.status_code if exito else 0,
                    "exito": exito
                })

            duracion_total = time.perf_counter() - t_inicio_escenario
            arr = np.array(latencias)
            avg_m = np.mean(arr)
            med_m = np.median(arr)
            p90_m = np.percentile(arr, 90)
            p95_m = np.percentile(arr, 95)
            p99_m = np.percentile(arr, 99)
            max_m = np.max(arr)
            rps_m = len(latencias) / duracion_total if duracion_total > 0 else 0

            cumple = "CUMPLE (p95 < 5000ms, err=0)" if p95_m < 5000 and errores == 0 else "NO CUMPLE"
            print(f"   -> [{nombre_tipo:<15}] n=200 | Err={errores} | Prom={avg_m:.2f}ms | Med={med_m:.2f}ms | "
                  f"p90={p90_m:.2f}ms | p95={p95_m:.2f}ms | p99={p99_m:.2f}ms | Máx={max_m:.2f}ms | RPS={rps_m:.1f} | {cumple}")

            registros_resultados.append({
                "escenario": f"base_{nombre_tipo}",
                "usuarios": 1,
                "solicitudes": 200,
                "errores": errores,
                "promedio_ms": round(float(avg_m), 2),
                "mediana_ms": round(float(med_m), 2),
                "p90_ms": round(float(p90_m), 2),
                "p95_ms": round(float(p95_m), 2),
                "p99_ms": round(float(p99_m), 2),
                "max_ms": round(float(max_m), 2),
                "rps": round(float(rps_m), 2)
            })

        # ----------------------------------------------------------------------
        # PASO 5: CARGA CONCURRENTE (1, 5, 10, 25, 50 usuarios x 60 segs)
        # ----------------------------------------------------------------------
        print("\n[PASO 5] Evaluando carga concurrente escalonada (60s por nivel con diálogos de 3 mensajes)...")
        niveles_usuarios = [1, 5, 10, 25, 50]
        duracion_segundos = 60

        for num_u in niveles_usuarios:
            print(f"\n   >>> Ejecutando nivel: {num_u} usuarios concurrentes durante {duracion_segundos}s...")
            monitor.start()

            latencias_nivel = []
            errores_nivel = [0]
            solicitudes_nivel = [0]
            lock = threading.Lock()
            stop_event = threading.Event()

            def _trabajador_usuario(u_idx):
                session_u = requests.Session()
                while not stop_event.is_set():
                    # Secuencia de 3 mensajes contextuales: Requisitos -> Costo -> Plazo
                    dialogo = [
                        random.choice(FRASES_REQUISITOS),
                        random.choice(FRASES_COSTO),
                        random.choice(FRASES_PLAZO)
                    ]
                    for msg in dialogo:
                        if stop_event.is_set():
                            break
                        t0 = time.perf_counter()
                        resp_ok = False
                        code = 0
                        try:
                            r = session_u.post(CHAT_URL, json={"mensaje": msg}, timeout=10)
                            lat = (time.perf_counter() - t0) * 1000
                            code = r.status_code
                            if r.status_code == 200:
                                resp_ok = True
                        except Exception:
                            lat = (time.perf_counter() - t0) * 1000

                        with lock:
                            solicitudes_nivel[0] += 1
                            if not resp_ok:
                                errores_nivel[0] += 1
                            latencias_nivel.append(lat)
                            registros_detalle.append({
                                "timestamp": datetime.now().isoformat(),
                                "escenario": f"concurrente_{num_u}_usuarios",
                                "usuario_id": u_idx,
                                "tipo": "dialogo_3_pasos",
                                "latencia_ms": round(lat, 2),
                                "status_code": code,
                                "exito": resp_ok
                            })

                        # Pausa corta aleatoria entre mensajes (simula digitación humana ligera)
                        time.sleep(random.uniform(0.05, 0.20))

            t_inicio_nivel = time.perf_counter()
            with ThreadPoolExecutor(max_workers=num_u) as executor:
                futures = [executor.submit(_trabajador_usuario, i+1) for i in range(num_u)]
                time.sleep(duracion_segundos)
                stop_event.set()
                for f in as_completed(futures):
                    pass

            tiempo_real_nivel = time.perf_counter() - t_inicio_nivel
            stats_hw = monitor.stop()

            arr = np.array(latencias_nivel)
            tot_reqs = len(arr)
            err_reqs = errores_nivel[0]
            avg_c = np.mean(arr) if tot_reqs > 0 else 0
            med_c = np.median(arr) if tot_reqs > 0 else 0
            p90_c = np.percentile(arr, 90) if tot_reqs > 0 else 0
            p95_c = np.percentile(arr, 95) if tot_reqs > 0 else 0
            p99_c = np.percentile(arr, 99) if tot_reqs > 0 else 0
            max_c = np.max(arr) if tot_reqs > 0 else 0
            rps_c = tot_reqs / tiempo_real_nivel if tiempo_real_nivel > 0 else 0

            cumple = "CUMPLE (p95 < 5000ms, err=0)" if p95_c < 5000 and err_reqs == 0 else "NO CUMPLE"
            print(f"   [Nivel {num_u:02d} usuarios] Solicitudes={tot_reqs} | Errores={err_reqs} | "
                  f"Prom={avg_c:.2f}ms | Med={med_c:.2f}ms | p90={p90_c:.2f}ms | p95={p95_c:.2f}ms | "
                  f"p99={p99_c:.2f}ms | Máx={max_c:.2f}ms | RPS={rps_c:.2f}")
            print(f"                     Uso CPU servidor: Prom={stats_hw['avg_cpu_pct']}% (Máx={stats_hw['max_cpu_pct']}%) | "
                  f"RAM: Prom={stats_hw['avg_mem_mb']:.1f} MB (Máx={stats_hw['max_mem_mb']:.1f} MB) | {cumple}")

            registros_resultados.append({
                "escenario": f"concurrente_{num_u}_usuarios",
                "usuarios": num_u,
                "solicitudes": tot_reqs,
                "errores": err_reqs,
                "promedio_ms": round(float(avg_c), 2),
                "mediana_ms": round(float(med_c), 2),
                "p90_ms": round(float(p90_c), 2),
                "p95_ms": round(float(p95_c), 2),
                "p99_ms": round(float(p99_c), 2),
                "max_ms": round(float(max_c), 2),
                "rps": round(float(rps_c), 2)
            })

    finally:
        # Apagar servidor
        print("\n[PASO 6] Deteniendo servidor de pruebas...")
        server_proc.terminate()
        server_proc.wait()
        print("-> Servidor detenido exitosamente.")

    # Guardar CSVs
    print("\n[PASO 7] Guardando resultados tabulares...")
    df_res = pd.DataFrame(registros_resultados)
    df_res.to_csv(CSV_RESULTADOS, index=False, encoding="utf-8")
    print(f"-> Resumen guardado en: {CSV_RESULTADOS} ({len(df_res)} filas)")

    df_det = pd.DataFrame(registros_detalle)
    df_det.to_csv(CSV_DETALLE, index=False, encoding="utf-8")
    print(f"-> Detalle crudo guardado en: {CSV_DETALLE} ({len(df_det)} solicitudes registradas)")

    print("\n" + "=" * 80)
    print("RESUMEN CONSOLIDADO DE RENDIMIENTO Y LATENCIA:")
    print("=" * 80)
    print(df_res.to_string(index=False))
    print("=" * 80)


if __name__ == "__main__":
    main()
