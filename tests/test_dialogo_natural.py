"""Conversaciones ciudadanas completas, con clasificador real y sin simular intenciones."""

import pytest

from app import app
from backend.chatbot.entendimiento import comprender


@pytest.fixture
def vecino():
    with app.test_client() as cliente:
        yield cliente


def decir(cliente, mensaje):
    respuesta = cliente.post('/api/chat', json={'mensaje': mensaje})
    assert respuesta.status_code == 200
    return respuesta.get_json()


def test_conversacion_adjunta_alternativas_y_pregunta_de_costo(vecino):
    assert decir(vecino, 'Hola')['status'] == 'saludo'
    assert decir(vecino, 'quiero saber como casarme en la municipalidad')['id_tramite'] == 'T_016'
    alternativas = decir(vecino, 'hay otro forma de casarme?')
    assert alternativas['status'] == 'clarification'
    assert 'otras alternativas' in alternativas['mensaje']
    assert alternativas['opciones'] == []
    assert decir(vecino, 'fuera del local')['status'] == 'clarification'
    dentro = decir(vecino, 'dentro del distrito')
    assert dentro['status'] == 'clarification'
    assert 'domicilio' in dentro['mensaje']
    resultado = decir(vecino, 'en un salon')
    assert resultado['id_tramite'] == 'T_017'
    assert decir(vecino, 'y cuanto me van a cobrar por eso')['costo'] == 'S/ 300.20'
    assert decir(vecino, 'ya')['intent'] == 'acuse_recibo'
    assert decir(vecino, 'y cuantos dias demora')['plazo'] == '20 días hábiles'


def test_cambio_de_lugar_conserva_pregunta_de_precio(vecino):
    assert decir(vecino, 'cuanto cuesta casarme en la municipalidad')['costo'] == 'S/ 240.00'
    resultado = decir(vecino, 'y cuanto cuesta en una ceremonia fuera de la municipalidad?')
    assert resultado['status'] == 'clarification'
    assert resultado['opciones'] == []
    decir(vecino, 'aca nomas')
    resultado = decir(vecino, 'en un salon')
    assert resultado['id_tramite'] == 'T_017'
    assert resultado['costo'] == 'S/ 300.20'


def test_respuestas_sociales_no_cortan_la_conversacion(vecino):
    decir(vecino, 'quiero casarme en la muni')
    assert decir(vecino, 'como estas')['status'] == 'charla_casual'
    assert decir(vecino, 'quiero hablar contigo')['status'] == 'charla_casual'
    for frase in ['no', 'no', 'ok', 'ok', 'ya', 'listo', 'si']:
        resultado = decir(vecino, frase)
        assert resultado['status'] == 'charla_casual'
        assert 'exclusivamente' not in resultado['mensaje']
    assert decir(vecino, 'y cuanto cuesta')['id_tramite'] == 'T_016'


def test_rectifica_un_dato_sin_reiniciar_todo(vecino):
    decir(vecino, 'quiero casarme')
    decir(vecino, 'fuera del local')
    decir(vecino, 'dentro del distrito')
    assert decir(vecino, 'mejor en mi jato')['id_tramite'] == 'T_020'


def test_construccion_aprende_modalidad_y_cambios_en_turnos_separados(vecino):
    macro = 'consultar_modificacion_proyecto_edificacion'
    with vecino.session_transaction() as sesion:
        sesion['macro_pendiente'] = macro
    primera = decir(vecino, 'ya me dieron la licencia')
    assert primera['status'] == 'clarification'
    segunda = decir(vecino, 'solo un cambio pequeño')
    assert segunda['status'] == 'clarification'
    assert 'modalidad' in segunda['mensaje']
    tercera = decir(vecino, 'creo que la b')
    assert tercera['id_tramite'] == 'T_194'


@pytest.mark.parametrize('macro,frases,codigo', [
    ('consultar_conexion_agua', ['es para mi casa'], 'T_025'),
    ('consultar_conexion_agua', ['para una empresa privada'], 'T_026'),
    ('consultar_publicidad_exterior', ['va a tener luces'], 'T_060'),
    ('consultar_publicidad_exterior', ['no lleva ninguna luz'], 'T_007'),
    ('consultar_itse', ['quiero renovarlo', 'el riesgo es bajo'], 'T_095'),
    ('consultar_divorcio', ['ya la tengo aprobada'], 'T_034'),
    ('consultar_tramite_vehicular', ['se me perdio el documento'], 'T_049'),
    ('consultar_lotes_urbanos', ['quiero unirlos en uno solo'], 'T_061'),
    ('consultar_registro_canino', ['es mestizo'], 'T_023'),
    ('consultar_licencia_cerco', ['es compartido con los vecinos'], 'T_117'),
])
def test_detalles_naturales_en_distintos_tramites(vecino, macro, frases, codigo):
    with vecino.session_transaction() as sesion:
        sesion['macro_pendiente'] = macro
    for frase in frases:
        resultado = decir(vecino, frase)
    assert resultado.get('id_tramite') == codigo, resultado


