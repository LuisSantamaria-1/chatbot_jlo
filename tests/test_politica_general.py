"""Regresión del gestor de diálogo sobre TODAS las macros, con el modelo real."""
import pytest

from app import app
from backend.nlp import clasificador as nlp


@pytest.fixture
def vecino():
    with app.test_client() as c:
        yield c


def decir(c, texto):
    r = c.post('/api/chat', json={'mensaje':texto})
    assert r.status_code == 200
    return r.get_json()


CAMBIOS = [
    ('kiero sakar licensia de konstruccion', 'consultar_licencia_construccion', None),
    ('quiero instalar una antena de celular', 'consultar_telecomunicaciones', 'T_237'),
    ('quiero registrar a mi perro', 'consultar_registro_canino', None),
    ('quiero casarme en la municipalidad', 'consultar_matrimonio_civil', 'T_016'),
    ('la muni me denego algo y quiero reclamar', 'consultar_recurso_administrativo', None),
    ('voy a romper la pista para conectar el desague', 'consultar_conexion_agua', None),
    ('quiero pasar mi licencia a nombre de otra persona', 'consultar_gestion_licencia', 'T_004'),
]


@pytest.mark.parametrize('origen', sorted(nlp.INTENCIONES_MACRO))
@pytest.mark.parametrize('consulta,destino,codigo', CAMBIOS)
def test_una_macro_pendiente_no_captura_una_solicitud_nueva(vecino, origen, consulta, destino, codigo):
    opciones = nlp.INTENCIONES_MACRO[origen]['opciones']
    with vecino.session_transaction() as s:
        s['macro_pendiente'] = origen
        s['marco_dialogo'] = {'macro':origen, 'propuesta':next(iter(opciones)), 'pregunta':'riesgo',
                             'atributos':{'area':100, 'unica':True, 'riesgo':'medio'}, 'candidatos':list(opciones)}
    respuesta = decir(vecino, consulta)
    if codigo:
        assert respuesta['id_tramite'] == codigo, respuesta
    else:
        assert respuesta['status'] == 'clarification', respuesta
        assert respuesta['intent'] == destino
        with vecino.session_transaction() as s:
            marco = s['marco_dialogo']
            assert marco['macro'] == destino
            assert not marco.get('propuesta')
            assert 'area' not in marco['atributos']
            assert 'riesgo' not in marco['atributos']


def test_nueva_vivienda_no_hereda_area_ni_unifamiliar(vecino):
    decir(vecino, 'quiero construir mi casa de dos pisos')
    decir(vecino, '100m2')
    assert decir(vecino, 'si')['id_tramite'] == 'T_103'
    otro = decir(vecino, 'voy a hacer un edificio de departamentos de 4 pisos')
    assert otro['status'] == 'clarification'
    assert 'modalidad B' in otro['mensaje']
    with vecino.session_transaction() as s:
        assert 'area' not in s['marco_dialogo']['atributos']
        assert s['marco_dialogo']['atributos']['unica'] is False
    respuesta = decir(vecino, '250m2')
    assert 'Modalidad B' in respuesta['nombre']


def test_finalizar_obra_cambia_de_fase(vecino):
    decir(vecino, 'quiero construir mi casa')
    respuesta = decir(vecino, 'ya termine de construir mi casa y quiero inscribirla')
    assert respuesta['intent'] == 'consultar_conformidad_obra'
    assert 'pisos' not in respuesta['mensaje']


@pytest.mark.parametrize('consulta', ['cuanto cuesta el pasaje a lima', 'donde pago mi recibo de luz', 'cuando pagan la pension 65', 'donde saco mi dni', 'a que hora abren ustedes', 'hay un bache enorme en mi calle a quien aviso'])
def test_fuera_de_dominio_no_usa_contador_de_repeticion(vecino, consulta):
    for _ in range(4):
        respuesta = decir(vecino, consulta)
        assert respuesta['status'] == 'fallback'
        assert 'No quiero hacerte repetir' not in respuesta['mensaje']
        assert not respuesta.get('id_tramite')


