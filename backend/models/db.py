from flask_sqlalchemy import SQLAlchemy

# Instancia única de SQLAlchemy para evitar importaciones circulares
db = SQLAlchemy()
