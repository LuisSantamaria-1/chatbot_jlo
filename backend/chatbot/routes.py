"""
routes.py
---------
Endpoints del Chatbot Ciudadano y renderizado del portal principal.
"""

import random
import logging
import time
from flask import Blueprint, request, jsonify, render_template, session
from config import UMBRAL_CONFIANZA, UMBRAL_DUDA_MIN, UMBRAL_DUDA_MAX
from backend.models import Tramite
from backend.chatbot.conversaciones import registrar_conversacion
from backend.nlp import (
    preprocesar_texto,
    detectar_subintencion_directa,
    es_correccion_de_contexto,
    interpretar_confirmacion,
    detectar_frustracion,
    predecir_intencion,
    resolver_intencion_macro,
    INTENCIONES_MACRO,
    INTENTS_SEGUIMIENTO,
    modelo_nlp,
    cargar_modelo,
)
from backend.chatbot.mensajes import (
    MENSAJES_SALUDO,
    MENSAJES_DESPEDIDA,
    MENSAJES_CHARLA_CASUAL,
    MENSAJES_FALLBACK,
    MENSAJES_EMPATIA_FALLBACK,
)

logger = logging.getLogger(__name__)

chatbot_bp = Blueprint("chatbot", __name__)


@chatbot_bp.route("/", methods=["GET"])
def home():
    """Ruta pública del Portal Ciudadano."""
    return render_template("index.html")