def test_comprension_acumula_atributos_sin_elegir_por_azar():
    opcion, marco = comprender('consultar_matrimonio_civil', 'fuera del local')
    assert opcion is None and set(marco['candidatos']) == {'b', 'd', 'e'}
    opcion, marco = comprender('consultar_matrimonio_civil', 'dentro del distrito', marco)
    assert opcion is None and set(marco['candidatos']) == {'b', 'e'}
    opcion, marco = comprender('consultar_matrimonio_civil', 'en un salón', marco)
    assert opcion == 'b'


def test_aclaraciones_sin_numeros(vecino):
    resultado = decir(vecino, 'quiero casarme')
    assert resultado['status'] == 'clarification'
    assert 'Respóndeme con' not in resultado['mensaje']
    assert not any(f'{i})' in resultado['mensaje'] for i in range(1, 6))
    assert decir(vecino, 'que?')['status'] == 'clarification'


@pytest.mark.parametrize('macro,pregunta,respuesta,codigo', [
    ('consultar_publicidad_exterior', 'luz', 'si', 'T_060'),
    ('consultar_publicidad_exterior', 'luz', 'no', 'T_007'),
    ('consultar_divorcio', 'aprobada', 'si', 'T_034'),
    ('consultar_divorcio', 'aprobada', 'no', 'T_009'),
    ('consultar_catastro_predial', 'código catastral', 'si', 'T_057'),
    ('consultar_catastro_predial', 'código catastral', 'no', 'T_058'),
])
def test_si_y_no_responden_la_pregunta_pendiente(vecino, macro, pregunta, respuesta, codigo):
    inicio = {'consultar_publicidad_exterior': 'quiero colocar un letrero',
              'consultar_divorcio': 'quiero divorciarme',
              'consultar_catastro_predial': 'necesito informacion sobre catastro'}
    datos = decir(vecino, inicio[macro])
    assert pregunta in datos['mensaje']
    assert decir(vecino, respuesta)['id_tramite'] == codigo


def test_duda_entre_dos_modalidades_pide_aclaracion(vecino):
    decir(vecino, 'quiero casarme')
    datos = decir(vecino, 'en mi casa o con el alcalde')
    assert datos['status'] == 'clarification'
    assert not datos.get('id_tramite')
    assert decir(vecino, 'la del alcalde')['id_tramite'] == 'T_021'


def test_seguimientos_con_otras_formas_de_preguntar(vecino):
    decir(vecino, 'quiero casarme en la municipalidad')
    assert decir(vecino, 'y cuanto me saldria')['costo'] == 'S/ 240.00'
    assert decir(vecino, 'cuanto tardaria eso')['plazo'] == '20 días hábiles'
    assert decir(vecino, 'que debo llevar')['requisitos']


def test_datos_numericos_en_varios_turnos(vecino):
    inicial = decir(vecino, 'quiero construir mi casa')
    assert inicial['status'] == 'clarification'
    assert 'pisos' in inicial['mensaje']
    assert 'metros' in decir(vecino, 'dos')['mensaje']
    assert 'única' in decir(vecino, '100,5')['mensaje']
    assert decir(vecino, 'si')['id_tramite'] == 'T_103'


def test_area_de_un_mercado_sin_elegir_letras(vecino):
    datos = decir(vecino, 'quiero construir un mercado')
    assert datos['status'] == 'clarification'
    assert 'metros' in datos['mensaje']
    assert decir(vecino, '20000')['id_tramite'] == 'T_151'


def test_compara_lugares_sin_arrastrar_una_ubicacion_anterior(vecino):
    decir(vecino, 'cuanto cuesta casarme en la municipalidad')
    fuera = decir(vecino, 'y en otro distrito cuanto me costaria')
    assert fuera['id_tramite'] == 'T_019'
    assert fuera['costo'] == 'S/ 344.90'
    de_nuevo = decir(vecino, 'y en la muni cuanto era')
    assert de_nuevo['id_tramite'] == 'T_016'


def test_rectificar_modalidad_de_habilitacion_no_repite_la_anterior(vecino):
    decir(vecino, 'quiero sacar una habilitacion urbana')
    assert decir(vecino, 'inversion publica')['id_tramite'] == 'T_075'
    corregida = decir(vecino, 'pero el mio es modalidad B')
    assert corregida['status'] == 'clarification'
    assert 'id_tramite' not in corregida
    assert decir(vecino, 'terreno residencial sin habilitar')['id_tramite'] == 'T_077'
    assert decir(vecino, 'es modalidad C')['status'] == 'clarification'
    assert decir(vecino, 'venta garantizada de lotes')['id_tramite'] == 'T_081'


def test_matrimonio_generico_no_adivina_local_con_semantica(vecino, monkeypatch):
    monkeypatch.setattr('backend.chatbot.entendimiento.sugerir', lambda *args: 'a')
    respuesta = decir(vecino, 'quiero casarme pe')
    assert respuesta['status'] == 'clarification'
    assert 'dónde' in respuesta['mensaje'].lower()


def test_rectificacion_natural_de_separacion(vecino):
    decir(vecino, 'quiero divorciarme')
    inicial = decir(vecino, 'no aun no')
    assert inicial['id_tramite'] == 'T_009'
    corregida = decir(vecino, 'ah no, si lo tengo')
    assert corregida['id_tramite'] == 'T_034'


def test_feria_sin_exigir_la_palabra_licencia(vecino):
    respuesta = decir(vecino, 'quiero abrir una feria de juegos en la plaza civica')
    assert respuesta['id_tramite'] == 'T_062'
