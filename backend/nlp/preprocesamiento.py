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
PALABRAS_CLAVE_COSTO = {"costo", "cuanto", "cuánto", "cuesta", "precio", "pago", "tasa", "monto", "valor", "arancel"}
PALABRAS_CLAVE_PLAZO = {"plazo", "dias", "días", "tiempo", "demora", "tarda", "duracion", "duración", "cuando", "cuándo"}


def detectar_subintencion_directa(texto_preprocesado):
    """
    Intercepta palabras clave directas en la consulta.
    """
    if any(palabra in texto_preprocesado for palabra in PALABRAS_CLAVE_PLAZO):
        return "plazo"
    if any(palabra in texto_preprocesado for palabra in PALABRAS_CLAVE_COSTO):
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
    if palabras & PALABRAS_AFIRMATIVAS:
        return "si"
    if palabras & PALABRAS_NEGATIVAS:
        return "no"
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
