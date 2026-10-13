"""
backend/models/conversacion_log.py
----------------------------------
Modelo de persistencia para el registro y auditoría de conversaciones del chatbot (RF08).
Registra cada turno de interacción de forma estructurada y anónima.
"""

from datetime import datetime, timezone
from backend.models.db import db


class ConversacionLog(db.Model):
    __tablename__ = "conversaciones_log"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sesion_id = db.Column(db.String(64), nullable=False, index=True)
    mensaje_usuario = db.Column(db.String(500), nullable=False)
    intencion_predicha = db.Column(db.String(60), nullable=False)
    confianza = db.Column(db.Float, nullable=False)
    tipo_respuesta = db.Column(db.String(30), nullable=False)
    id_tramite = db.Column(db.String(20), nullable=True)
    latencia_ms = db.Column(db.Integer, nullable=False)
    creado_en = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        """Serializa el registro para la API de administración."""
        return {
            "id": self.id,
            "sesion_id": self.sesion_id,
            "mensaje_usuario": self.mensaje_usuario,
            "intencion_predicha": self.intencion_predicha,
            "confianza": round(float(self.confianza), 4) if self.confianza is not None else 0.0,
            "tipo_respuesta": self.tipo_respuesta,
            "id_tramite": self.id_tramite,
            "latencia_ms": self.latencia_ms,
            "creado_en": self.creado_en.isoformat() if self.creado_en else None,
        }

    def __repr__(self):
        return f"<ConversacionLog {self.id} | {self.intencion_predicha} ({self.tipo_respuesta})>"
