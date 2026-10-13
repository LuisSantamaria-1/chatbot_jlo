import pytest
import pandas as pd
from backend.nlp.preprocesamiento import (
    preprocesar_texto,
    traducir_jerga,
    detectar_subintencion_directa,
)
from backend.nlp.clasificador import predecir_intencion
from config import UMBRAL_CONFIANZA, UMBRAL_DUDA_MIN, UMBRAL_DUDA_MAX


# ==============================================================================
# GRUPO A: NORMALIZACIÓN DE TEXTO Y TRADUCCIÓN DE JERGA (10 CASOS)
# ==============================================================================
CASOS_PREPROCESAMIENTO = [
    ("NLP_A01", "HOLA BUENOS DIAS", "hola buenos dias"),
    ("NLP_A02", "trámite de numeración", "tramite de numeracion"),
    ("NLP_A03", "¡hola!, ¿cuál es el costo?", "hola cual es el costo"),
    ("NLP_A04", "kiero mi permiso", "quiero mi permiso"),
    ("NLP_A05", "q requisitos piden", "que requisitos piden"),
    ("NLP_A06", "sacar lisencia municipal", "sacar licencia municipal"),
    ("NLP_A07", "necesito altoke mi constancia", "necesito rapido mi constancia"),
    ("NLP_A08", "como hago pa tramitar", "como hago para tramitar"),
    ("NLP_A09", "kiero lisencia altoke pa mi tienda", "quiero licencia rapido para mi tienda"),
    ("NLP_A10", "ayuda xfa", "ayuda por favor"),
]

@pytest.mark.parametrize("test_id, entrada, esperado", CASOS_PREPROCESAMIENTO)
def test_preprocesamiento_y_jerga(registrar, test_id, entrada, esperado):
    obtenido = preprocesar_texto(entrada)
    estado = "PASO" if obtenido == esperado else "FALLO"
    registrar(test_id, "preprocesamiento", entrada, esperado, obtenido, 1.0, estado)
    assert obtenido == esperado


# ==============================================================================
# GRUPO B: CLASIFICACIÓN DE INTENCIONES CON FRASES NUEVAS (30 CASOS)
# Verificado previamente que NINGUNA de estas frases existe en train ni test
# ==============================================================================
CASOS_INTENCIONES = [
    # 6 Clases Generales
    ("NLP_B01", "que tal como te va", "saludo"),
    ("NLP_B02", "nos vemos que te vaya bien", "despedida"),
    ("NLP_B03", "tienes amigos robots", "charla_casual"),
    ("NLP_B04", "dime la tarifa y precio", "consultar_costo"),
    ("NLP_B05", "en cuantos dias me responden", "consultar_plazo"),
    ("NLP_B06", "a que hora abren el cine en chiclayo", "fuera_de_dominio"),

    # 6 Macrointenciones (2 casos por cada una)
    ("NLP_B07", "quiero tramitar el cese definitivo de mi negocio", "consultar_gestion_licencia"),
    ("NLP_B08", "como hago para vender mi tienda y pasarle la licencia al nuevo comprador", "consultar_gestion_licencia"),
    ("NLP_B09", "se extravio la tarjeta de circulacion de mi mototaxi", "consultar_tramite_vehicular"),
    ("NLP_B10", "quiero empadronar mi moto recien comprada", "consultar_tramite_vehicular"),
    ("NLP_B11", "solicito incrementar el numero de unidades de mi empresa de mototaxis", "consultar_gestion_flota_vehicular"),
    ("NLP_B12", "nuestra asociacion de mototaxistas necesita permiso para un nuevo paradero", "consultar_gestion_flota_vehicular"),
    ("NLP_B13", "como solicito la conexion de agua potable para una persona juridica", "consultar_conexion_agua"),
    ("NLP_B14", "que piden para autorizarme romper la pista para instalar desague", "consultar_conexion_agua"),
    ("NLP_B15", "iniciar tramite de separacion mutua y divorcio rapido", "consultar_divorcio"),
    ("NLP_B16", "ya pasaron dos meses de mi separacion quiero el divorcio ulterior", "consultar_divorcio"),
    ("NLP_B17", "requisitos para casarme por civil un dia sabado fuera del municipio", "consultar_matrimonio_civil"),
    ("NLP_B18", "matrimonio civil comunitario de mi hermano", "consultar_matrimonio_civil"),

    # Trámites específicos (2 casos por trámite)
    ("NLP_B19", "deseo copia certificada de los acuerdos de concejo del mes pasado", "T_001"),
    ("NLP_B20", "solicito acceso a la informacion publica sobre el presupuesto municipal", "T_001"),
    ("NLP_B21", "tengo una bodeguita en mi casa y quiero abrirla con permiso provisional", "T_003"),
    ("NLP_B22", "licencia temporal para una bodega de abarrotes de barrio", "T_003"),
    ("NLP_B23", "requisitos para habilitacion urbana de predio menor de cinco hectareas", "T_007"),
    ("NLP_B24", "aprobacion municipal de proyecto de habilitacion urbana modal B", "T_007"),
    ("NLP_B25", "quiero dividir mi lote urbano en dos partes para mis hijos", "T_008"),
    ("NLP_B26", "regularizacion de subdivision de terreno urbano sin obras", "T_008"),
    ("NLP_B27", "necesito que la municipalidad le asigne numero de puerta a mi casa", "T_015"),
    ("NLP_B28", "certificado para saber la numeracion oficial de mi inmueble", "T_015"),
    ("NLP_B29", "visacion de planos para pedir luz electrica en mi lote de posesion", "T_080"),
    ("NLP_B30", "constancia y plano visado para tramite de electrificacion en asentamiento humano", "T_080"),
]

