"""
clasificador.py
---------------
Inferencia de intenciones con el pipeline TF-IDF + LinearSVC y desambiguación macro.
"""

import os
import difflib
import logging
import joblib
import numpy as np
from config import MODEL_PATH, BASE_DIR

logger = logging.getLogger(__name__)

# Carga segura del modelo serializado
modelo_nlp = None

def cargar_modelo():
    global modelo_nlp
    rutas_a_probar = [
        MODEL_PATH,
        BASE_DIR / "modelo_intenciones.joblib",
        BASE_DIR / "data" / "modelo_intenciones.joblib",
        BASE_DIR / "dataset" / "para ejecutar" / "modelo_intenciones.joblib",
    ]
    for ruta in rutas_a_probar:
        if os.path.exists(ruta):
            try:
                modelo_nlp = joblib.load(ruta)
                logger.info(f"Modelo NLP cargado correctamente desde: {ruta}")
                return modelo_nlp
            except Exception as e:
                logger.error(f"Error cargando modelo NLP desde {ruta}: {e}")
    logger.error("No se encontró el modelo de intenciones NLP en ninguna ruta esperada.")
    return None

# Carga inicial al importar
cargar_modelo()


# Intenciones de seguimiento
INTENTS_SEGUIMIENTO = {"consultar_costo", "consultar_plazo"}

# Correo institucional de licencias
CONTACTO_LICENCIAS = "Ofi_licencias@munijlo.gob.pe"