@pytest.mark.parametrize('consulta', ['no quiero nada', 'ninguno de ellos jajaja', 'jajaja'])
def test_pausa_social_no_es_fallback(vecino, consulta):
    assert decir(vecino, consulta)['status'] == 'charla_casual'


def test_correccion_de_raza_y_jerga(vecino, monkeypatch):
    monkeypatch.setattr('backend.chatbot.entendimiento.sugerir', lambda *a: 'a')
    pregunta = decir(vecino, 'quiero registrar a mi perro')
    assert 'raza' in pregunta['mensaje']
    assert decir(vecino, 'es mestizo')['id_tramite'] == 'T_023'
    assert decir(vecino, 'no, es un pitubll')['id_tramite'] == 'T_024'
    assert decir(vecino, 'quiero casarme en mi house')['id_tramite'] == 'T_020'


def test_sugerencia_rechazada_y_aclaraciones_no_se_repiten(vecino):
    macro = 'consultar_licencia_ampliacion_remodelacion'
    with vecino.session_transaction() as s:
        s['macro_pendiente'] = macro
        s['marco_dialogo'] = {'macro':macro, 'propuesta':'a', 'atributos':{}, 'candidatos':list('abcdef')}
    respuestas = [decir(vecino, t) for t in ['quiero remodelar mi casa por dentro', 'son mas de 200 m2', 'no mas', 'no se', 'otra vez no se']]
    assert all('¿te refieres a ampliar' not in r['mensaje'] for r in respuestas)
    assert all(a['mensaje'] != b['mensaje'] for a,b in zip(respuestas,respuestas[1:]))


@pytest.mark.parametrize('texto', ['no entendi', 'eso no es lo que pregunte'])
def test_reparacion_explicita_reinicia(vecino, texto):
    decir(vecino, 'quiero licencia de funcionamiento')
    respuesta = decir(vecino, texto)
    assert respuesta['status'] == 'correction'
    with vecino.session_transaction() as s:
        assert 'macro_pendiente' not in s and 'marco_dialogo' not in s


def test_consulta_sobre_condicion_usa_catalogo(vecino):
    decir(vecino, 'quiero postergar la fecha de mi matrimonio')
    respuesta = decir(vecino, 'si tengo mas de 2 meses ya no puedo')
    assert respuesta['intent'] == 'detalle_tramite_actual'
    assert '2 meses' in respuesta['mensaje']
    assert 'no tengo claro' not in respuesta['mensaje'].lower()


def test_licencia_ambigua_y_acceso_admin(vecino):
    respuesta = decir(vecino, 'no se que licencia necesito')
    assert respuesta['intent'] == 'tipo_licencia'
    assert 'construcción' in respuesta['mensaje']
    assert decir(vecino, 'b')['intent'] == 'consultar_licencia_construccion'
    pagina = vecino.get('/').get_data(as_text=True)
    assert 'class="acceso-admin" href="/admin"' in pagina


def test_todas_las_macros_estan_en_el_modelo():
    assert set(nlp.INTENCIONES_MACRO) <= set(nlp.modelo_nlp.classes_)


@pytest.mark.parametrize('macro', sorted(nlp.INTENCIONES_MACRO))
def test_dispatch_no_depende_de_lista_parcial_de_palabras(vecino, monkeypatch, macro):
    # Se aísla el contrato clasificador -> diálogo; el modelo real se usa en
    # las 195 conversaciones de cambios de asunto anteriores.
    monkeypatch.setattr(nlp, 'predecir_intencion', lambda texto: (macro, .9))
    respuesta = decir(vecino, 'consulta sobre ese asunto')
    assert respuesta['status'] == 'clarification'
    assert respuesta['intent'] == macro


def test_letra_responde_modalidad_preguntada_y_no_numero_de_fila(vecino):
    decir(vecino, 'quiero consultar un anteproyecto de edificacion')
    assert decir(vecino, 'b')['id_tramite'] == 'T_207'


def test_modalidad_b_tras_conformidad_no_reabre_otra_fila(vecino):
    decir(vecino, 'ya termine de construir mi casa y quiero inscribirla')
    decir(vecino, 'no')
    assert decir(vecino, 'b')['id_tramite'] == 'T_219'
