"""
app.py
------
Punto de entrada principal del Sistema Inteligente de Chatbot Municipal (MDJLO).
Inicializa la aplicación Flask a través del patrón Application Factory (backend.create_app).

Uso:
    python app.py
"""

import os
import socket

# Comprobar antes de cargar el modelo: en Windows dos servidores de desarrollo
# pueden retener el mismo puerto y entregar versiones distintas del proyecto.
# El hijo del recargador reutiliza deliberadamente el socket de su padre.
if __name__ == '__main__' and os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
    puerto_solicitado = int(os.environ.get('PORT', 5000))
    try:
        conexion_previa = socket.create_connection(('localhost', puerto_solicitado), timeout=.5)
    except OSError:
        pass
    else:
        conexion_previa.close()
        raise SystemExit(f'El chatbot ya está abierto en http://localhost:{puerto_solicitado}/. Puedes usarlo allí. Si quieres reiniciarlo desde esta terminal, primero detén la instancia anterior con Ctrl+C en la terminal donde se inició.')

from backend import create_app

# En ejecución directa de desarrollo (python app.py), si no hay SECRET_KEY ni FLASK_DEBUG explícito,
# se activa debug para permitir el arranque interactivo local con clave de sesión efímera.
if __name__ == "__main__" and not os.environ.get("SECRET_KEY") and "FLASK_DEBUG" not in os.environ:
    os.environ["FLASK_DEBUG"] = "1"

# Creación de la instancia de la aplicación con configuración modular
app = create_app()

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() in ("true", "1", "t")
    app.run(host="localhost", port=puerto, debug=debug)