# ---------------------------------------------------------------------------
# Intenciones macro + desambiguación (clasificación jerárquica)
# ---------------------------------------------------------------------------
INTENCIONES_MACRO = {
    "consultar_matrimonio_civil": {
        "pregunta": (
            "Con gusto te oriento sobre el matrimonio civil. Hay varias modalidades, "
            "cada una con su propio costo:\n"
            "a) En la municipalidad, en horario normal de trabajo (S/ 240.00)\n"
            "b) En otro local público dentro del distrito (S/ 300.20)\n"
            "c) En la municipalidad, pero fuera del horario de trabajo (S/ 266.70)\n"
            "d) En otro local público fuera del distrito (S/ 344.90)\n"
            "e) En tu domicilio, dentro del distrito (S/ 290.10)\n"
            "f) Ceremonia oficiada por el Alcalde (S/ 390.10)\n"
            "g) Matrimonio civil comunitario, junto con otras parejas (S/ 100.10)\n"
            "Respóndeme con la letra o cuéntame cuál prefieres."
        ),
        "opciones": {
            "a": {"id_tramite": "T_016", "palabras": {"normal", "aqui", "municipalidad", "estandar"}},
            "b": {"id_tramite": "T_017", "palabras": {"otro", "publico", "distrito"}},
            "c": {"id_tramite": "T_018", "palabras": {"fuera", "horario", "noche", "finde"}},
            "d": {"id_tramite": "T_019", "palabras": {"otra", "ciudad", "afuera"}},
            "e": {"id_tramite": "T_020", "palabras": {"domicilio", "casa"}},
            "f": {"id_tramite": "T_021", "palabras": {"alcalde"}},
            "g": {"id_tramite": "T_022", "palabras": {"comunitario", "grupal", "masivo"}},
        },
        "frases_no_seguro": [
            "no se", "no lo se", "no estoy seguro", "no tengo idea",
            "ni idea", "no lo tengo claro", "no lo tengo muy claro",
        ],
        "mensaje_no_seguro": (
            "No hay apuro, tómate tu tiempo para decidir. La opción más común es "
            "la 'a' (en la municipalidad, en horario normal, S/ 240.00). Cuando "
            "estés listo, dime la letra o cuéntame qué modalidad prefieres."
        ),
    },
    "consultar_conexion_agua": {
        "pregunta": (
            "¿Necesitas la conexión de agua y desagüe a tu nombre como persona "
            "particular (dueño de una vivienda), o es para una empresa?"
        ),
        "opciones": {
            "natural": {
                "id_tramite": "T_025",
                "palabras": {"natural", "particular", "vivienda", "casa",
                             "propietario", "personal", "mio"},
            },
            "juridica": {
                "id_tramite": "T_026",
                "palabras": {"juridica", "empresa", "negocio", "constructora",
                             "compania", "razon", "empresarial"},
            },
        },
        "frases_no_seguro": [
            "no se", "no lo se", "no estoy seguro", "no tengo idea",
            "ni idea", "no lo tengo claro", "no lo tengo muy claro",
        ],
        "mensaje_no_seguro": (
            "No hay problema. Cuando tengas claro si el trámite es a tu nombre "
            "personal o a nombre de una empresa, dime y te paso los requisitos "
            "exactos."
        ),
    },
    "consultar_tramite_vehicular": {
        "pregunta": (
            "Cuéntame exactamente qué necesitas con TU vehículo:\n"
            "a) Registrar o empadronar un vehículo menor nuevo\n"
            "b) Renovar o actualizar la tarjeta de operatividad\n"
            "c) Sacar un duplicado de mi tarjeta (perdida o robada)\n"
            "d) Dar de baja mi vehículo o reemplazarlo por otro\n"
            "Respóndeme con la letra o cuéntame cuál necesitas."
        ),
        "opciones": {
            "a": {"id_tramite": "T_045", "palabras": {"registrar", "empadronar", "empadronamiento", "inscribir", "nuevo", "formalizar"}},
            "b": {"id_tramite": "T_011", "palabras": {"renovar", "papeles", "tarjeta", "actualizar", "vencio", "vencieron", "revision"}},
            "c": {"id_tramite": "T_049", "palabras": {"duplicado", "perdida", "robo", "robada", "extravie", "reposicion"}},
            "d": {"id_tramite": "T_012", "palabras": {"baja", "reemplazar", "cambiar", "sustituir", "chatarrear", "vender", "malogro"}},
        },
        "frases_no_seguro": [
            "no se", "no lo se", "no estoy seguro", "no tengo idea",
            "ni idea", "no lo tengo claro", "no lo tengo muy claro",
        ],
        "mensaje_no_seguro": (
            "No hay apuro. Cuando tengas claro si necesitas registrar tu vehículo, "
            "renovar o duplicar tu tarjeta, o dar de baja tu unidad, dime y te oriento."
        ),
    },
    "consultar_gestion_flota_vehicular": {
        "pregunta": (
            "Cuéntame qué necesitas para tu asociación o empresa de transporte:\n"
            "a) Un permiso NUEVO para operar el servicio\n"
            "b) Renovar el permiso de operación (vigencia 10 años)\n"
            "c) Incrementar mi flota (agregar vehículos a un permiso existente)\n"
            "d) Autorización para usar un paradero\n"
            "Respóndeme con la letra o cuéntame cuál necesitas."
        ),
        "opciones": {
            "a": {"id_tramite": "T_010", "palabras": {"permiso", "asociacion", "formalizar", "empresa", "operar", "operacion", "nuevo"}},
            "b": {"id_tramite": "T_048", "palabras": {"renovar", "renovacion", "permiso", "operacion", "vencio", "diez", "anos"}},
            "c": {"id_tramite": "T_047", "palabras": {"incrementar", "aumentar", "agregar", "flota", "nuevo", "vehiculo"}},
            "d": {"id_tramite": "T_046", "palabras": {"paradero", "autorizacion", "espera", "zona"}},
        },
        "frases_no_seguro": [
            "no se", "no lo se", "no estoy seguro", "no tengo idea",
            "ni idea", "no lo tengo claro", "no lo tengo muy claro",
        ],
        "mensaje_no_seguro": (
            "No hay apuro. Cuando tengas claro si necesitas un permiso nuevo, "
            "renovarlo, incrementar tu flota, o autorización de paradero, dime y te oriento."
        ),
    },
    "consultar_divorcio": {
        "pregunta": (
            "Para orientarte bien, cuéntame en qué etapa estás:\n"
            "a) Aún no tengo la separación convencional, es mi primer paso\n"
            "b) Ya tengo la separación convencional (pasaron 2+ meses) y quiero el divorcio final\n"
            "Respóndeme con la letra o cuéntame cuál es tu caso."
        ),
        "opciones": {
            "a": {"id_tramite": "T_009", "palabras": {"primera", "vez", "inicio", "separacion", "convencional", "mutuo", "acuerdo"}},
            "b": {"id_tramite": "T_034", "palabras": {"ya", "tengo", "ulterior", "final", "ya pase", "resolucion", "declaro"}},
        },
        "frases_no_seguro": [
            "no se", "no lo se", "no estoy seguro", "no tengo idea",
            "ni idea", "no lo tengo claro", "no lo tengo muy claro",
        ],
        "mensaje_no_seguro": (
            "No hay problema. Cuando sepas si ya tienes la separación convencional "
            "aprobada o es tu primer trámite, cuéntame y te oriento mejor."
        ),
    },
    "consultar_gestion_licencia": {
        "pregunta": (
            "Ya tienes una licencia de funcionamiento y quieres hacer algo con "
            "ella. Cuéntame exactamente qué necesitas:\n"
            "a) Cambiar el giro/rubro de mi negocio (sigo siendo el mismo dueño)\n"
            "b) Transferir la licencia a otra persona (venta, herencia, cambio de dueño)\n"
            "c) Cerrar mi negocio (cese de actividades)\n"
            "d) Sacar un duplicado porque perdí o me robaron mi licencia\n"
            "Respóndeme con la letra o cuéntame cuál necesitas."
        ),
        "opciones": {
            "a": {
                "id_tramite": "T_002",
                "palabras": {"giro", "rubro", "cambiar", "cambio", "actividad"},
            },
            "b": {
                "id_tramite": "T_004",
                "palabras": {"transferir", "traspasar", "vender", "dueño",
                             "heredar", "titular", "propietario"},
            },
            "c": {
                "id_tramite": "T_005",
                "palabras": {"cerrar", "cese", "clausurar", "cesar", "baja"},
            },
            "d": {
                "id_tramite": "T_006",
                "palabras": {"duplicado", "perdi", "robaron", "extravie",
                             "robo", "copia"},
            },
        },
        "frases_no_seguro": [
            "no se", "no lo se", "no estoy seguro", "no tengo idea",
            "ni idea", "no lo tengo claro", "no lo tengo muy claro",
        ],
        "mensaje_no_seguro": (
            "No hay apuro. Cuando tengas claro si necesitas cambiar el giro, "
            "transferir la licencia, cerrar el negocio o sacar un duplicado, "
            "dime la letra o cuéntame qué pasó."
        ),
    },
}


