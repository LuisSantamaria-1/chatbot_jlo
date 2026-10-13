"""
scripts/benchmark_latencia_fase2.py
-----------------------------------
Mide la latencia base de /api/chat (50 consultas por 3 tipos) sobre un servidor
Flask real en producción (debug=False, threaded=True) para verificar el impacto
de pool_pre_ping y pool_recycle en la latencia y en el percentil P95.
"""

import sys
import os
import time
import subprocess
import requests
import numpy as np

PORT = 5058
BASE_URL = f"http://127.0.0.1:{PORT}"
CHAT_URL = f"{BASE_URL}/api/chat"

FRASES_SALUDO = [
    "hola buenos dias", "buenas tardes asistente", "hola que tal", "buen dia",
    "hola como estas", "saludos cordiales", "hola asistente municipal", "buenas noches"
]

FRASES_REQUISITOS = [
    "cuales son los requisitos para licencia de funcionamiento",
    "requisitos para matrimonio civil",
    "que necesito para duplicado de licencia",
    "requisitos para cambio de giro en licencia",
    "cuales son los requisitos para autorizacion de anuncio publicitario"
]

FRASES_SEGUIMIENTO_COSTO = [
    "cuanto cuesta este tramite", "cual es el costo oficial", "dime la tasa a pagar",
    "cual es el precio de este tramite", "cuanto es el derecho de tramite"
]


def iniciar_servidor():
    runner_script = os.path.join(os.path.dirname(__file__), "server_runner.py")
    cmd = [sys.executable, runner_script, str(PORT)]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for _ in range(40):
        time.sleep(0.2)
        try:
            r = requests.get(f"{BASE_URL}/", timeout=1)
            if r.status_code == 200:
                return proc
        except Exception:
            pass

    proc.terminate()
    raise RuntimeError("No se pudo iniciar el servidor en el puerto " + str(PORT))


def main():
    print(f"Levantando servidor en puerto {PORT} (debug=False, threaded=True)...")
    server_proc = iniciar_servidor()

    try:
        session = requests.Session()

        # Warm-up (3 peticiones para asegurar carga de modelos)
        for _ in range(3):
            session.post(CHAT_URL, json={"mensaje": "hola"}, timeout=5)

        tipos = [
            ("saludo", FRASES_SALUDO),
            ("requisitos_bd", FRASES_REQUISITOS),
            ("seguimiento_costo_bd", FRASES_SEGUIMIENTO_COSTO),
        ]

        todas_latencias = []
        resultados_por_tipo = {}

        for nombre, frases in tipos:
            latencias = []
            errores = 0

            # Si es seguimiento, inicializamos trámite en sesión
            if "seguimiento" in nombre:
                session.post(CHAT_URL, json={"mensaje": "requisitos para licencia de funcionamiento de riesgo bajo"}, timeout=5)

            for i in range(50):
                msg = frases[i % len(frases)]
                t0 = time.perf_counter()
                try:
                    resp = session.post(CHAT_URL, json={"mensaje": msg}, timeout=5)
                    lat_ms = (time.perf_counter() - t0) * 1000
                    if resp.status_code != 200:
                        errores += 1
                except Exception:
                    lat_ms = (time.perf_counter() - t0) * 1000
                    errores += 1

                latencias.append(lat_ms)
                todas_latencias.append(lat_ms)

            arr = np.array(latencias)
            resultados_por_tipo[nombre] = {
                "n": len(latencias),
                "errores": errores,
                "promedio": float(np.mean(arr)),
                "mediana": float(np.median(arr)),
                "p90": float(np.percentile(arr, 90)),
                "p95": float(np.percentile(arr, 95)),
                "p99": float(np.percentile(arr, 99)),
                "max": float(np.max(arr))
            }

        total_arr = np.array(todas_latencias)
        res_total = {
            "n": len(todas_latencias),
            "promedio": float(np.mean(total_arr)),
            "mediana": float(np.median(total_arr)),
            "p90": float(np.percentile(total_arr, 90)),
            "p95": float(np.percentile(total_arr, 95)),
            "p99": float(np.percentile(total_arr, 99)),
            "max": float(np.max(total_arr))
        }

        print("\n=== RESULTADOS DE LATENCIA BASE (50 consultas x 3 tipos = 150 total) ===")
        for k, v in resultados_por_tipo.items():
            print(f"[{k}] (n={v['n']}, err={v['errores']}):")
            print(f"   Promedio={v['promedio']:.2f}ms | Mediana={v['mediana']:.2f}ms | P90={v['p90']:.2f}ms | P95={v['p95']:.2f}ms | Máx={v['max']:.2f}ms")

        print("\n=== CONSOLIDADO GENERAL ===")
        print(f"Total: {res_total['n']} consultas")
        print(f"Promedio: {res_total['promedio']:.2f} ms")
        print(f"Mediana:  {res_total['mediana']:.2f} ms")
        print(f"P90:      {res_total['p90']:.2f} ms")
        print(f"P95:      {res_total['p95']:.2f} ms")
        print(f"P99:      {res_total['p99']:.2f} ms")
        print(f"Máximo:   {res_total['max']:.2f} ms")

    finally:
        server_proc.terminate()
        server_proc.wait(timeout=3)
        print("\nServidor de prueba finalizado.")


if __name__ == "__main__":
    main()
