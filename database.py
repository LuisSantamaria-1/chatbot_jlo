"""
database.py
------------
Backend de la base de datos para el chatbot municipal.

Define el modelo relacional (Tramite 1---N Requisito) usando Flask-SQLAlchemy
y provee una función para poblar la base de datos a partir de tramites.csv.

Uso:
    python database.py

Esto creará (o recreará) el archivo SQLite `municipal.db` en el mismo
directorio, con las tablas ya pobladas a partir de tramites.csv.
"""

import csv
import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# ---------------------------------------------------------------------------
# Configuración de la aplicación Flask y la base de datos
# ---------------------------------------------------------------------------

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CSV_PATH = os.path.join(BASE_DIR, "tramites.csv")
DB_PATH = os.path.join(BASE_DIR, "municipal.db")

app = Flask(__name__)
# Para producción / MySQL, reemplazar por algo como:
# "mysql+pymysql://usuario:password@localhost/municipal_db"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ---------------------------------------------------------------------------
# Modelos de Seguridad (Acceso Administrativo)
# ---------------------------------------------------------------------------

class Rol(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    usuarios = db.relationship("Usuario", backref="rol", lazy=True)

class Usuario(db.Model):
    __tablename__ = "usuarios"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)


# ---------------------------------------------------------------------------
# Modelos (Tramite 1---N Requisito)
# ---------------------------------------------------------------------------

class Tramite(db.Model):
    __tablename__ = "tramites"

    id = db.Column(db.Integer, primary_key=True)
    id_tramite = db.Column(db.String(20), unique=True, nullable=False, index=True)
    nombre = db.Column(db.String(255), nullable=False)
    costo = db.Column(db.String(100), nullable=True)
    plazo = db.Column(db.String(100), nullable=True)

    # Relación uno-a-muchos: un trámite tiene varios requisitos.
    # cascade="all, delete-orphan" asegura que al borrar un trámite
    # también se borren sus requisitos asociados.
    requisitos = db.relationship(
        "Requisito",
        backref="tramite",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="Requisito.orden",
    )

    def to_dict(self):
        """Serializa el trámite (útil luego para las respuestas del chatbot en Flask)."""
        return {
            "id": self.id,
            "id_tramite": self.id_tramite,
            "nombre": self.nombre,
            "costo": self.costo,
            "plazo": self.plazo,
            "requisitos": [r.descripcion for r in self.requisitos],
        }

    def __repr__(self):
        return f"<Tramite {self.id_tramite} - {self.nombre}>"


class Requisito(db.Model):
    __tablename__ = "requisitos"

    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.Text, nullable=False)
    orden = db.Column(db.Integer, nullable=False, default=0)

    tramite_id = db.Column(db.Integer, db.ForeignKey("tramites.id", ondelete="CASCADE"), nullable=False)

    def __repr__(self):
        return f"<Requisito {self.orden}: {self.descripcion[:30]}...>"


# ---------------------------------------------------------------------------
# Poblado de la base de datos desde el CSV
# ---------------------------------------------------------------------------

def _limpiar_requisito(texto_requisito):
    """
    Quita la numeración inicial tipo '1. ', '2. ', etc. de cada requisito
    individual, ya que ese orden se guardará en la columna `orden`.
    """
    texto_requisito = texto_requisito.strip()
    partes = texto_requisito.split(". ", 1)
    if len(partes) == 2 and partes[0].strip().isdigit():
        return partes[1].strip()
    return texto_requisito


def poblar_base_datos(csv_path=CSV_PATH):
    """
    Lee tramites.csv y crea/actualiza los registros de Tramite y Requisito.

    - Si un ID_Tramite ya existe, se actualiza (evita duplicados si el
      script se ejecuta varias veces).
    - Los requisitos vienen separados por ' | ' dentro de una sola celda,
      por lo que se separan en filas individuales de la tabla Requisito.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"No se encontró el archivo CSV en: {csv_path}")

    with open(csv_path, newline="", encoding="utf-8") as f:
        lector = csv.DictReader(f)

        contador_nuevos = 0
        contador_actualizados = 0

        for fila in lector:
            id_tramite = fila["ID_Tramite"].strip()
            nombre = fila["Nombre"].strip()
            requisitos_raw = fila["Requisitos"].strip()
            costo = fila["Costo"].strip()
            plazo = fila["Plazo"].strip()

            tramite = Tramite.query.filter_by(id_tramite=id_tramite).first()

            if tramite is None:
                tramite = Tramite(id_tramite=id_tramite)
                db.session.add(tramite)
                contador_nuevos += 1
            else:
                # Si ya existe, limpiamos sus requisitos anteriores
                # para volver a insertarlos actualizados.
                tramite.requisitos.clear()
                contador_actualizados += 1

            tramite.nombre = nombre
            tramite.costo = costo
            tramite.plazo = plazo

            # Separar los requisitos por el delimitador ' | '
            lista_requisitos = [r.strip() for r in requisitos_raw.split("|") if r.strip()]

            for orden, req_texto in enumerate(lista_requisitos, start=1):
                requisito = Requisito(
                    descripcion=_limpiar_requisito(req_texto),
                    orden=orden,
                )
                tramite.requisitos.append(requisito)

        db.session.commit()

    print(f"Poblado completo: {contador_nuevos} trámites nuevos, "
          f"{contador_actualizados} trámites actualizados.")


def inicializar_bd(csv_path=CSV_PATH):
    """Crea las tablas de seguridad y trámites, genera el admin por defecto y llena los trámites."""
    with app.app_context():
        db.create_all()

        # 1. Crear el rol de administrador si no existe
        rol_admin = Rol.query.filter_by(nombre='Administrador').first()
        if not rol_admin:
            rol_admin = Rol(nombre='Administrador')
            db.session.add(rol_admin)
            db.session.commit()

        # 2. Crear los usuarios administradores por defecto si no existen
        for usr_name in ['admin', 'admin_jlo']:
            admin_user = Usuario.query.filter_by(username=usr_name).first()
            if not admin_user:
                nuevo_admin = Usuario(
                    username=usr_name,
                    password_hash=generate_password_hash('admin123'),
                    rol_id=rol_admin.id
                )
                db.session.add(nuevo_admin)
                db.session.commit()
                print(f"Usuario administrador '{usr_name}' creado con éxito.")

        # 3. Poblar los trámites
        poblar_base_datos(csv_path)


# ---------------------------------------------------------------------------
# Ejecución directa: python database.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    inicializar_bd()

    # Verificación rápida en consola
    with app.app_context():
        print("\n--- Verificación de datos cargados ---")
        for t in Tramite.query.all():
            print(f"\n[{t.id_tramite}] {t.nombre}")
            print(f"  Costo: {t.costo}")
            print(f"  Plazo: {t.plazo}")
            print("  Requisitos:")
            for r in t.requisitos:
                print(f"    {r.orden}. {r.descripcion}")