def resolver_intencion_macro(clave_macro, texto_preprocesado):
    """
    Devuelve ("opcion", id_tramite) | ("no_seguro", None) | (None, None).
    """
    config = INTENCIONES_MACRO[clave_macro]

    if any(frase in texto_preprocesado for frase in config["frases_no_seguro"]):
        return "no_seguro", None

    palabras_usuario = texto_preprocesado.split()

    if len(palabras_usuario) == 1 and palabras_usuario[0] in config["opciones"]:
        clave = palabras_usuario[0]
        return clave, config["opciones"][clave]["id_tramite"]

    for clave_opcion, datos in config["opciones"].items():
        for palabra_clave in datos["palabras"]:
            coincidencias = difflib.get_close_matches(
                palabra_clave, palabras_usuario, n=1, cutoff=0.75
            )
            if coincidencias:
                return clave_opcion, datos["id_tramite"]

    return None, None


def predecir_intencion(texto_consulta):
    """
    Inferencia de intención + confianza con el modelo TF-IDF + LinearSVC.
    """
    global modelo_nlp
    if modelo_nlp is None:
        cargar_modelo()

    if hasattr(modelo_nlp, "decision_function"):
        scores = modelo_nlp.decision_function([texto_consulta])[0]
        T = 0.28  # temperatura de calibración del margen SVM
        exp_scores = np.exp((scores - np.max(scores)) / T)
        probabilidades = exp_scores / np.sum(exp_scores)
        max_idx = int(np.argmax(probabilidades))
        confianza = float(probabilidades[max_idx])
        intent_predicho = str(modelo_nlp.classes_[max_idx])
    elif hasattr(modelo_nlp, "predict_proba"):
        probs = modelo_nlp.predict_proba([texto_consulta])[0]
        max_idx = int(np.argmax(probs))
        confianza = float(probs[max_idx])
        intent_predicho = str(modelo_nlp.classes_[max_idx])
    else:
        intent_predicho = str(modelo_nlp.predict([texto_consulta])[0])
        confianza = 1.0
    return intent_predicho, confianza
