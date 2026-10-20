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
_NS = ["no se", "no estoy seguro", "no tengo idea"]
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
            "a": {"id_tramite": "T_016", "palabras": {"normal", "estandar", "municipalidad", "aqui"}, "frases": ["horario normal", "horario de trabajo", "en horario"]},
            "b": {"id_tramite": "T_017", "palabras": {"publico", "local", "colegio", "iglesia"}, "frases": ["otro local", "local publico", "dentro del distrito"]},
            "c": {"id_tramite": "T_018", "palabras": {"noche", "finde", "sabado", "domingo", "feriado"}, "frases": ["fuera de horario", "fuera del horario", "fuera de hora", "fin de semana"]},
            "d": {"id_tramite": "T_019", "palabras": {"afuera", "ciudad", "provincia"}, "frases": ["fuera del distrito", "fuera de distrito", "otro distrito", "otra ciudad", "otra provincia"]},
            "e": {"id_tramite": "T_020", "palabras": {"domicilio", "hogar", "casa"}, "frases": ["mi casa", "en casa"]},
            "f": {"id_tramite": "T_021", "palabras": {"alcalde"}, "frases": ["el alcalde"]},
            "g": {"id_tramite": "T_022", "palabras": {"comunitario", "comunitaria", "grupal", "masivo", "colectivo"}, "frases": ["con otras parejas", "matrimonio comunitario"]},
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
    "consultar_publicidad_exterior": {
        "pregunta": ("Claro, te ayudo con el letrero o anuncio de tu negocio. ¿Tu anuncio va a tener luz?\n"
                    "a) No, es un letrero o aviso simple pegado a la fachada\n"
                    "b) Sí, es luminoso o iluminado (con luz, led o neón)\n"
                    "Respóndeme con la letra o cuéntame cómo es tu anuncio."),
        "opciones": {
            "a": {"id_tramite": "T_007", "palabras": {"simple", "sencillo", "normal", "comun", "toldo", "banner", "pintado"},
                "frases": ["sin luz", "no tiene luz", "no lleva luz", "no es luminoso", "no es iluminado", "sin led", "sin neon"]},
            "b": {"id_tramite": "T_060", "palabras": {"luminoso", "luminosa", "iluminado", "iluminada", "led", "neon", "luces", "luz"},
                "frases": ["con luz", "tiene luz", "lleva luz"]},
        },
        "frases_no_seguro": _NS,
        "mensaje_no_seguro": "Si tu anuncio no lleva ninguna luz, led ni neón, es el trámite de anuncio simple (opción a). Si lleva luz, es la opción b.",
    },
    "consultar_certificacion_sanitaria": {
        "pregunta": ("Claro, te ayudo con la certificación sanitaria de tu negocio. ¿Qué necesitas?\n"
                    "a) Sacar o renovar mi certificación sanitaria\n"
                    "b) Perdí o se malogró mi certificado y quiero un duplicado\n"
                    "c) Quiero dar de baja mi certificación (cierro mi negocio o cambié de actividad)\n"
                    "Respóndeme con la letra o cuéntame cuál necesitas."),
        "opciones": {
            "a": {"id_tramite": "T_028", "palabras": {"renovar", "renovacion", "obtener", "abrir", "apertura", "tramitar"},
                "frases": ["por primera vez", "primera vez", "sacar mi certificacion", "sacar la certificacion", "sacar mi certificado", "sacar el certificado"]},
            "b": {"id_tramite": "T_063", "palabras": {"duplicado", "perdi", "perdio", "perdida", "extravie", "extravio", "robaron", "robo", "malogro", "malogre", "deterioro", "copia"},
                "frases": []},
            "c": {"id_tramite": "T_064", "palabras": {"baja", "cerrar", "cierro", "cierre", "cancelar", "anular", "devolver", "cese"},
                "frases": ["dar de baja"]},
        },
        "frases_no_seguro": _NS,
        "mensaje_no_seguro": "Cuéntame si es porque vas a abrir o renovar tu negocio, si perdiste tu certificado o si vas a cerrar, y te oriento.",
    },
    "consultar_registro_canino": {
        "pregunta": ("Claro, te ayudo a registrar a tu perro. ¿Cómo es?\n"
                    "a) Un perro común (mestizo o de raza no peligrosa)\n"
                    "b) Un perro de raza considerada peligrosa (por ejemplo pitbull o rottweiler)\n"
                    "Respóndeme con la letra o cuéntame qué perro tienes."),
        "opciones": {
            "a": {"id_tramite": "T_023", "palabras": {"comun", "normal", "mestizo", "faldero", "chico", "pequeno", "criollo", "corriente"},
                "frases": ["no es peligroso", "no es peligrosa", "no es de raza peligrosa", "no peligroso", "no peligrosa"]},
            "b": {"id_tramite": "T_024", "palabras": {"peligroso", "peligrosa", "pitbull", "rottweiler", "agresivo", "dogo", "bullterrier", "fila"},
                "frases": ["bull terrier", "raza peligrosa", "es peligroso"]},
        },
        "frases_no_seguro": _NS,
        "mensaje_no_seguro": "Si tu perro es de una raza como pitbull o rottweiler, es la opción b. Si es mestizo o de raza común, es la opción a.",
    },
    "consultar_evento_publico": {
        "pregunta": ("Claro, te ayudo con tu actividad. ¿Qué vas a hacer?\n"
                    "a) Un espectáculo o evento con público (concierto, show, festival)\n"
                    "b) Instalar una feria, un circo o juegos mecánicos\n"
                    "Respóndeme con la letra o cuéntame qué vas a organizar."),
        "opciones": {
            "a": {"id_tramite": "T_009", "palabras": {"primera", "inicio", "separacion", "convencional", "mutuo", "acuerdo"}, "frases": ["primer paso", "por primera vez", "aun no tengo", "todavia no tengo", "no tengo la separacion"]},
            "b": {"id_tramite": "T_034", "palabras": {"ulterior", "final", "definitivo"}, "frases": ["ya tengo", "ya pasaron", "ya pase", "ya me dieron", "ya me aprobaron", "ya esta aprobada", "divorcio final", "divorcio ulterior"]},
        },
        "frases_no_seguro": _NS,
        "mensaje_no_seguro": "Si vas a instalar juegos, un circo o una feria, es la opción b. Si es un evento o show con público, es la opción a.",
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
            "a": {"id_tramite": "T_045", "palabras": {"registrar", "empadronar", "empadronamiento", "inscribir", "inscribirlo", "formalizar"}, "frases": ["por primera vez", "vehiculo nuevo", "mototaxi nuevo", "moto nueva"]},
            "b": {"id_tramite": "T_011", "palabras": {"renovar", "renovacion", "actualizar", "vencio", "vencieron", "vence", "revision", "vigente"}, "frases": ["tarjeta vencida", "esta vencida", "se vencio"]},
            "c": {"id_tramite": "T_049", "palabras": {"duplicado", "perdida", "perdi", "perdio", "robo", "robada", "robaron", "extravie", "extravio", "reposicion", "copia"}, "frases": ["se me perdio", "me robaron", "otra copia"]},
            "d": {"id_tramite": "T_012", "palabras": {"baja", "reemplazar", "sustituir", "chatarrear", "vender", "malogro", "malogrado", "reemplazo"}, "frases": ["dar de baja", "cambiar de unidad", "cambiar la unidad", "otra unidad", "cambiar mi moto", "cambiar mi vehiculo"]},
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
            "a": {"id_tramite": "T_010", "palabras": {"permiso", "asociacion", "formalizar", "empresa", "operar", "operacion"}, "frases": ["permiso nuevo", "nuevo permiso", "por primera vez", "formalizar mi"]},
            "b": {"id_tramite": "T_048", "palabras": {"renovar", "renovacion"}, "frases": ["renovar", "renovacion", "vencio", "vence", "vencer", "vencimiento", "diez anos", "10 anos"]},
            "c": {"id_tramite": "T_047", "palabras": {"incrementar", "aumentar", "agregar", "flota", "sumar", "ampliar"}, "frases": ["incrementar", "aumentar", "agregar", "mas vehiculos", "otro vehiculo"]},
            "d": {"id_tramite": "T_046", "palabras": {"paradero", "paraderos", "parada"}, "frases": ["zona de espera", "punto de espera"]},
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
    "consultar_puesto_mercado": {
        "pregunta": ("Claro, te ayudo con tu puesto del mercado. ¿Qué quieres hacer?\n"
                    "a) Conseguir un puesto o empadronarme\n"
                    "b) Renovar mi puesto porque se vence\n"
                    "c) Quedarme con el puesto de un familiar fallecido\n"
                    "d) Tomar un puesto abandonado o vacío\n"
                    "e) Arreglar o remodelar mi puesto\n"
                    "f) Cambiar lo que vendo (cambio de giro)\n"
                    "Respóndeme con la letra o cuéntame cuál necesitas."),
        "opciones": {
            "a": {"id_tramite": "T_014", "palabras": {"empadronar", "empadronarme", "empadronamiento", "carnet", "inscribir", "inscribirme", "conseguir", "conducir"},
                "frases": ["por primera vez", "puesto nuevo"]},
            "b": {"id_tramite": "T_050", "palabras": {"renovar", "renovacion", "vence", "vencer", "vencimiento", "vencio", "prorroga"}, "frases": []},
            "c": {"id_tramite": "T_051", "palabras": {"fallecio", "fallecimiento", "fallecido", "fallecida", "murio", "muerte", "heredar", "herencia", "difunto", "difunta"}, "frases": []},
            "d": {"id_tramite": "T_052", "palabras": {"abandonado", "abandono", "vacio", "vacante", "revertido", "desocupado", "libre", "cerrado"}, "frases": []},
            "e": {"id_tramite": "T_053", "palabras": {"arreglar", "remodelar", "reparar", "mantenimiento", "reconstruir", "remodelacion", "techo", "pintar"}, "frases": []},
            "f": {"id_tramite": "T_054", "palabras": {"giro", "rubro"},
                "frases": ["cambiar lo que vendo", "vender otra cosa", "vender otro", "otro giro", "cambiar de giro", "cambiar de negocio"]},
        },
        "frases_no_seguro": _NS,
        "mensaje_no_seguro": "No te preocupes. Lo más común es querer conseguir un puesto o renovar el que ya tienes. ¿Te sirve alguna de esas dos?",
    },
    "consultar_numeracion_municipal": {
        "pregunta": ("Claro, te ayudo con el número de tu inmueble. ¿Cuál es tu caso?\n"
                    "a) Mi casa o local ya existe y necesito el documento que certifique su número\n"
                    "b) Tengo un proyecto de construcción aprobado y necesito que le asignen número (a la entrada o a cada departamento o local)\n"
                    "Respóndeme con la letra o cuéntame tu caso."),
        "opciones": {
            "a": {"id_tramite": "T_015", "palabras": {"certificado", "certificacion", "constancia", "documento", "existe", "construida", "construido"},
                "frases": ["ya existe", "ya esta construid", "ya esta hecha", "ya esta hecho"]},
            "b": {"id_tramite": "T_055", "palabras": {"proyecto", "aprobado", "aprobada", "departamentos", "unidades", "asignen", "asignacion", "condominio"},
                "frases": ["cada departamento", "cada local", "licencia de edificacion"]},
        },
        "frases_no_seguro": _NS,
        "mensaje_no_seguro": "Según el TUPA, la asignación de numeración es solo para proyectos de edificación ya aprobados. Si tu casa o local ya existe, lo que corresponde es el certificado de numeración (opción a). ¿Te sirve?",
    },
    "consultar_catastro_predial": {
        "pregunta": ("Claro, te ayudo con el catastro de tu predio. ¿Qué necesitas?\n"
                    "a) Mi predio ya tiene código catastral y necesito el certificado\n"
                    "b) Mi predio no tiene código catastral y necesito certificarlo\n"
                    "c) Quiero actualizar los datos de mi predio en el catastro\n"
                    "Respóndeme con la letra o cuéntame tu caso."),
        "opciones": {
            "a": {"id_tramite": "T_057", "palabras": {"positivo"}, "frases": ["ya tiene", "si tiene", "ya esta registrad", "si esta registrad", "ya cuenta"]},
            "b": {"id_tramite": "T_058", "palabras": {"negativo"}, "frases": ["no tiene", "no esta registrad", "no figura", "no cuenta", "sin codigo"]},
            "c": {"id_tramite": "T_059", "palabras": {"actualizar", "actualizacion", "actualizado", "corregir", "ampliacion", "datos", "modificar", "errados"}, "frases": []},
        },
        "frases_no_seguro": _NS,
        "mensaje_no_seguro": "Si no sabes si tu predio ya tiene código catastral, acércate a la municipalidad y consulta en el área de catastro para que lo verifiquen. Cuando lo sepas, vuelve y te indico los requisitos.",
    },
    "consultar_licencia_funcionamiento": {
        "pregunta": ("Con gusto te oriento con tu licencia de funcionamiento. Depende del tipo de local, "
                    "¿cuál se parece más al tuyo?\n"
                    "a) Un negocio pequeño y sencillo (por ejemplo una oficina, una peluquería o una tienda chica)\n"
                    "b) Un negocio mediano (por ejemplo un restaurante, un consultorio o una botica)\n"
                    "c) Un negocio grande o con bastante gente (por ejemplo un supermercado, un gimnasio o una clínica)\n"
                    "d) Un negocio de mucha concurrencia o actividad delicada (por ejemplo una discoteca, un grifo o un hospital)\n"
                    "e) Represento a un mercado, galería o centro comercial completo\n"
                    "Respóndeme con la letra o cuéntame qué negocio tienes. Si no estás seguro, dímelo y te digo a quién consultar."),
        "opciones": {
            "a": {"id_tramite": "T_065", "palabras": {"oficina", "peluqueria", "pequeno", "chico", "chica", "chiquito", "bazar", "kiosko", "sencillo", "boutique"}, "frases": ["riesgo bajo", "bajo riesgo"]},
            "b": {"id_tramite": "T_066", "palabras": {"restaurante", "consultorio", "botica", "farmacia", "mediano", "panaderia", "polleria", "cevicheria"}, "frases": ["riesgo medio"]},
            "c": {"id_tramite": "T_067", "palabras": {"supermercado", "gimnasio", "clinica", "grande", "hotel", "colegio", "academia", "hostal"}, "frases": ["riesgo alto"]},
            "d": {"id_tramite": "T_068", "palabras": {"discoteca", "grifo", "hospital", "casino", "gasolinera", "fabrica", "discoteque", "tragamonedas"}, "frases": ["riesgo muy alto", "muy alto"]},
            "e": {"id_tramite": "T_069", "palabras": {"galeria", "corporativa", "corporativo", "propietarios"}, "frases": ["centro comercial", "galeria comercial", "mercado de abastos", "junta de propietarios", "mercado completo"]},
        },
        "frases_no_seguro": _NS,
        "mensaje_no_seguro": ("No hay problema. El nivel de riesgo lo determina la municipalidad según tu local, así que lo mejor es consultarlo en la "
                            "Subgerencia de Comercio y Licencias (Ofi_licencias@munijlo.gob.pe). Cuando lo sepas, dime y te paso los requisitos exactos."),
    },
}


def resolver_intencion_macro(clave_macro, texto_preprocesado):
    config = INTENCIONES_MACRO[clave_macro]
    if any(f in texto_preprocesado for f in config["frases_no_seguro"]):
        return "no_seguro", None
    palabras_usuario = texto_preprocesado.split()
    if len(palabras_usuario) == 1 and palabras_usuario[0] in config["opciones"]:
        k = palabras_usuario[0]
        return k, config["opciones"][k]["id_tramite"]
    mejor = None  # frases de varias palabras: gana la más larga
    for k, datos in config["opciones"].items():
        for f in datos.get("frases", ()):
            if f in texto_preprocesado and (mejor is None or len(f) > mejor[0]):
                mejor = (len(f), k, datos["id_tramite"])
    if mejor:
        return mejor[1], mejor[2]
    for k, datos in config["opciones"].items():
        for pc in datos["palabras"]:
            if difflib.get_close_matches(pc, palabras_usuario, n=1, cutoff=0.75):
                return k, datos["id_tramite"]
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
