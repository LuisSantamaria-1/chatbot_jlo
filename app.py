"""
app.py
------
Punto de entrada principal del Sistema Inteligente de Chatbot Municipal (MDJLO).
Inicializa la aplicación Flask a través del patrón Application Factory (backend.create_app).

Uso:
    python app.py
"""

import os
from backend import create_app

# Creación de la instancia de la aplicación con configuración modular
app = create_app()

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() in ("true", "1", "t")
    app.run(host="localhost", port=puerto, debug=debug)