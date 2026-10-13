"""
diccionario.py
--------------
Normalización léxica: jerga peruana y errores ortográficos frecuentes del dominio municipal.
"""

import re

DICCIONARIO_CIUDADANO = {
    "kiero": "quiero",
    "qiero": "quiero",
    "q": "que",
    "sakar": "sacar",
    "ola": "hola",
    "kuanto": "cuanto",
    "kuantp": "cuanto",
    "kuesta": "cuesta",
    "pa": "para",
    "lincencia": "licencia",
    "lisencia": "licencia",
    "jato": "casa",
    "chamba": "trabajo",
    "bro": "",
    "causa": "",
    "altoke": "rapido",
    "xd": "",
    "porfa": "por favor",
    "porfis": "por favor",
    "xfa": "por favor",
}


def traducir_jerga(texto):
    """
    Reemplaza palabra por palabra (no subcadenas) usando DICCIONARIO_CIUDADANO.
    Se espera recibir texto YA en minúsculas, sin tildes y sin puntuación
    (es decir, ya procesado por los primeros pasos de preprocesar_texto),
    para que la comparación contra las llaves del diccionario sea exacta.
    """
    palabras = texto.split()
    palabras_traducidas = [DICCIONARIO_CIUDADANO.get(p, p) for p in palabras]
    texto_traducido = " ".join(p for p in palabras_traducidas if p != "")
    return re.sub(r"\s+", " ", texto_traducido).strip()
