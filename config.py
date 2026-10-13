"""
config.py
---------
Configuración centralizada para el Chatbot Municipal MDJLO.
Define credenciales de base de datos MySQL, rutas del sistema y parámetros de NLP.
"""

import os
from pathlib import Path

# Directorios base y rutas de datos
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# Rutas de archivos y artefactos
MODEL_PATH = DATA_DIR / "modelo_intenciones.joblib"
CSV_TRAMITES_PATH = DATA_DIR / "tramites.csv"
CSV_DATASET_PATH = DATA_DIR / "dataset_nlp.csv"

# Rutas de plantillas y estáticos
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Configuración de Base de Datos MySQL (HeidiSQL - municipal_db)
MYSQL_URI_DEFAULT = "mysql+pymysql://root:@127.0.0.1:3306/municipal_db"
SQLALCHEMY_DATABASE_URI = os.environ.get(
    "DATABASE_URL",
    os.environ.get("MYSQL_URL", MYSQL_URI_DEFAULT)
)
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_pre_ping": True,
    "pool_recycle": 280,
}

# Configuración de Sesión y Seguridad Flask
# SECRET_KEY se lee exclusivamente de la variable de entorno SECRET_KEY (sin valor por defecto en código).
SECRET_KEY = os.environ.get("SECRET_KEY")

SESSION_COOKIE_NAME = "mdjlo_session"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
# Cookie Secure: False en desarrollo local, True en producción (HTTPS). Se controla vía COOKIE_SECURE.
SESSION_COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() in ("true", "1", "t")
PERMANENT_SESSION_LIFETIME = 1800

# Orígenes CORS permitidos
ORIGENES_PERMITIDOS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Parámetros del modelo NLP y Umbrales de Confianza (RF04)
UMBRAL_CONFIANZA = 0.70
UMBRAL_DUDA_MIN = 0.35
UMBRAL_DUDA_MAX = 0.54
