from backend.models.db import db

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
        """Serializa el trámite para las respuestas de la API."""
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
    orden = db.Column(db.Integer, default=1)
    tramite_id = db.Column(db.Integer, db.ForeignKey("tramites.id"), nullable=False)

    def __repr__(self):
        return f"<Requisito {self.orden} de Tramite {self.tramite_id}>"
