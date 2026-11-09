"""
preprocesamiento.py
-------------------
Funciones de limpieza, normalización léxica y detección de señales conversacionales.
"""

import re
import sys
import unicodedata
from backend.nlp.diccionario import traducir_jerga

# ---------------------------------------------------------------------------
# Función de preprocesamiento requerida para entrenar y deserializar el pipeline TF-IDF
# ---------------------------------------------------------------------------
def preprocesar_texto(texto):
    """
    Normaliza el texto para coincidir exactamente entre entrenamiento e inferencia:
      1. Minúsculas y recorte de espacios laterales.
      2. Eliminación de acentos/tildes (NFKD + descarte de marcas 'Mn').
      3. Eliminación de toda puntuación (conserva solo \\w y \\s).
      4. Colapso de espacios múltiples.
      5. Traducción de jerga y errores ortográficos frecuentes del dominio
         municipal vía traducir_jerga() ("kiero" -> "quiero", etc.).
    """
    if texto is None:
        return ""
    texto = str(texto).lower().strip()
    texto_normalizado = unicodedata.normalize("NFKD", texto)
    texto_sin_acentos = "".join(
        c for c in texto_normalizado if unicodedata.category(c) != "Mn"
    )
    texto_sin_puntuacion = re.sub(r"[^\w\s]", "", texto_sin_acentos, flags=re.UNICODE)
    texto_intermedio = re.sub(r"\s+", " ", texto_sin_puntuacion).strip()
    return traducir_jerga(texto_intermedio)


# Alias en __main__ para compatibilidad retroactiva con modelos joblib serializados
# en scripts ejecutados directamente como __main__.
sys.modules["__main__"].preprocesar_texto = preprocesar_texto

# ---------------------------------------------------------------------------
# Palabras clave de costo y plazo (subintenciones directas)
# ---------------------------------------------------------------------------
PALABRAS_CLAVE_COSTO = {"costo", "costos", "cuesta", "cuestan", "precio", "pago", "pagar", "tasa", "monto", "valor", "arancel", "tarifa", "cobran"}
PALABRAS_CLAVE_PLAZO = {"plazo", "plazos", "demora", "demoran", "tarda", "tardan", "duracion"}


def detectar_campos_consulta(texto_preprocesado):
    """Campos solicitados, con límites de palabra y soporte para preguntas dobles."""
    palabras = set(texto_preprocesado.split())
    campos = []
    pide_plazo = bool(palabras & PALABRAS_CLAVE_PLAZO or re.search(r"\b(?:cuanto tiempo|en que tiempo|que tiempo|cuantos dias|que dias|en cuantos dias|cuando (?:sale|entregan|me entregan|estara))\b", texto_preprocesado))
    costo_explicito = (palabras & (PALABRAS_CLAVE_COSTO | {'gratis', 'gratuito', 'gratuita', 'barato', 'barata', 'paga'})
                      or re.search(r'\bcuanto(?:\s+me)?\s+(?:sale|vale|costaria|saldria)\b', texto_preprocesado))
    if costo_explicito or (not pide_plazo and re.search(r"\bcuanto(?:\s+me)?\s+(?:es|seria)\b", texto_preprocesado)):
        campos.append("costo")
    if pide_plazo:
        campos.append("plazo")
    if palabras & {"requisito", "requisitos", "documentos", "papeles", "piden", "documentacion"} or re.search(r'\b(?:que necesito|que documento|que debo llevar|que llevo|que presento)\b', texto_preprocesado):
        campos.append("requisitos")
    return tuple(campos)


# Solo se reutiliza el trámite activo cuando la pregunta es elíptica.
# Cualquier tema adicional (incluso ajeno a la muni) debe pasar por clasificación.
_PALABRAS_SEGUIMIENTO = set("""
y el la los las un una de del para por en a al que cual cuales cuanto cuantos
me mi se es son sera seria lo le te tu usted con sin favor porfa porfis
ese esa este esta esto eso esos esas mismo misma tramite tramites municipal
puedes podria podrias puede decir decirme indicar indicarme saber dime dar dame
quiero quisiera deseo necesito conocer ver mostrar muestrame repite repetir
requisitos requisito documentos documento papeles piden necesitan necesario
costo costos cuesta cuestan precio pago pagar tasa monto valor arancel tarifa
cobran sale plazo plazos demora demoran tarda tardan duracion tiempo dias
cuando entregan entreguen entregarme estara cuanto hola buenas gracias tambien
entonces ahora nuevamente otra vez hola buenos dias tardes noches
""".split())


def es_seguimiento_contextual(texto_preprocesado):
    return bool(detectar_campos_consulta(texto_preprocesado)) and set(texto_preprocesado.split()) <= _PALABRAS_SEGUIMIENTO


def detectar_subintencion_directa(texto_preprocesado):
    """
    Intercepta palabras clave directas en la consulta.
    """
    campos = detectar_campos_consulta(texto_preprocesado)
    if "plazo" in campos:
        return "plazo"
    if "costo" in campos:
        return "costo"
    return None


# ---------------------------------------------------------------------------
# Señales de corrección de contexto (evita falsas despedidas)
# ---------------------------------------------------------------------------
SEÑALES_CORRECCION_CONTEXTO = {
    "no", "dije", "eso", "ese", "esa", "otro", "otra",
    "equivoque", "confundi", "error", "referia", "refiero", "mal",
}


def es_correccion_de_contexto(texto_preprocesado):
    """
    Se usa SOLO cuando el modelo ya predijo "despedida" pero hay un
    tramite_actual activo en sesión. Filtra casos donde el usuario corrige al bot.
    """
    palabras = set(texto_preprocesado.split())
    coincidencias = palabras & SEÑALES_CORRECCION_CONTEXTO
    return len(coincidencias) >= 2


# ---------------------------------------------------------------------------
# Bucle de confirmación (zona de duda)
# ---------------------------------------------------------------------------
PALABRAS_AFIRMATIVAS = {
    "si", "sisi", "sip", "correcto", "exacto", "eso", "asi",
    "afirmativo", "efectivamente", "dale", "vale", "ok", "okay", "claro",
}

PALABRAS_NEGATIVAS = {
    "no", "nel", "negativo", "otro", "otra", "nada",
}


def interpretar_confirmacion(texto_preprocesado):
    """
    Devuelve "si", "no" o None para resolver sugerencias en zona de duda.
    """
    palabras = set(texto_preprocesado.split())
    if palabras & PALABRAS_NEGATIVAS:
        return "no"
    # "Sí, pero quiero otro trámite" no confirma la sugerencia anterior.
    permitidas = PALABRAS_AFIRMATIVAS | {"es", "ese", "esa", "el", "la", "tramite", "por", "favor", "gracias"}
    if palabras & PALABRAS_AFIRMATIVAS and palabras <= permitidas:
        return "si"
    return None


# ---------------------------------------------------------------------------
# Detección de frustración
# ---------------------------------------------------------------------------
FRASES_FRUSTRACION = [
    "no funciona", "no sirve para nada", "no sirve", "pesimo servicio",
    "que mal servicio", "esto es un desastre", "no entiendes nada",
    "no me ayudas", "no me ayudas en nada", "eres inutil", "no entiendo nada",
    "esto no sirve", "que porqueria", "malisimo este chatbot", "no resuelves nada",
    "perdida de tiempo", "no ayudas en nada", "que bot mas malo",
    "no sabes nada", "eres pesimo", "que servicio tan malo",
]


def detectar_frustracion(texto_preprocesado):
    return any(frase in texto_preprocesado for frase in FRASES_FRUSTRACION)