def _procesar_mensaje_chat():
    """
    Procesa la consulta ciudadana y determina la respuesta correspondiente.
    """
    try:
        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            return jsonify({
                "status": "error",
                "mensaje": "No se recibió un cuerpo JSON válido con la llave 'mensaje'."
            }), 400

        mensaje = data.get("mensaje")

        if not mensaje or not isinstance(mensaje, str) or not mensaje.strip():
            return jsonify({
                "status": "fallback",
                "mensaje": "Por favor, escribe una pregunta o consulta sobre el trámite municipal que deseas realizar."
            }), 400

        global modelo_nlp
        if modelo_nlp is None:
            modelo_nlp = cargar_modelo()

        if modelo_nlp is None:
            return jsonify({
                "status": "error",
                "mensaje": "El modelo de procesamiento de lenguaje natural no está disponible en el servidor."
            }), 503

        texto_consulta = mensaje.strip()

        # --- Desambiguación de intención macro pendiente -------------------
        macro_pendiente = session.get("macro_pendiente")

        if macro_pendiente:
            texto_macro = preprocesar_texto(texto_consulta)
            clave_opcion, id_tramite_resuelto = resolver_intencion_macro(macro_pendiente, texto_macro)

            if clave_opcion == "no_seguro":
                mensaje_no_seguro = INTENCIONES_MACRO[macro_pendiente]["mensaje_no_seguro"]
                session.pop("macro_pendiente", None)
                return jsonify({
                    "status": "derivacion",
                    "intent": "no_seguro_macro",
                    "mensaje": mensaje_no_seguro,
                }), 200

            elif id_tramite_resuelto is not None:
                session.pop("macro_pendiente", None)
                tramite_resuelto = Tramite.query.filter_by(id_tramite=id_tramite_resuelto).first()

                if tramite_resuelto is not None:
                    session["tramite_actual"] = tramite_resuelto.id_tramite
                    lista_requisitos = [r.descripcion for r in tramite_resuelto.requisitos]
                    requisitos_texto = "\n".join(f"- {r}" for r in lista_requisitos)
                    mensaje_resp = (
                        f"Entendido. Para el trámite \"{tramite_resuelto.nombre}\" necesitas:\n"
                        f"{requisitos_texto}\n\n"
                        "¿Deseas conocer el costo o el plazo de atención de este trámite?"
                    )
                    return jsonify({
                        "status": "success",
                        "id_tramite": tramite_resuelto.id_tramite,
                        "intent": "resolucion_macro",
                        "nombre": tramite_resuelto.nombre,
                        "requisitos": lista_requisitos,
                        "mensaje": mensaje_resp,
                    }), 200
            else:
                config_macro = INTENCIONES_MACRO[macro_pendiente]
                return jsonify({
                    "status": "clarification",
                    "intent": macro_pendiente,
                    "mensaje": (
                        "Disculpa, no logré identificar la opción. " + config_macro["pregunta"]
                    ),
                }), 200

        # --- Bucle de confirmación: ¿hay una sugerencia pendiente? ---------
        id_tramite_pendiente = session.get("tramite_pendiente")

        if id_tramite_pendiente:
            texto_confirmacion = preprocesar_texto(texto_consulta)
            respuesta_confirmacion = interpretar_confirmacion(texto_confirmacion)

            if respuesta_confirmacion == "si":
                session.pop("tramite_pendiente", None)
                tramite_confirmado = Tramite.query.filter_by(
                    id_tramite=id_tramite_pendiente
                ).first()

                if tramite_confirmado is not None:
                    session["tramite_actual"] = tramite_confirmado.id_tramite
                    lista_requisitos = [r.descripcion for r in tramite_confirmado.requisitos]
                    requisitos_texto = "\n".join(f"- {r}" for r in lista_requisitos)
                    mensaje_resp = (
                        f"¡Perfecto! Para el trámite \"{tramite_confirmado.nombre}\" "
                        f"necesitas:\n{requisitos_texto}\n\n"
                        "¿Deseas conocer el costo o el plazo de atención de este trámite?"
                    )
                    return jsonify({
                        "status": "success",
                        "id_tramite": tramite_confirmado.id_tramite,
                        "intent": "confirmacion_positiva",
                        "nombre": tramite_confirmado.nombre,
                        "requisitos": lista_requisitos,
                        "mensaje": mensaje_resp,
                    }), 200

            elif respuesta_confirmacion == "no":
                session.pop("tramite_pendiente", None)
                return jsonify({
                    "status": "clarification_rejected",
                    "intent": "confirmacion_negativa",
                    "mensaje": "Entendido, disculpa la confusión. ¿Podrías indicarme nuevamente y con más detalle qué trámite municipal necesitas realizar?"
                }), 200

            else:
                session.pop("tramite_pendiente", None)

        intent_predicho, confianza = predecir_intencion(texto_consulta)

        logger.info(
            f"Query: '{texto_consulta}' | Intent: '{intent_predicho}' | "
            f"Confianza: {confianza:.4f} | tramite_actual en sesión: {session.get('tramite_actual')}"
        )

        # --- Caso 0: zona de duda (0.35 <= confianza <= 0.54) --------------
        if UMBRAL_DUDA_MIN <= confianza <= UMBRAL_DUDA_MAX and str(intent_predicho).startswith("T_"):
            tramite_duda = Tramite.query.filter_by(
                id_tramite=str(intent_predicho).strip()
            ).first()

            if tramite_duda is not None:
                mensaje_resp = (
                    f"No estoy 100% seguro de haberte entendido. 🤔 ¿Te refieres a los "
                    f"requisitos para '{tramite_duda.nombre}'? Si es así, dímelo y te "
                    "paso los datos."
                )
                session["tramite_pendiente"] = tramite_duda.id_tramite
                return jsonify({
                    "status": "clarification",
                    "intent": intent_predicho,
                    "confianza": round(confianza, 4),
                    "id_tramite_sugerido": tramite_duda.id_tramite,
                    "nombre_sugerido": tramite_duda.nombre,
                    "mensaje": mensaje_resp,
                }), 200

        # --- Caso 1: saludo -----------------------------------------------
        if intent_predicho == "saludo":
            session.pop("tramite_actual", None)
            session.pop("tramite_pendiente", None)
            session.pop("macro_pendiente", None)
            return jsonify({
                "status": "saludo",
                "intent": "saludo",
                "confianza": round(confianza, 4),
                "mensaje": random.choice(MENSAJES_SALUDO)
            }), 200

        # --- Caso 1a-bis: corrección de contexto (sin importar el intent predicho) ---
        if session.get("tramite_actual"):
            texto_correccion = preprocesar_texto(texto_consulta)
            if es_correccion_de_contexto(texto_correccion):
                session.pop("tramite_actual", None)
                session.pop("tramite_pendiente", None)
                return jsonify({
                    "status": "correction",
                    "intent": "correccion_contexto",
                    "confianza": round(confianza, 4),
                    "mensaje": "Disculpa la confusión 🙏 ¿Sobre qué trámite necesitas información entonces?"
                }), 200

        # --- Caso 1b: despedida ---------------------------------------------
        if intent_predicho == "despedida":
            session.pop("tramite_actual", None)
            session.pop("tramite_pendiente", None)
            return jsonify({
                "status": "despedida",
                "intent": "despedida",
                "confianza": round(confianza, 4),
                "mensaje": random.choice(MENSAJES_DESPEDIDA)
            }), 200

        # --- Caso 1c: charla casual (small talk) ---------------------------
        if intent_predicho == "charla_casual":
            return jsonify({
                "status": "charla_casual",
                "intent": "charla_casual",
                "confianza": round(confianza, 4),
                "mensaje": random.choice(MENSAJES_CHARLA_CASUAL)
            }), 200

        # --- Caso 1d: pregunta de seguimiento (costo / plazo) con trámite activo ---
        texto_norm = preprocesar_texto(texto_consulta)
        subintencion_activa = detectar_subintencion_directa(texto_norm)
        es_seguimiento_modelo = intent_predicho in INTENTS_SEGUIMIENTO and confianza >= UMBRAL_CONFIANZA
        if session.get("tramite_actual") and (subintencion_activa or es_seguimiento_modelo):
            id_tramite_actual = session.get("tramite_actual")
            tramite = Tramite.query.filter_by(id_tramite=id_tramite_actual).first()

            if tramite:
                tipo_seguimiento = subintencion_activa or ("costo" if intent_predicho == "consultar_costo" else "plazo")
                if tipo_seguimiento == "costo":
                    costo_str = (tramite.costo or "").strip()
                    if not costo_str or costo_str.lower() == "no especificado":
                        mensaje_resp = f"El costo del trámite \"{tramite.nombre}\" no se encuentra disponible actualmente en el sistema. Te sugerimos acudir directamente a la municipalidad para consultar esta información."
                    else:
                        mensaje_resp = f"El costo del trámite \"{tramite.nombre}\" es: {tramite.costo}."
                else:  # plazo
                    plazo_str = (tramite.plazo or "").strip()
                    if not plazo_str or plazo_str.lower() == "no especificado" or plazo_str.startswith("0 "):
                        mensaje_resp = f"El plazo de atención del trámite \"{tramite.nombre}\" no se encuentra disponible actualmente en el sistema. Te sugerimos acudir directamente a la municipalidad para consultar esta información."
                    else:
                        mensaje_resp = f"El plazo de atención del trámite \"{tramite.nombre}\" es: {tramite.plazo}."

                return jsonify({
                    "status": "success",
                    "intent": f"consultar_{tipo_seguimiento}",
                    "confianza": round(confianza, 4),
                    "id_tramite": tramite.id_tramite,
                    "nombre": tramite.nombre,
                    "costo": tramite.costo if tipo_seguimiento == "costo" else None,
                    "plazo": tramite.plazo if tipo_seguimiento == "plazo" else None,
                    "datosTramite": {
                        "id_tramite": tramite.id_tramite,
                        "nombre": tramite.nombre,
                        "costo": tramite.costo if tipo_seguimiento == "costo" else None,
                        "plazo": tramite.plazo if tipo_seguimiento == "plazo" else None,
                        "requisitos": [r.descripcion for r in tramite.requisitos]
                    },
                    "mensaje": mensaje_resp,
                }), 200

        # --- Caso 2: fuera de dominio o confianza insuficiente (RF04) ------
        if intent_predicho == "fuera_de_dominio" or round(confianza, 2) < UMBRAL_CONFIANZA:
            texto_normalizado_fallback = preprocesar_texto(texto_consulta)
            if detectar_frustracion(texto_normalizado_fallback):
                mensaje_resp = random.choice(MENSAJES_EMPATIA_FALLBACK)
            else:
                mensaje_resp = random.choice(MENSAJES_FALLBACK)
            return jsonify({
                "status": "fallback",
                "intent": intent_predicho,
                "confianza": round(confianza, 4),
                "mensaje": mensaje_resp
            }), 200

        # --- Caso 3: pregunta de seguimiento sin contexto previo ----------
        if intent_predicho in INTENTS_SEGUIMIENTO:
            return jsonify({
                "status": "fallback",
                "intent": intent_predicho,
                "confianza": round(confianza, 4),
                "mensaje": "Con gusto te indico eso, pero primero cuéntame: ¿qué trámite municipal deseas realizar?"
            }), 200

        # --- Intención macro: requiere desambiguación antes de responder ---
        if intent_predicho in INTENCIONES_MACRO and confianza >= UMBRAL_CONFIANZA:
            session["macro_pendiente"] = intent_predicho
            return jsonify({
                "status": "clarification",
                "intent": intent_predicho,
                "confianza": round(confianza, 4),
                "mensaje": INTENCIONES_MACRO[intent_predicho]["pregunta"],
            }), 200

        # --- Caso 4: trámite específico detectado (T_001, T_002, ...) ------
        tramite = Tramite.query.filter_by(id_tramite=str(intent_predicho).strip()).first()

        if not tramite:
            return jsonify({
                "status": "fallback",
                "intent": intent_predicho,
                "confianza": round(confianza, 4),
                "mensaje": "No encontré información detallada para el trámite correspondiente a tu consulta. Por favor, intenta reformular tu pregunta o acércate a la mesa de partes.",
                "id_tramite_detectado": intent_predicho
            }), 200

        session["tramite_actual"] = tramite.id_tramite

        texto_normalizado = preprocesar_texto(texto_consulta)
        subintencion = detectar_subintencion_directa(texto_normalizado)

        if subintencion == "costo":
            costo_str = (tramite.costo or "").strip()
            if not costo_str or costo_str.lower() == "no especificado":
                mensaje_resp = (
                    f"El costo para {tramite.nombre} no se encuentra disponible actualmente en el sistema. "
                    "Te sugerimos acudir directamente a la municipalidad para consultar esta información. "
                    "¿Te puedo ayudar con algo más?"
                )
            else:
                mensaje_resp = (
                    f"El costo para {tramite.nombre} es: {tramite.costo}. "
                    "¿Te puedo ayudar con algo más?"
                )
            return jsonify({
                "status": "success",
                "id_tramite": tramite.id_tramite,
                "intent": intent_predicho,
                "confianza": round(confianza, 4),
                "nombre": tramite.nombre,
                "costo": tramite.costo,
                "datosTramite": {
                    "id_tramite": tramite.id_tramite,
                    "nombre": tramite.nombre,
                    "costo": tramite.costo,
                    "plazo": None,
                    "requisitos": [r.descripcion for r in tramite.requisitos]
                },
                "mensaje": mensaje_resp,
            }), 200

        if subintencion == "plazo":
            plazo_str = (tramite.plazo or "").strip()
            if not plazo_str or plazo_str.lower() == "no especificado" or plazo_str.startswith("0 "):
                mensaje_resp = (
                    f"El plazo de atención para {tramite.nombre} no se encuentra disponible actualmente en el sistema. "
                    "Te sugerimos acudir directamente a la municipalidad para consultar esta información. "
                    "¿Te puedo ayudar con algo más?"
                )
            else:
                mensaje_resp = (
                    f"El plazo de atención para {tramite.nombre} es: {tramite.plazo}. "
                    "¿Te puedo ayudar con algo más?"
                )
            return jsonify({
                "status": "success",
                "id_tramite": tramite.id_tramite,
                "intent": intent_predicho,
                "confianza": round(confianza, 4),
                "nombre": tramite.nombre,
                "plazo": tramite.plazo,
                "datosTramite": {
                    "id_tramite": tramite.id_tramite,
                    "nombre": tramite.nombre,
                    "costo": None,
                    "plazo": tramite.plazo,
                    "requisitos": [r.descripcion for r in tramite.requisitos]
                },
                "mensaje": mensaje_resp,
            }), 200

        lista_requisitos = [r.descripcion for r in tramite.requisitos]
        requisitos_texto = "\n".join(f"- {r}" for r in lista_requisitos)

        mensaje_resp = (
            f"Para el trámite \"{tramite.nombre}\" necesitas:\n{requisitos_texto}\n\n"
            "¿Deseas conocer el costo o el plazo de atención de este trámite?"
        )

        return jsonify({
            "status": "success",
            "id_tramite": tramite.id_tramite,
            "intent": intent_predicho,
            "confianza": round(confianza, 4),
            "nombre": tramite.nombre,
            "requisitos": lista_requisitos,
            "datosTramite": {
                "id_tramite": tramite.id_tramite,
                "nombre": tramite.nombre,
                "costo": None,
                "plazo": None,
                "requisitos": lista_requisitos
            },
            "mensaje": mensaje_resp,
        }), 200

    except Exception as e:
        logger.error(f"Error en /api/chat: {e}")
        return jsonify({
            "status": "error",
            "mensaje": "Ocurrió un error inesperado al procesar tu solicitud. Intenta nuevamente más tarde."
        }), 500


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
