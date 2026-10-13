"""
scripts/server_runner.py
------------------------
Lanzador del servidor Flask para pruebas de rendimiento y carga.
Ejecuta la aplicación en modo producción (debug=False, threaded=True) en un puerto aislado.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend import create_app

if __name__ == "__main__":
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else 5055
    if not os.environ.get("SECRET_KEY"):
        import secrets
        os.environ["SECRET_KEY"] = secrets.token_hex(32)
    app = create_app()
    app.run(host="127.0.0.1", port=puerto, debug=False, threaded=True)
