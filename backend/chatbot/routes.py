"""
routes.py
---------
Endpoints del Chatbot Ciudadano y renderizado del portal principal.
"""

import logging
import time
from flask import Blueprint, request, render_template
from backend.chatbot.conversaciones import registrar_conversacion

logger = logging.getLogger(__name__)

chatbot_bp = Blueprint("chatbot", __name__)


@chatbot_bp.route("/", methods=["GET"])
def home():
    """Ruta pública del Portal Ciudadano."""
    return render_template("index.html")


def _procesar_mensaje_chat():
    from backend.chatbot.dialogo import procesar_mensaje_chat
    return procesar_mensaje_chat()


@chatbot_bp.route("/api/chat", methods=["POST"])
def chat():
    """
    Endpoint principal del Chatbot con manejo de contexto, diálogo guiado
    y registro estructurado de auditoría en un único punto (RF08).
    """
    t_inicio = time.perf_counter()

    # Procesar lógica de diálogo del chatbot
    response, status_code = _procesar_mensaje_chat()

    # Medir latencia de atención en milisegundos
    latencia_ms = int((time.perf_counter() - t_inicio) * 1000)

    # Invocar registro de conversación en un ÚNICO punto
    try:
        payload = response.get_json() or {}
        data = request.get_json(silent=True) or {}
        mensaje_raw = str(data.get("mensaje", "") if isinstance(data, dict) else "")

        registrar_conversacion(
            mensaje_usuario=mensaje_raw,
            intencion_predicha=str(payload.get("intent") or "desconocido"),
            confianza=float(payload.get("confianza") or 0.0),
            tipo_respuesta=str(payload.get("status") or "error"),
            id_tramite=payload.get("id_tramite") or payload.get("id_tramite_sugerido"),
            latencia_ms=latencia_ms,
        )
    except Exception as e:
        logger.error(f"Fallo en llamada a registrar_conversacion en chat(): {e}")

    return response, status_code
