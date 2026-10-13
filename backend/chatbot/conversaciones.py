"""
backend/chatbot/conversaciones.py
---------------------------------
Servicio de auditoría, trazabilidad y persistencia de interacciones del chatbot (RF08).
Registra de forma anónima y no intrusiva cada turno conversacional.
"""

import hashlib
import logging
import uuid
from datetime import datetime, timezone
from flask import session
from backend.models import db, ConversacionLog

logger = logging.getLogger(__name__)

# Lista fija de tipos de respuesta permitidos en el sistema
TIPOS_RESPUESTA_VALIDOS = (
    "success",                 # Trámite, requisitos, costo o plazo atendido con éxito
    "clarification",           # Zona de duda (0.35-0.54) o desambiguación de macrointención
    "clarification_rejected",  # Ciudadano rechazó la sugerencia de trámite
    "fallback",                # Fuera de dominio, confianza insuficiente (<0.70) o sin contexto
    "saludo",                  # Saludo inicial
    "despedida",               # Despedida y cierre de interacción
    "charla_casual",           # Conversación informal (small talk)
    "correction",              # Corrección de contexto ("no, ese no")
    "derivacion",              # Derivación a ventanilla municipal (duda en macrointención)
    "error",                   # Entrada inválida o error en el procesamiento
)


def obtener_sesion_id_anonimo():
    """
    Genera un identificador de sesión anónimo y persistente para la interacción.
    No almacena cookies en claro, IPs, ni cabeceras privadas.
    Utiliza un hash criptográfico unidireccional SHA-256 de 64 caracteres.
    """
    if "_anon_token" not in session:
        session["_anon_token"] = uuid.uuid4().hex
    token = str(session.get("_anon_token") or "")
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:64]


def registrar_conversacion(
    mensaje_usuario,
    intencion_predicha="desconocido",
    confianza=0.0,
    tipo_respuesta="error",
    id_tramite=None,
    latencia_ms=0,
    sesion_id=None,
):
    """
    Registra el turno de conversación en la base de datos de auditoría.
    Garantía de disponibilidad: si la persistencia falla, ejecuta rollback,
    registra el error en logs y NO interrumpe la respuesta al ciudadano.
    """
    try:
        if not sesion_id:
            sesion_id = obtener_sesion_id_anonimo()

        # Truncar mensaje a 500 caracteres (privacidad y capacidad)
        mensaje_seguro = str(mensaje_usuario or "")[:500]

        # Garantizar que el tipo de respuesta pertenezca a la lista fija
        if tipo_respuesta not in TIPOS_RESPUESTA_VALIDOS:
            tipo_respuesta = "error"

        registro = ConversacionLog(
            sesion_id=sesion_id,
            mensaje_usuario=mensaje_seguro,
            intencion_predicha=str(intencion_predicha or "desconocido")[:60],
            confianza=float(confianza or 0.0),
            tipo_respuesta=tipo_respuesta,
            id_tramite=str(id_tramite)[:20] if id_tramite else None,
            latencia_ms=int(latencia_ms or 0),
            creado_en=datetime.now(timezone.utc),
        )

        db.session.add(registro)
        db.session.commit()

        logger.info(
            f"[AUDITORIA] Sesion: {sesion_id[:8]}... | Intent: {registro.intencion_predicha} "
            f"({registro.confianza:.2f}) | Tipo: {registro.tipo_respuesta} | "
            f"Tramite: {registro.id_tramite} | Latencia: {registro.latencia_ms}ms"
        )
        return registro

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al registrar conversacion en BD: {e}", exc_info=True)
        return None
