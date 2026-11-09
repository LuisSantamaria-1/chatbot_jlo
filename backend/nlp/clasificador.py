"""
clasificador.py
---------------
Inferencia de intenciones con el pipeline TF-IDF + LinearSVC y desambiguación macro.
"""

import os
import difflib
import re
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
            "e) Cambiar los datos de mi tarjeta de operatividad (por ejemplo el nombre o razón social del propietario)\n"
            "Respóndeme con la letra o cuéntame cuál necesitas."
        ),
        "opciones": {
            "a": {"id_tramite": "T_045", "palabras": {"registrar", "empadronar", "empadronamiento", "inscribir", "inscribirlo", "formalizar"}, "frases": ["por primera vez", "vehiculo nuevo", "mototaxi nuevo", "moto nueva"]},
            "b": {"id_tramite": "T_011", "palabras": {"renovar", "renovacion", "actualizar", "vencio", "vencieron", "vence", "revision", "vigente"}, "frases": ["tarjeta vencida", "esta vencida", "se vencio"]},
            "c": {"id_tramite": "T_049", "palabras": {"duplicado", "perdida", "perdi", "perdio", "robo", "robada", "robaron", "extravie", "extravio", "reposicion", "copia"}, "frases": ["se me perdio", "me robaron", "otra copia"]},
            "d": {"id_tramite": "T_012", "palabras": {"baja", "reemplazar", "sustituir", "chatarrear", "vender", "malogro", "malogrado", "reemplazo"}, "frases": ["dar de baja", "cambiar de unidad", "cambiar la unidad", "otra unidad", "cambiar mi moto", "cambiar mi vehiculo"]},
            "e": {"id_tramite": "T_247", "palabras": set(), "frases": ["cambiar los datos", "cambio de datos", "modificar los datos", "modificacion de datos", "cambiar el nombre", "razon social", "nombre del propietario", "nombre del titular", "datos del propietario", "datos de mi tarjeta"]},
        },
        "frases_no_seguro": [
            "no se", "no lo se", "no estoy seguro", "no tengo idea",
            "ni idea", "no lo tengo claro", "no lo tengo muy claro",
        ],
        "mensaje_no_seguro": (
            "No hay apuro. Cuando tengas claro si necesitas registrar tu vehículo, "
            "renovar o duplicar tu tarjeta, dar de baja tu unidad, o cambiar los datos de tu tarjeta. dime y te oriento."

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
    },"consultar_recurso_administrativo": {
        "pregunta": ("Entiendo que quieres impugnar una decisión de la municipalidad. ¿Cuál es tu caso?\n"
                    "a) Tengo una prueba o documento nuevo que antes no presenté (reconsideración, gratuito, 15 días hábiles)\n"
                    "b) No tengo pruebas nuevas, pero creo que interpretaron mal las pruebas que ya había, o es una cuestión de ley (apelación, gratuito, 30 días hábiles)\n"
                    "Respóndeme con la letra o cuéntame tu caso."),
        "opciones": {
            "a": {"id_tramite": "T_029", "palabras": {"reconsideracion", "reconsiderar", "reconsidero", "reconsiderarlo"},
                "frases": ["nueva prueba", "nuevas pruebas", "prueba nueva", "pruebas nuevas", "documento nuevo", "nuevo documento", "tengo una prueba", "tengo pruebas", "tengo un documento"]},
            "b": {"id_tramite": "T_070", "palabras": {"apelacion", "apelar", "apelo", "interpretaron", "interpretacion", "interpreto", "derecho"},
                "frases": ["no tengo pruebas", "no tengo prueba", "no tengo ninguna prueba", "sin pruebas", "no hay pruebas", "mal interpretad", "cuestion de ley", "tema de ley", "puro derecho", "superior"]},
        },
        "frases_no_seguro": ["no se", "no estoy seguro", "no tengo idea"],
        "mensaje_no_seguro": "Si tienes un documento o prueba nueva, es la reconsideración (opción a). Si no tienes pruebas nuevas pero crees que interpretaron mal las que ya había, o es un tema de ley, es la apelación (opción b).",
    },

    "consultar_habilitacion_urbana": {
        "pregunta": ("Claro, te ayudo con la habilitación urbana de tu terreno. Cuéntame cuál es tu caso:\n"
                    "PROYECTOS DEL ESTADO\n"
                    "a) Proyecto del Estado (inversión pública, obra o servicio público, o concesión)\n"
                    "b) Programa de vivienda del Estado (Bono Familiar Habitacional)\n"
                    "TERRENO RESIDENCIAL PEQUEÑO\n"
                    "c) Habilitar un terreno residencial de hasta 5 hectáreas, sin habilitar y de un solo lote\n"
                    "d) Modificar un proyecto de habilitación ya aprobado (por etapas)\n"
                    "HABILITAR Y CONSTRUIR A LA VEZ\n"
                    "e) Vender los lotes con garantía (venta garantizada de lotes)\n"
                    "f) Construir las viviendas para venderlas ya edificadas\n"
                    "CASOS ESPECIALES\n"
                    "g) Mi terreno está dentro de zona de patrimonio cultural, área natural protegida o ecosistema frágil\n"
                    "h) Reurbanizar una zona (mover vías, juntar o dividir lotes, demoler)\n"
                    "i) Mi terreno no colinda con zona urbana (o necesita un planeamiento integral)\n"
                    "j) Mi terreno colinda con zona arqueológica, patrimonio cultural o área natural protegida\n"
                    "k) Habilitar para industria, comercio o usos especiales\n"
                    "En los casos c a g, j y k la evaluación la puede hacer la Municipalidad o un Revisor Urbano (profesional externo autorizado, con plazos más cortos según el TUPA). "
                    "Si quieres el de Revisor Urbano, agrégalo a tu respuesta (por ejemplo: 'c con revisor'); si no, te paso el trámite con la Municipalidad.\n"
                    "Respóndeme con la letra o cuéntame tu caso. Si tu terreno es de otro tipo, dímelo y te digo a quién consultar."),
        "opciones": {
            "a": {"id_tramite": "T_075", "palabras": {"inversion", "concesion", "asociacion", "infraestructura", "estado", "estatal", "publica", "publico"},
                "frases": ["inversion publica", "obra publica", "asociacion publico", "servicios publicos", "proyecto del estado", "concesion privada", "entidad publica"]},
            "b": {"id_tramite": "T_076", "palabras": {"bono", "bfh", "beneficiarios"},
                "frases": ["bono familiar", "bono habitacional", "programa de vivienda", "sector vivienda", "reubicar beneficiarios", "reubicacion de beneficiarios"]},
            "c": {"id_tramite": "T_077", "id_revisor": "T_078", "palabras": {"residencial", "hectareas", "hectarea", "isla", "rustica", "rustico"}, "frases": []},
            "d": {"id_tramite": "T_079", "id_revisor": "T_080", "palabras": {"modificar", "modificacion", "etapa", "etapas", "integral", "vencido", "vencio"},
                "frases": ["modificar mi proyecto", "modificacion de proyecto", "proyecto integral", "por etapas", "plazo vencido"]},
            "e": {"id_tramite": "T_081", "id_revisor": "T_082", "palabras": {"garantizada", "garantizado"},
                "frases": ["venta garantizada", "garantizada de lotes", "vender lotes", "vender los lotes", "venta de lotes", "lotes con garantia"]},
            "f": {"id_tramite": "T_083", "id_revisor": "T_084", "palabras": {"viviendas", "casas", "edificadas", "edificada"},
                "frases": ["construir las viviendas", "construir viviendas", "venta de viviendas", "vender las viviendas", "vender viviendas", "vender casas", "viviendas edificadas", "urbanizacion con casas"]},
            "g": {"id_tramite": "T_085", "id_revisor": "T_086", "palabras": {"patrimonio", "arqueologico", "arqueologica", "protegida", "protegidas", "amortiguamiento", "ecosistema", "ecosistemas", "fragil", "fragiles", "natural", "reserva"},
                "frases": ["area natural", "zona arqueologica", "patrimonio cultural", "no encaja", "ninguna de las anteriores", "no esta en las anteriores"]},
            "h": {"id_tramite": "T_087", "palabras": {"reurbanizacion", "reurbanizar", "recomposicion", "demolicion", "demoler", "redimensionamiento", "redimensionar"},
                "frases": ["trama urbana", "mover vias", "reubicar vias", "reorganizar calles"]},
            "i": {"id_tramite": "T_088", "palabras": {"planeamiento", "aislado", "rural"},
                "frases": ["planeamiento integral", "no colinda", "no colindan", "lejos de la ciudad", "sin colindar", "terreno aislado", "fuera de la zona urbana", "colinda con predios", "colindan con predios", "sin ejecutar", "no ejecutado", "no ejecutados"]},
            "j": {"id_tramite": "T_089", "id_revisor": "T_090", "palabras": {"colinda", "colindan", "colindante", "colindantes"}, "frases": [],
                "todas": [["colind", "arqueolog"], ["colind", "patrimonio"], ["colind", "natural"], ["colind", "protegid"],
                            ["lado", "arqueolog"], ["lado", "natural"], ["lado", "protegid"],
                            ["junto", "patrimonio"], ["junto", "arqueolog"], ["junto", "natural"], ["junto", "protegid"]]},
            "k": {"id_tramite": "T_091", "id_revisor": "T_092", "palabras": {"industria", "industrial", "comercio", "comercial", "especiales"},
                "frases": ["usos especiales", "uso industrial", "uso comercial", "parque industrial", "para industria", "para comercio"]},
        },
        "frases_no_seguro": ["no se", "no estoy seguro", "no tengo idea", "es otro caso", "otro caso"],
        "mensaje_no_seguro": ("No hay problema. La habilitación urbana depende del tipo de proyecto y del tamaño del terreno, así que lo mejor es "
                            "consultarlo en la municipalidad (área de desarrollo territorial) antes de iniciar. Cuando lo sepas, dime la letra "
                            "y te paso los requisitos exactos."),
},
"consultar_lotes_urbanos": {
    "pregunta": ("Claro, te ayudo con tu lote. ¿Qué quieres hacer?\n"
                 "a) Dividir un lote en dos o más (subdivisión)\n"
                 "b) Juntar dos o más lotes en uno solo (acumulación)\n"
                 "Respóndeme con la letra o cuéntame qué quieres hacer."),
    "opciones": {
        "a": {"id_tramite": "T_074", "palabras": {"dividir", "subdividir", "subdivision", "partir", "fraccionar", "lotizar", "separar", "independizar", "repartir"},
              "frases": ["dividir mi", "partir mi", "sublotes"]},
        "b": {"id_tramite": "T_061", "palabras": {"juntar", "unir", "acumular", "acumulacion", "fusion", "fusionar"},
              "frases": ["en uno solo", "en un solo", "una sola unidad", "un solo lote"]},
    },
    "frases_no_seguro": ["no se", "no estoy seguro", "no tengo idea"],
    "mensaje_no_seguro": "Si quieres separar un lote en varios, es la opción a (subdivisión). Si quieres juntar varios en uno solo, es la b (acumulación).",
},
    "consultar_licencia_cesionario": {
        "pregunta": ("Entiendo, vas a funcionar dentro de un local que ya tiene licencia de otra persona. "
                    "Depende del tipo de local, ¿cuál se parece más?\n"
                    "a) Un local mediano (por ejemplo un restaurante, un consultorio o una botica)\n"
                    "b) Un local grande o con bastante gente (por ejemplo un supermercado, un gimnasio o una clínica)\n"
                    "c) Un local de mucha concurrencia o actividad delicada (por ejemplo una discoteca, un grifo o un hospital)\n"
                    "Respóndeme con la letra o cuéntame qué local es. Si no estás seguro, dímelo y te digo a quién consultar."),
        "opciones": {
            "a": {"id_tramite": "T_071", "palabras": {"restaurante", "consultorio", "botica", "farmacia", "mediano", "panaderia", "polleria", "cevicheria"}, "frases": ["riesgo medio"]},
            "b": {"id_tramite": "T_072", "palabras": {"supermercado", "gimnasio", "clinica", "grande", "hotel", "colegio", "academia", "hostal"}, "frases": ["riesgo alto"]},
            "c": {"id_tramite": "T_073", "palabras": {"discoteca", "grifo", "hospital", "casino", "gasolinera", "fabrica", "discoteque", "tragamonedas"}, "frases": ["riesgo muy alto", "muy alto"]},
        },
        "frases_no_seguro": ["no se", "no estoy seguro", "no tengo idea"],
        "mensaje_no_seguro": ("No hay problema. El nivel de riesgo lo determina la municipalidad según el local, así que lo mejor es consultarlo en la "
                            "Subgerencia de Comercio y Licencias (Ofi_licencias@munijlo.gob.pe). Cuando lo sepas, dime y te paso los requisitos exactos."),
    },
    # ---- PEGAR dentro de INTENCIONES_MACRO (antes del cierre '}') ----
    "consultar_itse": {
        "pregunta": ('Claro, te ayudo con la ITSE (la inspección de seguridad de defensa civil de tu local). Depende del tipo de negocio, ¿cuál se parece más al tuyo?\nPara sacarla por primera vez:\na) un negocio pequeño o sencillo (oficina, peluquería, tienda chica)\nb) un negocio mediano (restaurante, consultorio, botica)\nc) un negocio grande o con mucha gente (supermercado, gimnasio, clínica)\nd) un negocio de mucha concurrencia o actividad delicada (discoteca, grifo, hospital)\nPara RENOVAR mi certificado ITSE (antes de que se venza):\ne) renovar: negocio pequeño o sencillo\nf) renovar: negocio mediano\ng) renovar: negocio grande o con mucha gente\nh) renovar: negocio de mucha concurrencia o actividad delicada\ni) Perdí mi certificado ITSE y quiero un duplicado\nRespóndeme con la letra o cuéntame qué negocio tienes y si es nueva o renovación.'),
        "opciones": {
            "a": {"id_tramite": "T_100", "palabras": set(), "frases": ['oficina', 'peluqueria', 'tienda chica', 'tiendita', 'bazar', 'bodega', 'riesgo bajo', 'bajo riesgo']},
            "b": {"id_tramite": "T_101", "palabras": set(), "frases": ['restaurante', 'consultorio', 'botica', 'farmacia', 'panaderia', 'polleria', 'cevicheria', 'riesgo medio']},
            "c": {"id_tramite": "T_093", "palabras": set(), "frases": ['supermercado', 'gimnasio', 'clinica', 'hostal', 'hotel', 'colegio', 'academia', 'riesgo alto']},
            "d": {"id_tramite": "T_094", "palabras": set(), "frases": ['discoteca', 'grifo', 'hospital', 'casino', 'gasolinera', 'tragamonedas', 'riesgo muy alto', 'muy alto']},
            "e": {"id_tramite": "T_095", "palabras": set(), "frases": [], "todas": [['renov', 'oficina'], ['renov', 'peluqueria'], ['renov', 'tienda chica'], ['renov', 'tiendita'], ['renov', 'bazar'], ['renov', 'bodega'], ['renov', 'riesgo bajo'], ['renov', 'bajo riesgo'], ['venc', 'oficina'], ['venc', 'peluqueria'], ['venc', 'tienda chica'], ['venc', 'tiendita'], ['venc', 'bazar'], ['venc', 'bodega'], ['venc', 'riesgo bajo'], ['venc', 'bajo riesgo']]},
            "f": {"id_tramite": "T_096", "palabras": set(), "frases": [], "todas": [['renov', 'restaurante'], ['renov', 'consultorio'], ['renov', 'botica'], ['renov', 'farmacia'], ['renov', 'panaderia'], ['renov', 'polleria'], ['renov', 'cevicheria'], ['renov', 'riesgo medio'], ['venc', 'restaurante'], ['venc', 'consultorio'], ['venc', 'botica'], ['venc', 'farmacia'], ['venc', 'panaderia'], ['venc', 'polleria'], ['venc', 'cevicheria'], ['venc', 'riesgo medio']]},
            "g": {"id_tramite": "T_097", "palabras": set(), "frases": [], "todas": [['renov', 'supermercado'], ['renov', 'gimnasio'], ['renov', 'clinica'], ['renov', 'hostal'], ['renov', 'hotel'], ['renov', 'colegio'], ['renov', 'academia'], ['renov', 'riesgo alto'], ['venc', 'supermercado'], ['venc', 'gimnasio'], ['venc', 'clinica'], ['venc', 'hostal'], ['venc', 'hotel'], ['venc', 'colegio'], ['venc', 'academia'], ['venc', 'riesgo alto']]},
            "h": {"id_tramite": "T_098", "palabras": set(), "frases": [], "todas": [['renov', 'discoteca'], ['renov', 'grifo'], ['renov', 'hospital'], ['renov', 'casino'], ['renov', 'gasolinera'], ['renov', 'tragamonedas'], ['renov', 'riesgo muy alto'], ['renov', 'muy alto'], ['venc', 'discoteca'], ['venc', 'grifo'], ['venc', 'hospital'], ['venc', 'casino'], ['venc', 'gasolinera'], ['venc', 'tragamonedas'], ['venc', 'riesgo muy alto'], ['venc', 'muy alto']]},
            "i": {"id_tramite": "T_102", "palabras": set(), "frases": ['duplicado', 'perdi', 'se me perdio', 'extravie', 'otra copia', 'copia del certificado', 'me robaron']},
        },
        "frases_no_seguro": _NS,
        "mensaje_no_seguro": ('No hay problema. El nivel de riesgo lo determina la municipalidad según tu local; consúltalo en la Subgerencia de Comercio y Licencias (Ofi_licencias@munijlo.gob.pe). Cuando lo sepas, dime y te paso los requisitos.'),
    },
    "consultar_licencia_construccion": {
        "pregunta": ("Claro, te ayudo con la licencia para construir. ¿Qué vas a construir?\na) Una sola casa (vivienda unifamiliar) de hasta 120 m², que sea lo único construido en el lote\nb) Vivienda, edificio de departamentos o condominio de hasta 5 pisos y hasta 3000 m² techados\nc) Vivienda multifamiliar, quinta o condominio de MÁS de 5 pisos o más de 3000 m² techados\nd) Un edificio de uso mixto: vivienda con comercio\ne) Una obra en un predio declarado Patrimonio Cultural de la Nación\nSi es otra obra (ampliar, remodelar, demoler, cercar, o un local comercial, industrial o del Estado) dímelo así. Si quieres que la evalúe un Revisor Urbano, agrega 'con revisor' (por ejemplo: 'b con revisor'). Respóndeme con la letra o cuéntame tu caso."),
        "opciones": {
            "a": {"id_tramite": "T_103", "palabras": set(), "frases": ['120 m', '120 metros', 'unifamiliar', 'una sola vivienda', 'casa sencilla', 'casita', 'unica edificacion', 'terreno vacio', 'lote vacio', 'una casa']},
            "b": {"id_tramite": "T_115", "id_revisor": "T_116", "palabras": set(), "frases": ['hasta cinco pisos', 'hasta 5 pisos', 'cuatro pisos', 'tres pisos', '3 pisos', '4 pisos', 'departamentos', 'condominio de casas', 'menos de 3000']},
            "c": {"id_tramite": "T_127", "id_revisor": "T_128", "palabras": set(), "frases": [], "todas": [['mas de cinco pisos'], ['mas de 5 pisos'], ['mas de 3000'], ['seis pisos'], ['6 pisos'], ['siete pisos'], ['mas de tres mil']]},
            "d": {"id_tramite": "T_131", "id_revisor": "T_132", "palabras": set(), "frases": [], "todas": [['uso mixto'], ['vivienda y comercio'], ['comercio y vivienda'], ['tienda abajo'], ['negocio en el primer piso'], ['departamentos encima'], ['tienda y vivienda'], ['local y vivienda']]},
            "e": {"id_tramite": "T_133", "id_revisor": "T_134", "palabras": set(), "frases": ['patrimonio', 'monumento historico', 'casona', 'ministerio de cultura', 'historico', 'historica']},
        },
        "frases_no_seguro": ['no se', 'no estoy seguro', 'no tengo idea', 'otra obra', 'es otra obra'],
        "mensaje_no_seguro": ('Si lo que necesitas es ampliar o remodelar, demoler, hacer un cerco o construir un local comercial, industrial o del Estado, cuéntamelo con esas palabras y te llevo al trámite correcto.'),
    },
    "consultar_licencia_ampliacion_remodelacion": {
        "pregunta": ("Claro, te ayudo con la licencia para ampliar o remodelar. ¿Qué vas a hacer?\na) Ampliar mi casa (lo existente más lo nuevo no pasa de 200 m² y la casa ya tiene licencia o declaratoria de fábrica)\nb) Remodelar mi casa sin tocar la estructura, sin agregar área y sin cambiar su uso\nc) Una obra pequeña de ampliación o remodelación (obra menor)\nd) Ampliar o remodelar mi vivienda cambiando la estructura, aumentando el área techada o cambiando el uso\ne) Ampliar, remodelar o demoler en parte un edificio que no es vivienda o es grande (comercial, oficinas, multifamiliar)\nf) Ampliar, remodelar o demoler en parte un local de industria, mercado grande, colegio, clínica, hotel o terminal\nSi quieres que la evalúe un Revisor Urbano, agrega 'con revisor' (por ejemplo: 'd con revisor'). Respóndeme con la letra o cuéntame tu caso."),
        "opciones": {
            "a": {"id_tramite": "T_104", "palabras": set(), "frases": ['ampliar mi casa', 'ampliacion de mi vivienda', 'agrandar mi casa', 'ampliacion de mi casa', 'ampliar mi vivienda', 'cuarto adicional', 'piso mas', 'declaratoria de fabrica', '200 metros', '200 m']},
            "b": {"id_tramite": "T_105", "palabras": set(), "frases": ['sin tocar', 'sin modificar', 'sin ampliar', 'sin cambiar', 'sin aumentar', 'sin aumentar el area', 'sin aumentar area', 'sin estructura', 'por dentro', 'acabados', 'distribucion', 'remodelar mi casa', 'remodelar mi vivienda', 'sin tocar la estructura', 'sin modificar la estructura', 'sin cambiar la estructura', 'sin tocar columnas']},
            "c": {"id_tramite": "T_108", "palabras": set(), "frases": ['obra menor', 'obras menores', 'g040', 'g.040', 'pequena obra', 'pequenas mejoras', 'obra pequena', 'ampliacion pequena', 'remodelacion menor']},
            "d": {"id_tramite": "T_119", "id_revisor": "T_120", "palabras": set(), "frases": ['modificar la estructura', 'tocar la estructura', 'cambiar la estructura', 'cambio estructural', 'modificacion estructural', 'aumentar el area', 'mas area techada', 'cambiar el uso', 'cambio de uso', 'columnas y vigas', 'tocando columnas', 'tocando la estructura', 'modificando la estructura', 'area techada']},
            "e": {"id_tramite": "T_145", "id_revisor": "T_146", "palabras": set(), "frases": ['edificio comercial', 'edificio de oficinas', 'no es vivienda', 'multifamiliar', 'local de varios pisos', 'edificio grande', 'centro comercial']},
            "f": {"id_tramite": "T_157", "id_revisor": "T_158", "palabras": set(), "frases": ['fabrica', 'industria', 'industrial', 'mercado', 'colegio', 'clinica', 'hotel', 'terminal', 'hospital', 'estadio']},
        },
        "frases_no_seguro": _NS,
        "mensaje_no_seguro": ('Si vas a agregar área o tocar la estructura de tu casa, es la opción d. Si solo cambias acabados y distribución sin tocar nada estructural, es la b. Cuéntame más y te oriento.'),
    },
    "consultar_licencia_demolicion": {
        "pregunta": ("Claro, te ayudo con la licencia de demolición. ¿Cuál es tu caso?\na) Demoler TODA una construcción de hasta 3 pisos, sin sótano ni semisótano y sin explosivos\nb) Demoler TODO un edificio de hasta 5 pisos o con sótano o semisótano, sin explosivos\nc) Demoler TODO un edificio de MÁS de 5 pisos o usando explosivos\nd) Demoler solo una parte de la construcción (demolición parcial)\nSi quieres que la evalúe un Revisor Urbano, agrega 'con revisor' (por ejemplo: 'b con revisor'). Respóndeme con la letra o cuéntame tu caso."),
        "opciones": {
            "a": {"id_tramite": "T_107", "palabras": set(), "frases": ['hasta tres pisos', 'hasta 3 pisos', 'dos pisos', 'un piso', 'sin sotano', 'casa vieja', 'no tiene sotano', 'sin semisotano', 'no tiene semisotano', 'tres pisos', '3 pisos', '1 piso', '2 pisos', 'mi casa']},
            "b": {"id_tramite": "T_123", "id_revisor": "T_124", "palabras": set(), "frases": ['cinco pisos', '5 pisos', '4 pisos', 'cuatro pisos', 'con sotano', 'semisotano', 'tiene sotano']},
            "c": {"id_tramite": "T_141", "id_revisor": "T_142", "palabras": set(), "frases": ['con explosivos', 'usar explosivos', 'usando explosivos', 'dinamita', 'implosion', 'mas de cinco pisos', 'mas de 5 pisos', 'seis pisos', '6 pisos']},
            "d": {"id_tramite": "T_121", "id_revisor": "T_122", "palabras": set(), "frases": ['parcial', 'solo una parte', 'una parte', 'solo el segundo piso', 'un sector', 'algunos ambientes', 'unos ambientes', 'solo unos']},
        },
        "frases_no_seguro": _NS,
        "mensaje_no_seguro": ('Si vas a tirar toda una construcción de hasta tres pisos sin sótano, es la opción a. Si es solo una parte, es la d. Cuéntame cuántos pisos tiene y si usarás explosivos.'),
    },
    "consultar_licencia_cerco": {
        "pregunta": ("Claro, te ayudo con la licencia para construir un cerco. ¿Cuál es tu caso?\na) Un cerco de más de 20 metros en mi propio lote o terreno\nb) Un cerco dentro de un condominio o edificio con áreas comunes (propiedad exclusiva y común)\nSi quieres que la evalúe un Revisor Urbano, agrega 'con revisor' (por ejemplo: 'b con revisor'). Respóndeme con la letra o cuéntame tu caso."),
        "opciones": {
            "a": {"id_tramite": "T_106", "palabras": set(), "frases": ['20 metros', 'mas de 20', 'mi lote', 'mi terreno', 'mi casa', 'cerco perimetrico', 'cercar mi terreno', '30 metros', '40 metros']},
            "b": {"id_tramite": "T_117", "id_revisor": "T_118", "palabras": set(), "frases": ['condominio', 'junta de propietarios', 'propiedad comun', 'propiedad exclusiva', 'edificio', 'unidades inmobiliarias', 'unidad inmobiliaria', 'departamentos']},
        },
        "frases_no_seguro": _NS,
        "mensaje_no_seguro": ('Si el cerco es para tu propio lote o terreno, es la opción a. Si es dentro de un condominio o edificio con áreas comunes, es la b.'),
    },
    "consultar_licencia_edificacion_no_vivienda": {
        "pregunta": ("Claro, te ayudo con la licencia para construir un local que no es vivienda. ¿Qué vas a construir?\na) Local comercial, centro de diversión, sala de espectáculos o cultural, hasta 30 000 m²\nb) Local comercial, centro de diversión o sala de espectáculos de MÁS de 30 000 m²\nc) Un mercado de hasta 15 000 m²\nd) Un mercado de MÁS de 15 000 m²\ne) Un estadio o local deportivo de hasta 20 000 personas\nf) Un estadio o local deportivo de MÁS de 20 000 personas\ng) Una fábrica, planta o local de industria\nh) Colegio, clínica, hotel, grifo o terminal de transporte\ni) Otro edificio que no es vivienda (oficinas, banco, iglesia, taller, almacén)\nj) Un tipo de edificación que no encaja en ninguna de las anteriores\nSi quieres que la evalúe un Revisor Urbano, agrega 'con revisor' (por ejemplo: 'c con revisor'). Respóndeme con la letra o cuéntame tu caso."),
        "opciones": {
            "a": {"id_tramite": "T_135", "id_revisor": "T_136", "palabras": set(), "frases": ['local comercial', 'centro de diversion', 'sala de espectaculos', 'cine', 'teatro', 'centro cultural', 'galeria', 'biblioteca', 'tienda grande', 'discoteca']},
            "b": {"id_tramite": "T_149", "id_revisor": "T_150", "palabras": set(), "frases": [], "todas": [['mas de 30000'], ['mas de 30 000'], ['mas de treinta mil'], ['mas de 30 mil'], ['mall']]},
            "c": {"id_tramite": "T_137", "id_revisor": "T_138", "palabras": set(), "frases": ['mercado', 'puestos de venta', 'mercadito', 'mercado de abastos']},
            "d": {"id_tramite": "T_151", "id_revisor": "T_152", "palabras": set(), "frases": [], "todas": [['mercado', 'mas de 15000'], ['mercado', 'mas de 15 000'], ['mercado', 'mas de quince mil'], ['mercado', 'mas de 15 mil'], ['mercado', 'grande'], ['mercado', 'enorme']]},
            "e": {"id_tramite": "T_139", "id_revisor": "T_140", "palabras": set(), "frases": ['estadio', 'coliseo', 'losa deportiva', 'complejo deportivo', 'local deportivo', 'polideportivo']},
            "f": {"id_tramite": "T_153", "id_revisor": "T_154", "palabras": set(), "frases": [], "todas": [['estadio', 'mas de 20000'], ['estadio', 'mas de 20 000'], ['estadio', 'mas de veinte mil'], ['estadio', 'mas de 20 mil'], ['estadio', 'grande'], ['estadio', 'enorme'], ['coliseo', 'mas de 20000'], ['coliseo', 'mas de 20 000'], ['coliseo', 'mas de veinte mil'], ['coliseo', 'mas de 20 mil'], ['coliseo', 'grande'], ['coliseo', 'enorme'], ['deportivo', 'mas de 20000'], ['deportivo', 'mas de 20 000'], ['deportivo', 'mas de veinte mil'], ['deportivo', 'mas de 20 mil'], ['deportivo', 'grande'], ['deportivo', 'enorme']]},
            "g": {"id_tramite": "T_147", "id_revisor": "T_148", "palabras": set(), "frases": ['fabrica', 'industria', 'industrial', 'planta', 'almacen industrial', 'taller industrial', 'parque industrial']},
            "h": {"id_tramite": "T_155", "id_revisor": "T_156", "palabras": set(), "frases": ['colegio', 'clinica', 'hotel', 'hospedaje', 'grifo', 'terminal terrestre', 'terminal de buses', 'estacion de servicio', 'universidad privada', 'instituto', 'hospital', 'terminal']},
            "i": {"id_tramite": "T_129", "id_revisor": "T_130", "palabras": set(), "frases": ['oficinas', 'oficina', 'banco', 'iglesia', 'templo', 'almacen', 'deposito', 'taller', 'no es vivienda', 'que no sea vivienda']},
            "j": {"id_tramite": "T_143", "id_revisor": "T_144", "palabras": set(), "frases": ['no encaja', 'ninguno de los anteriores', 'ninguna de las anteriores', 'demas edificaciones', 'no esta en las anteriores', 'especial']},
        },
        "frases_no_seguro": _NS,
        "mensaje_no_seguro": ('Cuéntame para qué va a servir el local (comercio, mercado, estadio, fábrica, colegio, clínica, hotel, oficinas...) y su tamaño aproximado, y te oriento.'),
    },
    "consultar_licencia_edificacion_estado": {
        "pregunta": ('Claro, te ayudo con la licencia para una obra del Estado. ¿Qué se va a construir?\na) Viviendas de un programa del Sector Vivienda (Bono Familiar Habitacional)\nb) Una obra de inversión pública, asociación público-privada o concesión para servicios o infraestructura pública\nc) Un cuartel, comisaría o penal (Fuerzas Armadas, Policía o establecimiento penitenciario)\nd) Una obra de una universidad nacional\ne) Un establecimiento de salud estatal (posta, centro de salud, hospital)\nf) Un colegio o institución educativa estatal\nRespóndeme con la letra o cuéntame qué obra es.'),
        "opciones": {
            "a": {"id_tramite": "T_109", "palabras": set(), "frases": ['bono familiar', 'bfh', 'bono habitacional', 'beneficiarios']},
            "b": {"id_tramite": "T_110", "palabras": set(), "frases": ['inversion publica', 'asociacion publico', 'concesion', 'infraestructura publica', 'servicios publicos', 'servicio publico']},
            "c": {"id_tramite": "T_111", "palabras": set(), "frases": ['cuartel', 'militar', 'policia', 'comisaria', 'penal', 'reclusion', 'fuerzas armadas', 'carcel', 'ejercito']},
            "d": {"id_tramite": "T_112", "palabras": set(), "frases": ['universidad nacional', 'universidad', 'pabellon']},
            "e": {"id_tramite": "T_113", "palabras": set(), "frases": ['posta', 'centro de salud', 'hospital', 'establecimiento de salud', 'essalud', 'minsa', 'salud estatal']},
            "f": {"id_tramite": "T_114", "palabras": set(), "frases": ['colegio', 'institucion educativa', 'escuela', 'aulas', 'ie estatal', 'colegio publico']},
        },
        "frases_no_seguro": _NS,
        "mensaje_no_seguro": ('Cuéntame qué se va a construir (vivienda del bono familiar, obra pública por concesión, cuartel o comisaría, universidad nacional, posta u hospital estatal, colegio estatal) y te oriento.'),
    },
    "consultar_modificacion_proyecto_edificacion": {
        "pregunta": ("Claro, te ayudo con la modificación de tu proyecto de edificación. Tu licencia o resolución indica la modalidad (A, B, C o D). Cuéntame:\nANTES de que me den la licencia:\na) Antes de que me den la licencia - modalidad B\nb) Antes de que me den la licencia - modalidad C\nc) Antes de que me den la licencia - modalidad D\nDESPUÉS de emitida la licencia, un cambio PEQUEÑO (no sustancial):\nd) Cambio pequeño después de la licencia - modalidad A\ne) Cambio pequeño después de la licencia - modalidad B\nf) Cambio pequeño después de la licencia - modalidad C\ng) Cambio pequeño después de la licencia - modalidad D\nDESPUÉS de emitida la licencia, un cambio GRANDE (sustancial):\nh) Cambio grande después de la licencia - modalidad A\ni) Cambio grande después de la licencia - modalidad B\nj) Cambio grande después de la licencia - modalidad C\nk) Cambio grande después de la licencia - modalidad D\nSi quieres que la evalúe un Revisor Urbano (modalidades B, C y D), agrega 'con revisor' (por ejemplo: 'f con revisor'). Respóndeme con la letra o cuéntame tu caso."),
        "opciones": {
            "a": {"id_tramite": "T_190", "palabras": set(), "frases": [], "todas": [['antes', 'modalidad b'], ['aun no', 'modalidad b'], ['todavia no', 'modalidad b']]},
            "b": {"id_tramite": "T_191", "palabras": set(), "frases": [], "todas": [['antes', 'modalidad c'], ['aun no', 'modalidad c'], ['todavia no', 'modalidad c']]},
            "c": {"id_tramite": "T_192", "palabras": set(), "frases": [], "todas": [['antes', 'modalidad d'], ['aun no', 'modalidad d'], ['todavia no', 'modalidad d']]},
            "d": {"id_tramite": "T_193", "palabras": set(), "frases": [], "todas": [['no sustancial', 'modalidad a'], ['pequeno', 'modalidad a'], ['menor', 'modalidad a'], ['poco', 'modalidad a'], ['ligero', 'modalidad a'], ['leve', 'modalidad a']]},
            "e": {"id_tramite": "T_194", "id_revisor": "T_195", "palabras": set(), "frases": [], "todas": [['no sustancial', 'modalidad b'], ['pequeno', 'modalidad b'], ['menor', 'modalidad b'], ['poco', 'modalidad b'], ['ligero', 'modalidad b'], ['leve', 'modalidad b']]},
            "f": {"id_tramite": "T_196", "id_revisor": "T_197", "palabras": set(), "frases": [], "todas": [['no sustancial', 'modalidad c'], ['pequeno', 'modalidad c'], ['menor', 'modalidad c'], ['poco', 'modalidad c'], ['ligero', 'modalidad c'], ['leve', 'modalidad c']]},
            "g": {"id_tramite": "T_198", "id_revisor": "T_199", "palabras": set(), "frases": [], "todas": [['no sustancial', 'modalidad d'], ['pequeno', 'modalidad d'], ['menor', 'modalidad d'], ['poco', 'modalidad d'], ['ligero', 'modalidad d'], ['leve', 'modalidad d']]},
            "h": {"id_tramite": "T_200", "palabras": set(), "frases": [], "todas": [['sustancial', 'modalidad a'], ['grande', 'modalidad a'], ['importante', 'modalidad a'], ['fuerte', 'modalidad a'], ['grave', 'modalidad a']]},
            "i": {"id_tramite": "T_201", "id_revisor": "T_202", "palabras": set(), "frases": [], "todas": [['sustancial', 'modalidad b'], ['grande', 'modalidad b'], ['importante', 'modalidad b'], ['fuerte', 'modalidad b'], ['grave', 'modalidad b']]},
            "j": {"id_tramite": "T_203", "id_revisor": "T_204", "palabras": set(), "frases": [], "todas": [['sustancial', 'modalidad c'], ['grande', 'modalidad c'], ['importante', 'modalidad c'], ['fuerte', 'modalidad c'], ['grave', 'modalidad c']]},
            "k": {"id_tramite": "T_205", "id_revisor": "T_206", "palabras": set(), "frases": [], "todas": [['sustancial', 'modalidad d'], ['grande', 'modalidad d'], ['importante', 'modalidad d'], ['fuerte', 'modalidad d'], ['grave', 'modalidad d']]},
        },
        "frases_no_seguro": _NS,
        "mensaje_no_seguro": ('Revisa tu licencia o resolución: ahí figura la modalidad (A, B, C o D). Con eso y sabiendo si ya te dieron la licencia y si el cambio es pequeño o grande, te oriento.'),
    },
    "consultar_anteproyecto_consulta": {
        "pregunta": ('Claro, te ayudo con el anteproyecto en consulta (revisión previa de tus planos de arquitectura antes de pedir la licencia). Según el tamaño de tu obra:\na) Modalidad B (por ejemplo vivienda o condominio de hasta 5 pisos)\nb) Modalidad C (por ejemplo edificio multifamiliar grande o local comercial)\nc) Modalidad D (por ejemplo industria, mercado grande, hospital u hotel)\nRespóndeme con la letra o cuéntame tu obra.'),
        "opciones": {
            "a": {"id_tramite": "T_207", "palabras": set(), "frases": ['modalidad b', 'hasta cinco pisos', 'hasta 5 pisos', 'vivienda de hasta']},
            "b": {"id_tramite": "T_208", "palabras": set(), "frases": ['modalidad c', 'multifamiliar', 'comercial', 'edificio grande', 'mas de cinco pisos']},
            "c": {"id_tramite": "T_209", "palabras": set(), "frases": ['modalidad d', 'industria', 'industrial', 'mercado', 'estadio', 'hospital', 'hotel', 'grifo', 'fabrica']},
        },
        "frases_no_seguro": _NS,
        "mensaje_no_seguro": ('La modalidad depende del tamaño y uso de tu obra: B (vivienda hasta 5 pisos), C (multifamiliar o comercial grande) y D (industria, mercado, hospital, hotel). Cuéntame qué vas a construir.'),
    },
    "consultar_conformidad_obra": {
        "pregunta": ('Claro, te ayudo con la conformidad de obra (declaratoria de edificación) de tu construcción TERMINADA. Cuéntame cómo quedó respecto a los planos aprobados y qué modalidad tenía tu licencia (A, B, C o D):\na) Terminé mi obra modalidad A y quedó igual a los planos aprobados\nb) Terminé mi obra modalidad B, C o D y quedó igual a los planos aprobados\nQuedó CON cambios respecto a los planos:\nc) Terminé mi obra modalidad A pero con cambios respecto a los planos\nd) Terminé mi obra modalidad B pero con cambios respecto a los planos\ne) Terminé mi obra modalidad C pero con cambios respecto a los planos\nf) Terminé mi obra modalidad D pero con cambios respecto a los planos\ng) Solo quiero la Declaración Municipal de Edificación Terminada (modalidades B, C y D)\nRespóndeme con la letra o cuéntame tu caso.'),
        "opciones": {
            "a": {"id_tramite": "T_218", "palabras": set(), "frases": [], "todas": [['sin cambios', 'modalidad a'], ['sin variaciones', 'modalidad a'], ['igual al plano', 'modalidad a'], ['tal cual el plano', 'modalidad a'], ['sin modificaciones', 'modalidad a'], ['sin cambiar nada', 'modalidad a'], ['igualito al plano', 'modalidad a'], ['igual al proyecto', 'modalidad a'], ['tal cual el proyecto', 'modalidad a'], ['igualito al proyecto', 'modalidad a']]},
            "b": {"id_tramite": "T_219", "palabras": set(), "frases": [], "todas": [['sin cambios', 'modalidad b'], ['sin cambios', 'modalidad c'], ['sin cambios', 'modalidad d'], ['sin variaciones', 'modalidad b'], ['sin variaciones', 'modalidad c'], ['sin variaciones', 'modalidad d'], ['igual al plano', 'modalidad b'], ['igual al plano', 'modalidad c'], ['igual al plano', 'modalidad d'], ['tal cual el plano', 'modalidad b'], ['tal cual el plano', 'modalidad c'], ['tal cual el plano', 'modalidad d'], ['sin modificaciones', 'modalidad b'], ['sin modificaciones', 'modalidad c'], ['sin modificaciones', 'modalidad d'], ['sin cambiar nada', 'modalidad b'], ['sin cambiar nada', 'modalidad c'], ['sin cambiar nada', 'modalidad d'], ['igualito al plano', 'modalidad b'], ['igualito al plano', 'modalidad c'], ['igualito al plano', 'modalidad d'], ['igual al proyecto', 'modalidad b'], ['igual al proyecto', 'modalidad c'], ['igual al proyecto', 'modalidad d'], ['tal cual el proyecto', 'modalidad b'], ['tal cual el proyecto', 'modalidad c'], ['tal cual el proyecto', 'modalidad d'], ['igualito al proyecto', 'modalidad b'], ['igualito al proyecto', 'modalidad c'], ['igualito al proyecto', 'modalidad d']]},
            "c": {"id_tramite": "T_220", "palabras": set(), "frases": [], "todas": [['con cambios', 'modalidad a'], ['con variaciones', 'modalidad a'], ['con modificaciones', 'modalidad a'], ['cambie', 'modalidad a'], ['modifique', 'modalidad a'], ['distinto al plano', 'modalidad a'], ['distinto al proyecto', 'modalidad a'], ['diferente al proyecto', 'modalidad a'], ['varie', 'modalidad a'], ['con diferencias', 'modalidad a']]},
            "d": {"id_tramite": "T_221", "palabras": set(), "frases": [], "todas": [['con cambios', 'modalidad b'], ['con variaciones', 'modalidad b'], ['con modificaciones', 'modalidad b'], ['cambie', 'modalidad b'], ['modifique', 'modalidad b'], ['distinto al plano', 'modalidad b'], ['distinto al proyecto', 'modalidad b'], ['diferente al proyecto', 'modalidad b'], ['varie', 'modalidad b'], ['con diferencias', 'modalidad b']]},
            "e": {"id_tramite": "T_222", "palabras": set(), "frases": [], "todas": [['con cambios', 'modalidad c'], ['con variaciones', 'modalidad c'], ['con modificaciones', 'modalidad c'], ['cambie', 'modalidad c'], ['modifique', 'modalidad c'], ['distinto al plano', 'modalidad c'], ['distinto al proyecto', 'modalidad c'], ['diferente al proyecto', 'modalidad c'], ['varie', 'modalidad c'], ['con diferencias', 'modalidad c']]},
            "f": {"id_tramite": "T_223", "palabras": set(), "frases": [], "todas": [['con cambios', 'modalidad d'], ['con variaciones', 'modalidad d'], ['con modificaciones', 'modalidad d'], ['cambie', 'modalidad d'], ['modifique', 'modalidad d'], ['distinto al plano', 'modalidad d'], ['distinto al proyecto', 'modalidad d'], ['diferente al proyecto', 'modalidad d'], ['varie', 'modalidad d'], ['con diferencias', 'modalidad d']]},
            "g": {"id_tramite": "T_217", "palabras": set(), "frases": ['declaracion municipal', 'declaracion de edificacion terminada', 'edificacion terminada']},
        },
        "frases_no_seguro": _NS,
        "mensaje_no_seguro": ('Revisa tu licencia de edificación: ahí figura la modalidad (A, B, C o D). Con eso y sabiendo si la obra quedó igual al plano o con cambios, te oriento.'),
    },
    "consultar_conformidad_obra_anticipada": {
        "pregunta": ('Claro, te ayudo con la conformidad de obra ANTICIPADA (cuando solo has construido hasta el casco no habitable, es decir la estructura y muros, sin acabados). Cuéntame cómo quedó respecto a los planos y qué modalidad tenía tu licencia:\na) Casco no habitable, modalidad B (vivienda), igual a los planos\nb) Casco no habitable, modalidad C (oficinas y comercio), igual a los planos\nc) Casco no habitable, modalidad D (comercio), igual a los planos\nQuedó CON cambios respecto a los planos:\nd) Casco no habitable, modalidad B (vivienda), con cambios\ne) Casco no habitable, modalidad C (oficinas y comercio), con cambios\nf) Casco no habitable, modalidad D (comercio), con cambios\nRespóndeme con la letra o cuéntame tu caso.'),
        "opciones": {
            "a": {"id_tramite": "T_211", "palabras": set(), "frases": [], "todas": [['sin cambios', 'modalidad b'], ['sin variaciones', 'modalidad b'], ['igual al plano', 'modalidad b'], ['tal cual el plano', 'modalidad b'], ['sin modificaciones', 'modalidad b'], ['sin cambiar nada', 'modalidad b'], ['igualito al plano', 'modalidad b'], ['igual al proyecto', 'modalidad b'], ['tal cual el proyecto', 'modalidad b'], ['igualito al proyecto', 'modalidad b']]},
            "b": {"id_tramite": "T_212", "palabras": set(), "frases": [], "todas": [['sin cambios', 'modalidad c'], ['sin variaciones', 'modalidad c'], ['igual al plano', 'modalidad c'], ['tal cual el plano', 'modalidad c'], ['sin modificaciones', 'modalidad c'], ['sin cambiar nada', 'modalidad c'], ['igualito al plano', 'modalidad c'], ['igual al proyecto', 'modalidad c'], ['tal cual el proyecto', 'modalidad c'], ['igualito al proyecto', 'modalidad c']]},
            "c": {"id_tramite": "T_213", "palabras": set(), "frases": [], "todas": [['sin cambios', 'modalidad d'], ['sin variaciones', 'modalidad d'], ['igual al plano', 'modalidad d'], ['tal cual el plano', 'modalidad d'], ['sin modificaciones', 'modalidad d'], ['sin cambiar nada', 'modalidad d'], ['igualito al plano', 'modalidad d'], ['igual al proyecto', 'modalidad d'], ['tal cual el proyecto', 'modalidad d'], ['igualito al proyecto', 'modalidad d']]},
            "d": {"id_tramite": "T_214", "palabras": set(), "frases": [], "todas": [['con cambios', 'modalidad b'], ['con variaciones', 'modalidad b'], ['con modificaciones', 'modalidad b'], ['cambie', 'modalidad b'], ['modifique', 'modalidad b'], ['distinto al plano', 'modalidad b'], ['distinto al proyecto', 'modalidad b'], ['diferente al proyecto', 'modalidad b'], ['varie', 'modalidad b'], ['con diferencias', 'modalidad b']]},
            "e": {"id_tramite": "T_215", "palabras": set(), "frases": [], "todas": [['con cambios', 'modalidad c'], ['con variaciones', 'modalidad c'], ['con modificaciones', 'modalidad c'], ['cambie', 'modalidad c'], ['modifique', 'modalidad c'], ['distinto al plano', 'modalidad c'], ['distinto al proyecto', 'modalidad c'], ['diferente al proyecto', 'modalidad c'], ['varie', 'modalidad c'], ['con diferencias', 'modalidad c']]},
            "f": {"id_tramite": "T_216", "palabras": set(), "frases": [], "todas": [['con cambios', 'modalidad d'], ['con variaciones', 'modalidad d'], ['con modificaciones', 'modalidad d'], ['cambie', 'modalidad d'], ['modifique', 'modalidad d'], ['distinto al plano', 'modalidad d'], ['distinto al proyecto', 'modalidad d'], ['diferente al proyecto', 'modalidad d'], ['varie', 'modalidad d'], ['con diferencias', 'modalidad d']]},
        },
        "frases_no_seguro": _NS,
        "mensaje_no_seguro": ('Esto aplica cuando la obra está solo a nivel de casco no habitable (modalidades B, C o D). Revisa tu licencia para ver la modalidad y dime si quedó igual a los planos o con cambios.'),
    },
    "consultar_proyecto_integral_edificacion": {
        "pregunta": ("Claro, te ayudo con el proyecto integral de edificacion (para construir un edificio por etapas). ¿Cuál es tu caso?\na) Aprobar solo el proyecto integral - modalidad C\nb) Aprobar solo el proyecto integral - modalidad D\nc) Aprobar el proyecto integral Y a la vez la licencia de una etapa - modalidad C\nd) Aprobar el proyecto integral Y a la vez la licencia de una etapa - modalidad D\ne) Ya tengo el proyecto integral aprobado y quiero la licencia de una etapa\nf) Modificar el proyecto de una etapa de un proyecto integral ya aprobado (o con plazo vencido) - modalidad B\nSi quieres que la evalúe un Revisor Urbano, agrega 'con revisor' (por ejemplo: 'b con revisor'). Respóndeme con la letra o cuéntame tu caso."),
        "opciones": {
            "a": {"id_tramite": "T_225", "palabras": set(), "frases": [], "todas": [['modalidad c']]},
            "b": {"id_tramite": "T_226", "palabras": set(), "frases": [], "todas": [['modalidad d']]},
            "c": {"id_tramite": "T_227", "palabras": set(), "frases": [], "todas": [['con licencia', 'modalidad c'], ['y licencia', 'modalidad c'], ['con la licencia', 'modalidad c'], ['y la licencia', 'modalidad c'], ['junto con la licencia', 'modalidad c'], ['mas la licencia', 'modalidad c'], ['al mismo tiempo', 'modalidad c'], ['en conjunto', 'modalidad c'], ['junto', 'modalidad c']]},
            "d": {"id_tramite": "T_228", "palabras": set(), "frases": [], "todas": [['con licencia', 'modalidad d'], ['y licencia', 'modalidad d'], ['con la licencia', 'modalidad d'], ['y la licencia', 'modalidad d'], ['junto con la licencia', 'modalidad d'], ['mas la licencia', 'modalidad d'], ['al mismo tiempo', 'modalidad d'], ['en conjunto', 'modalidad d'], ['junto', 'modalidad d']]},
            "e": {"id_tramite": "T_229", "palabras": set(), "frases": [], "todas": [['ya aprobado'], ['ya tengo el proyecto'], ['ya me aprobaron'], ['ya tengo el dictamen'], ['ya esta aprobado'], ['aprobado con anterioridad'], ['ya tengo mi proyecto'], ['ya fue aprobado']]},
            "f": {"id_tramite": "T_125", "id_revisor": "T_126", "palabras": set(), "frases": [], "todas": [['modificar', 'proyecto integral'], ['modificacion', 'proyecto integral'], ['modificar', 'etapa'], ['cambiar', 'proyecto integral'], ['modificar mi proyecto']]},
        },
        "frases_no_seguro": _NS,
        "mensaje_no_seguro": ('Revisa en tu expediente la modalidad (C o D) y dime si ya tienes el proyecto integral aprobado o lo vas a tramitar junto con la licencia de una etapa.'),
    },
    "consultar_proyecto_integral_habilitacion": {
        "pregunta": ('Claro, te ayudo con el proyecto integral de habilitacion urbana (para habilitar un terreno por etapas). ¿Cuál es tu caso?\na) Aprobar solo el proyecto integral - modalidad C\nb) Aprobar solo el proyecto integral - modalidad D\nc) Aprobar el proyecto integral Y a la vez la licencia de una etapa - modalidad C\nd) Aprobar el proyecto integral Y a la vez la licencia de una etapa - modalidad D\ne) Ya tengo el proyecto integral aprobado y quiero la licencia de una etapa\nRespóndeme con la letra o cuéntame tu caso.'),
        "opciones": {
            "a": {"id_tramite": "T_183", "palabras": set(), "frases": [], "todas": [['modalidad c']]},
            "b": {"id_tramite": "T_184", "palabras": set(), "frases": [], "todas": [['modalidad d']]},
            "c": {"id_tramite": "T_185", "palabras": set(), "frases": [], "todas": [['con licencia', 'modalidad c'], ['y licencia', 'modalidad c'], ['con la licencia', 'modalidad c'], ['y la licencia', 'modalidad c'], ['junto con la licencia', 'modalidad c'], ['mas la licencia', 'modalidad c'], ['al mismo tiempo', 'modalidad c'], ['en conjunto', 'modalidad c'], ['junto', 'modalidad c']]},
            "d": {"id_tramite": "T_186", "palabras": set(), "frases": [], "todas": [['con licencia', 'modalidad d'], ['y licencia', 'modalidad d'], ['con la licencia', 'modalidad d'], ['y la licencia', 'modalidad d'], ['junto con la licencia', 'modalidad d'], ['mas la licencia', 'modalidad d'], ['al mismo tiempo', 'modalidad d'], ['en conjunto', 'modalidad d'], ['junto', 'modalidad d']]},
            "e": {"id_tramite": "T_187", "palabras": set(), "frases": [], "todas": [['ya aprobado'], ['ya tengo el proyecto'], ['ya me aprobaron'], ['ya tengo el dictamen'], ['ya esta aprobado'], ['aprobado con anterioridad'], ['ya tengo mi proyecto'], ['ya fue aprobado']]},
        },
        "frases_no_seguro": _NS,
        "mensaje_no_seguro": ('Revisa en tu expediente la modalidad (C o D) y dime si ya tienes el proyecto integral aprobado o lo vas a tramitar junto con la licencia de una etapa.'),
    },
    "consultar_prorroga_revalidacion_licencia": {
        "pregunta": ('Claro, te ayudo con tu licencia de obra. ¿Qué necesitas?\na) Prorrogar mi licencia de EDIFICACIÓN (construcción) que todavía está vigente\nb) Revalidar mi licencia de EDIFICACIÓN (construcción) que ya se venció (debo tener avance de obra)\nc) Prorrogar mi licencia de HABILITACIÓN URBANA que todavía está vigente\nd) Revalidar mi licencia de HABILITACIÓN URBANA que ya se venció (debo tener avance de obra)\nRespóndeme con la letra o cuéntame tu caso.'),
        "opciones": {
            "a": {"id_tramite": "T_230", "palabras": set(), "frases": [], "todas": [['prorroga', 'edificacion'], ['prorroga', 'construccion'], ['prorroga', 'obra'], ['prorroga', 'casa'], ['prorroga', 'construir'], ['prorroga', 'edificio'], ['prorrogar', 'edificacion'], ['prorrogar', 'construccion'], ['prorrogar', 'obra'], ['prorrogar', 'casa'], ['prorrogar', 'construir'], ['prorrogar', 'edificio'], ['prorrogarla', 'edificacion'], ['prorrogarla', 'construccion'], ['prorrogarla', 'obra'], ['prorrogarla', 'casa'], ['prorrogarla', 'construir'], ['prorrogarla', 'edificio'], ['ampliar el plazo', 'edificacion'], ['ampliar el plazo', 'construccion'], ['ampliar el plazo', 'obra'], ['ampliar el plazo', 'casa'], ['ampliar el plazo', 'construir'], ['ampliar el plazo', 'edificio'], ['mas tiempo', 'edificacion'], ['mas tiempo', 'construccion'], ['mas tiempo', 'obra'], ['mas tiempo', 'casa'], ['mas tiempo', 'construir'], ['mas tiempo', 'edificio'], ['extender', 'edificacion'], ['extender', 'construccion'], ['extender', 'obra'], ['extender', 'casa'], ['extender', 'construir'], ['extender', 'edificio'], ['ampliacion de plazo', 'edificacion'], ['ampliacion de plazo', 'construccion'], ['ampliacion de plazo', 'obra'], ['ampliacion de plazo', 'casa'], ['ampliacion de plazo', 'construir'], ['ampliacion de plazo', 'edificio']]},
            "b": {"id_tramite": "T_231", "palabras": set(), "frases": [], "todas": [['revalida', 'edificacion'], ['revalida', 'construccion'], ['revalida', 'obra'], ['revalida', 'casa'], ['revalida', 'construir'], ['revalida', 'edificio'], ['revalidar', 'edificacion'], ['revalidar', 'construccion'], ['revalidar', 'obra'], ['revalidar', 'casa'], ['revalidar', 'construir'], ['revalidar', 'edificio'], ['revalidacion', 'edificacion'], ['revalidacion', 'construccion'], ['revalidacion', 'obra'], ['revalidacion', 'casa'], ['revalidacion', 'construir'], ['revalidacion', 'edificio'], ['ya vencio', 'edificacion'], ['ya vencio', 'construccion'], ['ya vencio', 'obra'], ['ya vencio', 'casa'], ['ya vencio', 'construir'], ['ya vencio', 'edificio'], ['se vencio', 'edificacion'], ['se vencio', 'construccion'], ['se vencio', 'obra'], ['se vencio', 'casa'], ['se vencio', 'construir'], ['se vencio', 'edificio'], ['caduco', 'edificacion'], ['caduco', 'construccion'], ['caduco', 'obra'], ['caduco', 'casa'], ['caduco', 'construir'], ['caduco', 'edificio'], ['ya caduco', 'edificacion'], ['ya caduco', 'construccion'], ['ya caduco', 'obra'], ['ya caduco', 'casa'], ['ya caduco', 'construir'], ['ya caduco', 'edificio'], ['vencida', 'edificacion'], ['vencida', 'construccion'], ['vencida', 'obra'], ['vencida', 'casa'], ['vencida', 'construir'], ['vencida', 'edificio']]},
            "c": {"id_tramite": "T_188", "palabras": set(), "frases": [], "todas": [['prorroga', 'habilitacion'], ['prorroga', 'lotizacion'], ['prorroga', 'urbanizacion'], ['prorroga', 'terreno'], ['prorrogar', 'habilitacion'], ['prorrogar', 'lotizacion'], ['prorrogar', 'urbanizacion'], ['prorrogar', 'terreno'], ['prorrogarla', 'habilitacion'], ['prorrogarla', 'lotizacion'], ['prorrogarla', 'urbanizacion'], ['prorrogarla', 'terreno'], ['ampliar el plazo', 'habilitacion'], ['ampliar el plazo', 'lotizacion'], ['ampliar el plazo', 'urbanizacion'], ['ampliar el plazo', 'terreno'], ['mas tiempo', 'habilitacion'], ['mas tiempo', 'lotizacion'], ['mas tiempo', 'urbanizacion'], ['mas tiempo', 'terreno'], ['extender', 'habilitacion'], ['extender', 'lotizacion'], ['extender', 'urbanizacion'], ['extender', 'terreno'], ['ampliacion de plazo', 'habilitacion'], ['ampliacion de plazo', 'lotizacion'], ['ampliacion de plazo', 'urbanizacion'], ['ampliacion de plazo', 'terreno']]},
            "d": {"id_tramite": "T_189", "palabras": set(), "frases": [], "todas": [['revalida', 'habilitacion'], ['revalida', 'lotizacion'], ['revalida', 'urbanizacion'], ['revalida', 'terreno'], ['revalidar', 'habilitacion'], ['revalidar', 'lotizacion'], ['revalidar', 'urbanizacion'], ['revalidar', 'terreno'], ['revalidacion', 'habilitacion'], ['revalidacion', 'lotizacion'], ['revalidacion', 'urbanizacion'], ['revalidacion', 'terreno'], ['ya vencio', 'habilitacion'], ['ya vencio', 'lotizacion'], ['ya vencio', 'urbanizacion'], ['ya vencio', 'terreno'], ['se vencio', 'habilitacion'], ['se vencio', 'lotizacion'], ['se vencio', 'urbanizacion'], ['se vencio', 'terreno'], ['caduco', 'habilitacion'], ['caduco', 'lotizacion'], ['caduco', 'urbanizacion'], ['caduco', 'terreno'], ['ya caduco', 'habilitacion'], ['ya caduco', 'lotizacion'], ['ya caduco', 'urbanizacion'], ['ya caduco', 'terreno'], ['vencida', 'habilitacion'], ['vencida', 'lotizacion'], ['vencida', 'urbanizacion'], ['vencida', 'terreno']]},
        },
        "frases_no_seguro": _NS,
        "mensaje_no_seguro": ('Dime si tu licencia es de construcción (edificación) o de habilitación urbana, y si todavía está vigente (prórroga) o ya se venció (revalidación).'),
    },
    "consultar_modificacion_habilitacion_urbana": {
        "pregunta": ("Claro, te ayudo a hacer una modificación NO sustancial al proyecto de habilitación urbana que te aprobaron, antes de ejecutarlo. Tu licencia indica la modalidad (A, B, C o D):\na) Modalidad A (aprobación automática)\nb) Modalidad B\nc) Modalidad C\nd) Modalidad D\nSi quieres que la evalúe un Revisor Urbano (modalidades B, C y D), agrega 'con revisor' (por ejemplo: 'c con revisor'). Respóndeme con la letra o cuéntame tu caso."),
        "opciones": {
            "a": {"id_tramite": "T_159", "palabras": set(), "frases": ['modalidad a', 'aprobacion automatica', 'automatica', 'firma de profesionales']},
            "b": {"id_tramite": "T_160", "id_revisor": "T_161", "palabras": set(), "frases": ['modalidad b']},
            "c": {"id_tramite": "T_162", "id_revisor": "T_163", "palabras": set(), "frases": ['modalidad c']},
            "d": {"id_tramite": "T_164", "id_revisor": "T_165", "palabras": set(), "frases": ['modalidad d']},
        },
        "frases_no_seguro": _NS,
        "mensaje_no_seguro": ('Revisa tu licencia o resolución de habilitación urbana: ahí figura la modalidad (A, B, C o D). Con eso te indico el trámite.'),
    },
    "consultar_independizacion_terreno_rustico": {
        "pregunta": ('Claro, te ayudo con la independización o parcelación de un terreno rústico (parcelas de más de 1 hectárea cada una). ¿Cuál es tu caso?\na) Solo dividir un terreno rústico que está dentro de la zona urbana\nb) Solo dividir un terreno rústico en zona de expansión urbana (urbanizable inmediata) con planeamiento integral aprobado\nc) Dividirlo y habilitarlo a la vez - modalidad B\nd) Dividirlo y habilitarlo a la vez - modalidad C\ne) Dividirlo y habilitarlo a la vez - modalidad D\nf) Dividirlo y habilitarlo a la vez, en un terreno que no colinda con zona urbana o con proyectos aprobados no ejecutados (modalidad D con planeamiento integral)\nSi quieres dividir y habilitar a la vez, tu proyecto tiene una modalidad (B, C o D). Respóndeme con la letra o cuéntame tu caso.'),
        "opciones": {
            "a": {"id_tramite": "T_166", "palabras": set(), "frases": ['solo dividir', 'solo independizar', 'solamente dividir', 'solo parcelar', 'sin habilitar', 'nada mas']},
            "b": {"id_tramite": "T_167", "palabras": set(), "frases": ['urbanizable', 'expansion urbana', 'zona de expansion', 'area de expansion']},
            "c": {"id_tramite": "T_168", "palabras": set(), "frases": [], "todas": [['modalidad b']]},
            "d": {"id_tramite": "T_169", "palabras": set(), "frases": [], "todas": [['modalidad c']]},
            "e": {"id_tramite": "T_170", "palabras": set(), "frases": [], "todas": [['modalidad d']]},
            "f": {"id_tramite": "T_171", "palabras": set(), "frases": [], "todas": [['no colind'], ['aislado'], ['lejos de la ciudad'], ['no ejecutado'], ['modalidad d', 'no colind'], ['modalidad d', 'aislado']]},
        },
        "frases_no_seguro": _NS,
        "mensaje_no_seguro": ('Cuéntame si solo quieres dividir el terreno rústico o también habilitarlo, y si está dentro de la zona urbana, en zona de expansión, o aislado. Con eso te oriento.'),
    },
    "consultar_recepcion_obras_habilitacion": {
        "pregunta": ('Claro, te ayudo con la recepción de obras de tu habilitación urbana (cuando ya terminaste de ejecutar las obras). Dime si quedó igual al proyecto aprobado o con cambios, y la modalidad de tu licencia (A, B, C o D):\na) Igual al proyecto, modalidad A\nb) Igual al proyecto, modalidad B\nc) Igual al proyecto, modalidad C\nd) Igual al proyecto, modalidad D\nQuedó CON cambios no sustanciales respecto al proyecto:\ne) Con cambios, modalidad A\nf) Con cambios, modalidad B\ng) Con cambios, modalidad C\nh) Con cambios, modalidad D\ni) Recepción parcial: solo de una etapa ya terminada\nRespóndeme con la letra o cuéntame tu caso.'),
        "opciones": {
            "a": {"id_tramite": "T_172", "palabras": set(), "frases": [], "todas": [['sin cambios', 'modalidad a'], ['sin variaciones', 'modalidad a'], ['igual al plano', 'modalidad a'], ['tal cual el plano', 'modalidad a'], ['sin modificaciones', 'modalidad a'], ['sin cambiar nada', 'modalidad a'], ['igualito al plano', 'modalidad a'], ['igual al proyecto', 'modalidad a'], ['tal cual el proyecto', 'modalidad a'], ['igualito al proyecto', 'modalidad a']]},
            "b": {"id_tramite": "T_173", "palabras": set(), "frases": [], "todas": [['sin cambios', 'modalidad b'], ['sin variaciones', 'modalidad b'], ['igual al plano', 'modalidad b'], ['tal cual el plano', 'modalidad b'], ['sin modificaciones', 'modalidad b'], ['sin cambiar nada', 'modalidad b'], ['igualito al plano', 'modalidad b'], ['igual al proyecto', 'modalidad b'], ['tal cual el proyecto', 'modalidad b'], ['igualito al proyecto', 'modalidad b']]},
            "c": {"id_tramite": "T_174", "palabras": set(), "frases": [], "todas": [['sin cambios', 'modalidad c'], ['sin variaciones', 'modalidad c'], ['igual al plano', 'modalidad c'], ['tal cual el plano', 'modalidad c'], ['sin modificaciones', 'modalidad c'], ['sin cambiar nada', 'modalidad c'], ['igualito al plano', 'modalidad c'], ['igual al proyecto', 'modalidad c'], ['tal cual el proyecto', 'modalidad c'], ['igualito al proyecto', 'modalidad c']]},
            "d": {"id_tramite": "T_175", "palabras": set(), "frases": [], "todas": [['sin cambios', 'modalidad d'], ['sin variaciones', 'modalidad d'], ['igual al plano', 'modalidad d'], ['tal cual el plano', 'modalidad d'], ['sin modificaciones', 'modalidad d'], ['sin cambiar nada', 'modalidad d'], ['igualito al plano', 'modalidad d'], ['igual al proyecto', 'modalidad d'], ['tal cual el proyecto', 'modalidad d'], ['igualito al proyecto', 'modalidad d']]},
            "e": {"id_tramite": "T_176", "palabras": set(), "frases": [], "todas": [['con cambios', 'modalidad a'], ['con variaciones', 'modalidad a'], ['con modificaciones', 'modalidad a'], ['cambie', 'modalidad a'], ['modifique', 'modalidad a'], ['distinto al plano', 'modalidad a'], ['distinto al proyecto', 'modalidad a'], ['diferente al proyecto', 'modalidad a'], ['varie', 'modalidad a'], ['con diferencias', 'modalidad a']]},
            "f": {"id_tramite": "T_177", "palabras": set(), "frases": [], "todas": [['con cambios', 'modalidad b'], ['con variaciones', 'modalidad b'], ['con modificaciones', 'modalidad b'], ['cambie', 'modalidad b'], ['modifique', 'modalidad b'], ['distinto al plano', 'modalidad b'], ['distinto al proyecto', 'modalidad b'], ['diferente al proyecto', 'modalidad b'], ['varie', 'modalidad b'], ['con diferencias', 'modalidad b']]},
            "g": {"id_tramite": "T_178", "palabras": set(), "frases": [], "todas": [['con cambios', 'modalidad c'], ['con variaciones', 'modalidad c'], ['con modificaciones', 'modalidad c'], ['cambie', 'modalidad c'], ['modifique', 'modalidad c'], ['distinto al plano', 'modalidad c'], ['distinto al proyecto', 'modalidad c'], ['diferente al proyecto', 'modalidad c'], ['varie', 'modalidad c'], ['con diferencias', 'modalidad c']]},
            "h": {"id_tramite": "T_179", "palabras": set(), "frases": [], "todas": [['con cambios', 'modalidad d'], ['con variaciones', 'modalidad d'], ['con modificaciones', 'modalidad d'], ['cambie', 'modalidad d'], ['modifique', 'modalidad d'], ['distinto al plano', 'modalidad d'], ['distinto al proyecto', 'modalidad d'], ['diferente al proyecto', 'modalidad d'], ['varie', 'modalidad d'], ['con diferencias', 'modalidad d']]},
            "i": {"id_tramite": "T_180", "palabras": set(), "frases": ['parcial', 'por etapas', 'una etapa', 'primera etapa', 'segunda etapa', 'solo una etapa']},
        },
        "frases_no_seguro": _NS,
        "mensaje_no_seguro": ('Revisa la licencia de tu habilitación urbana: ahí figura la modalidad (A, B, C o D). Dime también si ejecutaste todo igual al proyecto o hiciste cambios, o si recibes solo una etapa.'),
    },
    "consultar_regularizacion_obras": {
        "pregunta": ('Claro, te ayudo a regularizar lo que se hizo sin licencia. ¿Qué construiste o habilitaste sin licencia?\na) Solo habilité un terreno sin licencia (lotes, calles, hasta el 17 de septiembre de 2018)\nb) Habilité el terreno Y construí sin licencia, y quiero regularizar las dos cosas juntas\nc) Solo construí o edifiqué sin licencia (casa, ampliación, remodelación o demolición)\nRespóndeme con la letra o cuéntame tu caso.'),
        "opciones": {
            "a": {"id_tramite": "T_181", "palabras": set(), "frases": ['habilitacion urbana', 'lotizacion', 'urbanizacion', 'terreno sin habilitar', 'sin habilitar', 'habilite']},
            "b": {"id_tramite": "T_182", "palabras": set(), "frases": [], "todas": [['habilitacion', 'edificacion'], ['terreno', 'casa'], ['lotizacion', 'construccion'], ['conjunta'], ['conjuntamente'], ['las dos cosas'], ['ambas cosas'], ['los dos'], ['a la vez'], ['urbanizacion', 'construccion']]},
            "c": {"id_tramite": "T_224", "palabras": set(), "frases": ['construi sin licencia', 'casa sin licencia', 'edificacion', 'construccion', 'obra sin licencia', 'construi mi casa', 'construir sin licencia', 'regularizar mi casa', 'ampliacion', 'sin permiso']},
        },
        "frases_no_seguro": _NS,
        "mensaje_no_seguro": ('Cuéntame si lo que hiciste sin licencia fue habilitar un terreno (lotizar, abrir calles), construir, o ambas cosas, y te oriento.'),
    },
    "consultar_libre_disponibilidad": {
        "pregunta": ('Claro, te ayudo con la libre disponibilidad. ¿Cuál es tu caso?\na) Soy propietario de un lote urbano y quiero la libre disponibilidad para usarlo y construir\nb) Es un área de uso público (terreno de aportes o vías) para un proyecto de inversión pública\nRespóndeme con la letra o cuéntame tu caso.'),
        "opciones": {
            "a": {"id_tramite": "T_232", "palabras": set(), "frases": ['lote urbano', 'mi lote', 'mi terreno', 'propietario', 'construir', 'mi casa']},
            "b": {"id_tramite": "T_246", "palabras": set(), "frases": ['inversion publica', 'aportes', 'uso publico', 'areas de uso publico', 'via publica', 'vias', 'entidad publica', 'obra publica']},
        },
        "frases_no_seguro": _NS,
        "mensaje_no_seguro": ('Dime si eres propietario de un lote urbano que quieres usar libremente (opción a), o si es un área pública (aportes o vías) para un proyecto de inversión pública (opción b).'),
    },
    "consultar_obras_via_publica": {
        "pregunta": ('Claro, te ayudo con trabajos en la vía o áreas públicas. ¿Qué necesitas?\na) Construir, arreglar o acondicionar la vereda o una rampa frente a mi predio\nb) Ya terminé la obra en área pública y quiero la conformidad de obra\nc) Dejar materiales de construcción o instalaciones provisionales en la berma lateral\nd) Soy empresa de servicios (agua, luz o gas) y voy a instalar o dar mantenimiento a redes\ne) Abrir o romper la pista o la vereda (apertura de pistas y veredas)\nRespóndeme con la letra o cuéntame tu caso.'),
        "opciones": {
            "a": {"id_tramite": "T_233", "palabras": set(), "frases": ['vereda frente', 'rampa', 'refaccionar la vereda', 'arreglar la vereda', 'arreglar mi vereda', 'acondicionar la vereda', 'refaccionar mi vereda']},
            "b": {"id_tramite": "T_240", "palabras": set(), "frases": ['conformidad', 'ya termine', 'termine los trabajos', 'concluida', 'culmine']},
            "c": {"id_tramite": "T_241", "palabras": set(), "frases": ['berma', 'materiales de construccion', 'arena', 'ladrillos', 'desmonte', 'dejar materiales', 'ocupar la vereda', 'ocupar la pista', 'instalaciones provisionales']},
            "d": {"id_tramite": "T_242", "palabras": set(), "frases": ['agua', 'luz', 'gas natural', 'alcantarillado', 'electricidad', 'empresa de servicios', 'tuberias', 'redes', 'epsel', 'electronorte', 'alumbrado publico', 'mantenimiento', 'empresa electrica', 'electrica']},
            "e": {"id_tramite": "T_243", "palabras": set(), "frases": ['abrir la pista', 'romper la pista', 'apertura de pistas', 'romper la vereda', 'abrir zanja', 'zanja', 'pistas y veredas', 'abrir la vereda']},
        },
        "frases_no_seguro": _NS,
        "mensaje_no_seguro": ('Cuéntame si es para arreglar la vereda frente a tu casa, poner materiales en la berma, romper la pista para una conexión, o si eres empresa de agua, luz o gas.'),
    },
    "consultar_telecomunicaciones": {
        "pregunta": ('Claro, te ayudo con infraestructura de telecomunicaciones. ¿Qué necesitas?\na) Ya terminé de instalar la infraestructura de banda ancha y quiero la conformidad de ejecución\nb) Autorización para instalar infraestructura y redes para banda ancha\nc) Autorización para instalar una estación de radiocomunicación (antena o torre)\nd) Autorización para otra infraestructura de telecomunicaciones (que no es estación de radiocomunicación)\ne) Ampliar el plazo de mi autorización de telecomunicaciones\nRespóndeme con la letra o cuéntame tu caso.'),
        "opciones": {
            "a": {"id_tramite": "T_235", "palabras": set(), "frases": ['conformidad de la instalacion', 'conformidad de obra', 'conformidad', 'termine la instalacion', 'finalizo la instalacion', 'concluy']},
            "b": {"id_tramite": "T_236", "palabras": set(), "frases": ['banda ancha', 'fibra optica', 'fibra', 'internet']},
            "c": {"id_tramite": "T_237", "palabras": set(), "frases": ['radiocomunicacion', 'antena', 'torre', 'estacion base', 'celular', 'estacion de radio']},
            "d": {"id_tramite": "T_238", "palabras": set(), "frases": ['cableado', 'postes', 'ductos', 'camaras', 'cables', 'infraestructura distinta', 'distinta a', 'red de']},
            "e": {"id_tramite": "T_239", "palabras": set(), "frases": ['ampliacion de plazo', 'ampliar el plazo', 'mas plazo', 'prorroga', 'extender el plazo', 'amplien']},
        },
        "frases_no_seguro": _NS,
        "mensaje_no_seguro": ('Cuéntame si es para instalar banda ancha o fibra, una antena o estación de radiocomunicación, otra infraestructura, o si ya instalaste y quieres la conformidad o más plazo.'),
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


from backend.nlp.configuracion_dialogo import preparar_macros
from backend.nlp.preprocesamiento import preprocesar_texto

preparar_macros(INTENCIONES_MACRO)


def contiene_frase_exacta(texto, frase):
    """Coincidencia con límites: luz != luces, lotes != sublotes."""
    return bool(re.search(rf"(?<!\w){re.escape(frase)}(?!\w)", texto))


def interpretar_seleccion_macro(clave_macro, texto):
    texto = preprocesar_texto(texto)
    texto = re.sub(r"^(?:(?:quiero|elijo|escojo)\s+)?(?:(?:la|el)\s+)?(?:opcion|alternativa|letra)\s+", "", texto)
    texto = re.sub(r"^(?:la|el)\s+(?=[a-k](?:\s|$))", "", texto)
    texto = re.sub(r"\s+por favor$", "", texto)
    partes = texto.split()
    permitidas = {"con", "sin", "revisor", "revisores", "urbano", "urbanos", "por", "comision", "municipal", "municipalidad"}
    if partes and partes[0] in INTENCIONES_MACRO[clave_macro]["opciones"] and set(partes[1:]) <= permitidas:
        return partes[0]
    return None


def coincidencias_intencion_macro(clave_macro, texto_preprocesado):
    """Todas las opciones compatibles; nunca desempatar por orden o puntaje."""
    texto = preprocesar_texto(texto_preprocesado)
    config = INTENCIONES_MACRO[clave_macro]
    coincidencias = []
    for clave, datos in config["opciones"].items():
        if any(contiene_frase_exacta(texto, f) for f in datos.get("excluir", ())):
            continue
        frases = any(contiene_frase_exacta(texto, f) for f in datos.get("frases", ()))
        todas = any(all(contiene_frase_exacta(texto, f) for f in grupo) for grupo in datos.get("todas", ()))
        palabras = any(contiene_frase_exacta(texto, f) for f in datos.get("palabras", ()))
        if frases or todas or palabras:
            coincidencias.append(clave)
    return tuple(coincidencias)


def solicita_revisor(texto):
    texto = preprocesar_texto(texto)
    return bool(re.search(r"\brevisor(?:es)?\b", texto)) and not re.search(r"\b(?:sin|no quiero|no prefiero)\s+(?:un\s+)?revisor\b", texto)


def resolver_intencion_macro(clave_macro, texto_preprocesado, estricto=True):
    """Conserva el contrato (opción, id). El diálogo usa siempre modo estricto."""
    config = INTENCIONES_MACRO[clave_macro]
    texto = preprocesar_texto(texto_preprocesado)
    if any(contiene_frase_exacta(texto, frase) for frase in config["frases_no_seguro"]):
        return "no_seguro", None
    opcion = interpretar_seleccion_macro(clave_macro, texto)
    if opcion is None:
        coincidencias = coincidencias_intencion_macro(clave_macro, texto)
        if len(coincidencias) == 1:
            opcion = coincidencias[0]
        elif not coincidencias and not estricto:
            candidatos = {k for k, datos in config["opciones"].items() for palabra in datos.get("palabras", ())
                          if len(palabra) >= 5 and difflib.get_close_matches(palabra, texto.split(), n=1, cutoff=0.86)}
            if len(candidatos) == 1:
                opcion = candidatos.pop()
    if opcion is None:
        return None, None
    datos = config["opciones"][opcion]
    codigo = datos.get("id_revisor") if solicita_revisor(texto) else None
    return opcion, codigo or datos["id_tramite"]


def resolver_grupo_macro(clave_macro, texto_preprocesado):
    config = INTENCIONES_MACRO[clave_macro]
    grupos = config.get("grupos", {})
    texto = preprocesar_texto(texto_preprocesado)
    numero = re.fullmatch(r"(?:(?:el |la )?(?:grupo |opcion |numero ))?([1-5])(?: por favor)?", texto)
    if numero and numero[1] in grupos:
        return numero[1]
    encontrados = [k for k, grupo in grupos.items() if any(contiene_frase_exacta(texto, f) for f in grupo.get("frases", ()))]
    if not encontrados:
        # Una palabra distintiva de un grupo también es una respuesta válida:
        # «uno residencial» no exige repetir «terreno residencial pequeño».
        comunes = set('el la los las un una uno de del en para por con sin y o mi que quiero mejor grupo caso casos proyecto proyectos licencia certificado obra obras urbana habilitacion pequeno pequena grande municipal terreno terrenos lote lotes casa vivienda edificio local inspeccion etapa etapas'.split())
        comunes.update(clave_macro.removeprefix('consultar_').split('_'))
        vocabularios = {k: set(preprocesar_texto(g['etiqueta'] + ' ' + ' '.join(g.get('frases', ()))).split()) - comunes for k,g in grupos.items()}
        tokens = set(texto.split()) - comunes
        for k,vocabulario in vocabularios.items():
            if re.search(r'\b(?:sin|no)\b',preprocesar_texto(grupos[k]['etiqueta'])) and not re.search(r'\b(?:sin|no|aislado)\b',texto):
                continue
            exclusivos = vocabulario - set().union(*(v for otro,v in vocabularios.items() if otro != k))
            if any(len(p) >= 4 and p in tokens and not re.search(rf'\b(?:no|sin)\s+(?:un |una |uno )?{re.escape(p)}\b',texto) for p in exclusivos):
                encontrados.append(k)
    return encontrados[0] if len(encontrados) == 1 else None


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
