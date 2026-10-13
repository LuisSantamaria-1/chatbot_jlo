"""
backend/__init__.py
-------------------
Factory de la aplicación Flask (Application Factory Pattern).
Configura CORS, base de datos MySQL y registra los Blueprints modulares.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request
from flask_cors import CORS
import config
from backend.models import db
from backend.chatbot import chatbot_bp
from backend.admin import admin_bp


def create_app(config_object=None):
    """
    Crea y configura la instancia de Flask.
    """
    app = Flask(
        __name__,
        template_folder=str(config.TEMPLATES_DIR),
        static_folder=str(config.STATIC_DIR),
    )

    if config_object:
        app.config.from_object(config_object)
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = config.SQLALCHEMY_DATABASE_URI
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config.SQLALCHEMY_TRACK_MODIFICATIONS
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = getattr(config, "SQLALCHEMY_ENGINE_OPTIONS", {})
        app.config["SESSION_COOKIE_NAME"] = config.SESSION_COOKIE_NAME
        app.config["SESSION_COOKIE_HTTPONLY"] = config.SESSION_COOKIE_HTTPONLY
        app.config["SESSION_COOKIE_SAMESITE"] = config.SESSION_COOKIE_SAMESITE
        app.config["SESSION_COOKIE_SECURE"] = config.SESSION_COOKIE_SECURE
        app.config["PERMANENT_SESSION_LIFETIME"] = config.PERMANENT_SESSION_LIFETIME

    # Validación estricta de SECRET_KEY:
    # Si no existe en el entorno y no es modo debug/testing, se niega a iniciar con RuntimeError explicativo.
    is_debug = (
        app.config.get("DEBUG", False)
        or os.environ.get("FLASK_DEBUG", "false").lower() in ("true", "1", "t")
    )
    is_testing = app.config.get("TESTING", False)
    secret_key = app.config.get("SECRET_KEY") or config.SECRET_KEY or os.environ.get("SECRET_KEY")

    if not secret_key:
        if is_debug or is_testing:
            import secrets
            secret_key = secrets.token_hex(32)
            logging.getLogger("backend").warning(
                "SECRET_KEY no configurada en el entorno. "
                "Se generó una clave aleatoria efímera para modo debug/pruebas."
            )
        else:
            raise RuntimeError(
                "SECRET_KEY no está configurada en las variables de entorno. "
                "Para generarla en producción ejecuta: "
                'python -c "import secrets; print(secrets.token_hex(32))"'
            )

    app.secret_key = secret_key
    app.config["SECRET_KEY"] = secret_key

    # Configuración de CORS
    CORS(
        app,
        resources={r"/api/*": {"origins": config.ORIGENES_PERMITIDOS}},
        supports_credentials=True,
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )

    # Inicializar Base de Datos con la App
    db.init_app(app)

    # Registrar Blueprints Modulares
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(admin_bp)

    # Configuración de Logging Estándar con RotatingFileHandler (logs/chatbot.log)
    logs_dir = config.BASE_DIR / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / "chatbot.log"

    backend_logger = logging.getLogger("backend")
    if not any(isinstance(h, RotatingFileHandler) for h in backend_logger.handlers):
        file_handler = RotatingFileHandler(
            str(log_file),
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setFormatter(logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
        ))
        file_handler.setLevel(logging.INFO)
        backend_logger.setLevel(logging.INFO)
        backend_logger.addHandler(file_handler)

    if not any(isinstance(h, RotatingFileHandler) for h in app.logger.handlers):
        for h in backend_logger.handlers:
            if isinstance(h, RotatingFileHandler):
                app.logger.addHandler(h)
                break

    # Cabeceras de Seguridad HTTP (after_request)
    @app.after_request
    def agregar_cabeceras_seguridad(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        # Control de caché para rutas administrativas (/admin y /api/admin/*)
        if request.path == "/admin" or request.path.startswith("/admin/") or request.path.startswith("/api/admin/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # HSTS únicamente sobre solicitudes HTTPS
        if request.is_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Content-Security-Policy adaptada a los recursos del portal y panel
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "font-src 'self' data:; "
            "frame-ancestors 'self'"
        )
        return response

    return app
