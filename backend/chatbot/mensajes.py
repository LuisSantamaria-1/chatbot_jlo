"""
mensajes.py
-----------
Bancos de respuestas dinámicas del chatbot (saludo, despedida, fallback, empatía).
"""

MENSAJES_SALUDO = [
    "¡Hola! 👋 Soy Leonardito, el asistente virtual de la Municipalidad Distrital de José Leonardo Ortiz. ¿Sobre qué trámite municipal deseas consultar?",
    "¡Hola! 👋 Qué gusto saludarte. Soy Leonardito. ¿En qué trámite municipal te puedo orientar hoy?",
    "¡Buenas! Soy Leonardito, el asistente del TUPA de la MDJLO. Cuéntame, ¿qué trámite necesitas hacer?",
]

MENSAJES_DESPEDIDA = [
    "¡De nada! Ha sido un gusto ayudarte. Si necesitas consultar otro trámite del TUPA, aquí estaré. ¡Que tengas un excelente día! ✨",
    "¡Un gusto ayudarte! Cuando necesites otra consulta del TUPA, aquí me tienes. ¡Que estés muy bien!",
    "¡Hasta pronto! Si te surge otra duda sobre algún trámite municipal, no dudes en volver a escribirme.",
]

MENSAJES_CHARLA_CASUAL = [
    "¡Todo muy bien por aquí! 🤖 Aunque me encantaría charlar, mi sistema está configurado exclusivamente para ayudarte con los trámites y licencias del TUPA. ¿Tienes alguna consulta sobre eso?",
    "¡Todo excelente! 🤖 Soy un asistente enfocado en trámites municipales, así que no puedo charlar de otros temas, pero con gusto te ayudo si tienes alguna consulta del TUPA.",
]

MENSAJES_FALLBACK = [
    "Solo puedo orientarte sobre los trámites y procedimientos administrativos del TUPA de la Municipalidad Distrital de José Leonardo Ortiz (licencias comerciales, cambio de giro, duplicados, acceso a la información, etc.). Por favor, formula una consulta relacionada a trámites municipales.",
    "Mi especialidad es exclusivamente el TUPA de la Municipalidad (licencias, permisos, duplicados, etc.). ¿Podrías reformular tu consulta hacia algún trámite municipal?",
]

MENSAJES_EMPATIA_FALLBACK = [
    "Lamento que esto no te esté resultando útil 🙏 Mi función es acotada: solo puedo orientarte sobre trámites del TUPA municipal. Si me indicas qué trámite necesitas, con gusto te ayudo con eso.",
    "Entiendo tu frustración, y quiero ayudarte de la mejor forma posible. Mi alcance solo cubre trámites municipales del TUPA — dime qué trámite necesitas y te doy la información exacta.",
]