@pytest.mark.parametrize("test_id, entrada, esperado", CASOS_INTENCIONES)
def test_clasificacion_intenciones(registrar, test_id, entrada, esperado):
    obtenido, confianza = predecir_intencion(entrada)
    estado = "PASO" if obtenido == esperado else "FALLO"
    registrar(test_id, "clasificacion_intenciones", entrada, esperado, obtenido, confianza, estado)
    assert obtenido == esperado, (
        f"Fallo semántico: entrada='{entrada}', esperado='{esperado}', "
        f"obtenido='{obtenido}', confianza={confianza:.4f}"
    )


# ==============================================================================
# GRUPO C: REGLAS DE DECISIÓN Y UMBRALES (5 CASOS)
# ==============================================================================
def test_regla_costo_vs_plazo(registrar):
    entrada = "cuantos dias demora"
    subint = detectar_subintencion_directa(entrada)
    esperado = "plazo"
    estado = "PASO" if subint == esperado else "FALLO"
    registrar("NLP_C01", "reglas_subintencion", entrada, esperado, subint, 1.0, estado)
    assert subint == esperado

def test_regla_horario_no_activa_plazo(registrar):
    entrada = "cual es el horario de atencion de mesa de partes"
    subint = detectar_subintencion_directa(entrada)
    esperado = None
    estado = "PASO" if subint is None else "FALLO"
    registrar("NLP_C02", "reglas_subintencion", entrada, "None", str(subint), 1.0, estado)
    assert subint is None

def test_logica_zona_duda(registrar):
    # Simular evaluación de confianza en rango de duda [0.35, 0.54]
    conf_ejemplo = 0.45
    en_duda = UMBRAL_DUDA_MIN <= conf_ejemplo <= UMBRAL_DUDA_MAX
    registrar("NLP_C03", "reglas_umbrales", f"conf={conf_ejemplo}", "en_zona_duda=True", f"en_zona_duda={en_duda}", conf_ejemplo, "PASO" if en_duda else "FALLO")
    assert en_duda is True

def test_logica_rango_fallback_intermedio(registrar):
    # Rango 0.55 - 0.69 debe caer fuera de duda y menor que UMBRAL_CONFIANZA (0.70)
    conf_ejemplo = 0.62
    fuera_de_duda = conf_ejemplo > UMBRAL_DUDA_MAX
    menor_que_umbral = conf_ejemplo < UMBRAL_CONFIANZA
    es_fallback = fuera_de_duda and menor_que_umbral
    registrar("NLP_C04", "reglas_umbrales", f"conf={conf_ejemplo}", "es_fallback=True", f"es_fallback={es_fallback}", conf_ejemplo, "PASO" if es_fallback else "FALLO")
    assert es_fallback is True

def test_logica_confianza_menor_minimo(registrar):
    # Confianza < 0.35 es menor a UMBRAL_DUDA_MIN y UMBRAL_CONFIANZA
    conf_ejemplo = 0.25
    es_muy_baja = conf_ejemplo < UMBRAL_DUDA_MIN
    registrar("NLP_C05", "reglas_umbrales", f"conf={conf_ejemplo}", "menor_a_minimo=True", f"menor_a_minimo={es_muy_baja}", conf_ejemplo, "PASO" if es_muy_baja else "FALLO")
    assert es_muy_baja is True
