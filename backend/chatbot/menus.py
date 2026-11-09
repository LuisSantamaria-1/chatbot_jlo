"""Presentación de menús sin botones y sin cambiar claves de resolución."""

from backend.nlp.clasificador import INTENCIONES_MACRO


def _compactar(introduccion, alternativas, cierre):
    # Introducción + opciones + cierre, como máximo cinco líneas en total.
    ancho = 1 if len(alternativas) <= 3 else 2
    lineas = [introduccion]
    lineas.extend(" · ".join(alternativas[i:i + ancho]) for i in range(0, len(alternativas), ancho))
    return "\n".join([*lineas, cierre])


def menu_macro(clave, grupo=None):
    config = INTENCIONES_MACRO[clave]
    grupos = config.get("grupos", {})
    if grupos and grupo not in grupos:
        alternativas = [f'{k}) {g["etiqueta"]}' for k, g in grupos.items()]
        return _compactar("¿Con qué se relaciona tu caso?", alternativas,
                          "Respóndeme con el número o cuéntame tu caso"), 1, None
    claves = grupos[grupo]["opciones"] if grupos else list(config["opciones"])
    etiquetas = [f'{k}) {config["opciones"][k]["etiqueta"]}' for k in claves]
    introduccion = f'{grupos[grupo]["etiqueta"]}: ¿cuál es tu caso?' if grupos else config["pregunta"]
    return _compactar(introduccion, etiquetas, "Respóndeme con la opción o cuéntame tu caso"), 2 if grupos else 1, grupo
