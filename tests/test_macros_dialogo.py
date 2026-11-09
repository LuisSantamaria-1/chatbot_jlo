"""Resolución real de todas las macros y contrato del diálogo por niveles."""

from collections import Counter
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from app import app
from backend.nlp import clasificador as nlp
from backend.chatbot.menus import menu_macro
from casos_macros import CASOS

CONTRATO = json.loads(Path(__file__).with_name('contrato_macros.json').read_text(encoding='utf-8'))
REVISORES = [(m, k, frase, CONTRATO[m][k]['id_revisor']) for m, k, frase in CASOS if CONTRATO[m][k].get('id_revisor')]


@pytest.fixture
def ciudadano():
    with app.test_client() as client:
        yield client


def decir(client, mensaje):
    respuesta = client.post('/api/chat', json={'mensaje': mensaje})
    assert respuesta.status_code == 200
    return respuesta.get_json()


def test_cobertura_cinco_consultas_por_opcion():
    cantidades = Counter((m, k) for m, k, frase in CASOS)
    assert set(cantidades) == {(m, k) for m, c in nlp.INTENCIONES_MACRO.items() for k in c['opciones']}
    assert all(n == 5 for n in cantidades.values())
    assert len(CASOS) == len(set(CASOS))
    assert nlp.INTENCIONES_MACRO.keys() == CONTRATO.keys()


@pytest.mark.parametrize('macro,opcion,frase', CASOS)
def test_cada_opcion_con_resolver_real(macro, opcion, frase):
    assert nlp.coincidencias_intencion_macro(macro, frase) == (opcion,)
    assert nlp.resolver_intencion_macro(macro, frase, estricto=True) == (opcion, CONTRATO[macro][opcion]['id_tramite'])


@pytest.mark.parametrize('macro,opcion,frase,codigo', REVISORES)
def test_cinco_consultas_por_alternativa_revisor(macro, opcion, frase, codigo):
    assert nlp.resolver_intencion_macro(macro, frase + ' Prefiero evaluación con Revisor Urbano.', estricto=True) == (opcion, codigo)


@pytest.mark.parametrize('macro', list(CONTRATO))
def test_no_seguro_en_todas_las_macros(macro):
    for frase in nlp.INTENCIONES_MACRO[macro]['frases_no_seguro']:
        assert nlp.resolver_intencion_macro(macro, frase, estricto=True) == ('no_seguro', None)


@pytest.mark.parametrize('macro', list(CONTRATO))
def test_menus_breves_y_grupos_completos(macro):
    config = nlp.INTENCIONES_MACRO[macro]
    grupos = config.get('grupos', {})
    assert bool(grupos) == (len(config['opciones']) > 5)
    if grupos:
        assert 3 <= len(grupos) <= 5
        assert sorted(k for g in grupos.values() for k in g['opciones']) == sorted(config['opciones'])
    for grupo in (None, *grupos):
        mensaje, nivel, elegido = menu_macro(macro, grupo)
        assert len(mensaje.splitlines()) <= 5
        assert 'revisor' not in mensaje.lower()
        assert mensaje.splitlines()[-1].startswith('Respóndeme')
        if grupo:
            assert nivel == 2 and elegido == grupo
            for k in grupos[grupo]['opciones']:
                assert f'{k})' in mensaje
            for k in set(config['opciones']) - set(grupos[grupo]['opciones']):
                assert f'{k})' not in mensaje
        assert all(len(v['etiqueta'].split()) < 8 for v in config['opciones'].values())


@pytest.mark.parametrize('macro,opcion', [(m, k) for m,c in CONTRATO.items() for k in c])
def test_api_opcion_explicita_conserva_contrato_y_botones(ciudadano, macro, opcion):
    with ciudadano.session_transaction() as sesion:
        sesion['macro_pendiente'] = macro
        sesion['macro_nivel_pendiente'] = 1
    datos = decir(ciudadano, opcion)
    assert datos['id_tramite'] == CONTRATO[macro][opcion]['id_tramite']
    assert {'status', 'intent', 'confianza', 'id_tramite', 'nombre', 'requisitos', 'datosTramite', 'mensaje', 'opciones'} <= datos.keys()
    assert [b['texto'] for b in datos['opciones']] == ['Requisitos', 'Costo', 'Plazo', 'Otro trámite']
    with ciudadano.session_transaction() as sesion:
        assert 'macro_pendiente' not in sesion
        assert 'macro_nivel_pendiente' not in sesion
        assert 'macro_grupo_pendiente' not in sesion


def test_ejemplos_solicitados_con_modelo_y_resolver_reales(ciudadano):
    assert decir(ciudadano, 'quiero casarme dentro de la municipalidad')['id_tramite'] == 'T_016'
    assert decir(ciudadano, 'no era eso')['status'] == 'clarification'
    decir(ciudadano, 'otro tramite')
    assert decir(ciudadano, 'quiero casarme')['status'] == 'clarification'
    decir(ciudadano, 'otro tramite')
    datos = decir(ciudadano, 'habilitacion urbana para un proyecto del estado')
    assert datos['status'] == 'clarification' and datos['opciones'] == []
    with ciudadano.session_transaction() as sesion:
        assert sesion['macro_nivel_pendiente'] == 2
        assert sesion['macro_grupo_pendiente'] == '1'
    decir(ciudadano, 'otro tramite')
    assert decir(ciudadano, 'quiero habilitar un terreno para vender lotes con garantia')['id_tramite'] == 'T_081'
    decir(ciudadano, 'otro tramite')
    datos = decir(ciudadano, 'quiero hacer una habilitacion urbana')
    assert datos['status'] == 'clarification' and datos['opciones'] == []
    with ciudadano.session_transaction() as sesion:
        assert sesion['macro_nivel_pendiente'] == 1


def test_arbol_con_letras_globales_revisor_y_correccion(ciudadano):
    decir(ciudadano, 'quiero hacer una habilitacion urbana')
    nivel2 = decir(ciudadano, '2')
    assert 'residencial' in nivel2['mensaje'].lower() and 'proyecto' in nivel2['mensaje'].lower()
    assert 'Respóndeme con' not in nivel2['mensaje'] and nivel2['opciones'] == []
    normal = decir(ciudadano, 'c')
    assert normal['id_tramite'] == 'T_077'
    assert normal['mensaje'].count('Si prefieres Revisor Urbano, dímelo.') == 1
    revisor = decir(ciudadano, 'prefiero revisor urbano')
    assert revisor['id_tramite'] == 'T_078'
    assert 'Si prefieres' not in revisor['mensaje']
    assert decir(ciudadano, 'no era eso')['status'] == 'clarification'
    with ciudadano.session_transaction() as sesion:
        assert sesion['macro_nivel_pendiente'] == 1
    assert decir(ciudadano, 'c con revisor')['id_tramite'] == 'T_078'


@pytest.mark.parametrize('nivel', [1, 2])
def test_revisor_funciona_en_cualquier_nivel(ciudadano, nivel):
    decir(ciudadano, 'quiero hacer una habilitacion urbana')
    if nivel == 2:
        decir(ciudadano, '1')
    assert decir(ciudadano, 'c con revisor')['id_tramite'] == 'T_078'


def test_ambiguedad_y_limites_sin_difflib():
    assert nlp.resolver_intencion_macro('consultar_matrimonio_civil', 'quiero casarme') == (None, None)
    assert nlp.resolver_intencion_macro('consultar_matrimonio_civil', 'quiero casarme en mi casa o con el alcalde') == (None, None)
    assert nlp.resolver_intencion_macro('consultar_publicidad_exterior', 'mi anuncio no tiene luz') == ('a', 'T_007')
    assert nlp.resolver_intencion_macro('consultar_publicidad_exterior', 'mi anuncio tiene luces') == (None, None)
    assert nlp.resolver_intencion_macro('consultar_lotes_urbanos', 'quiero información de lotes') == (None, None)
    assert nlp.resolver_intencion_macro('consultar_matrimonio_civil', 'quiero otro u otra') == (None, None)
    with patch.object(nlp.difflib, 'get_close_matches', side_effect=AssertionError('No usar difflib')):
        assert nlp.resolver_intencion_macro('consultar_lotes_urbanos', 'quiero subdividr mi terreno', estricto=True) == (None, None)


def test_transcripcion_del_ciudadano(ciudadano):
    decir(ciudadano, 'hola')
    assert decir(ciudadano, 'necesito casarme ya')['status'] == 'clarification'
    assert decir(ciudadano, 'en la muni nomas')['id_tramite'] == 'T_016'
    assert decir(ciudadano, 'y cuanto cuesta')['costo'] == 'S/ 240.00'
    assert decir(ciudadano, 'ah ya gracias')['intent'] == 'agradecimiento'
    assert decir(ciudadano, 'y el plazo cuando es')['plazo'] == '20 días hábiles'
    decir(ciudadano, 'otro tramite')
    assert decir(ciudadano, 'cuanto me costaria casarme la municipalidad')['costo'] == 'S/ 240.00'


def test_todos_los_tramites_son_alcanzables():
    from backend.models import Tramite
    codigos = {t.id_tramite for t in Tramite.query.all()}
    referencias = {d['id_tramite'] for c in nlp.INTENCIONES_MACRO.values() for d in c['opciones'].values()}
    referencias |= {d['id_revisor'] for c in nlp.INTENCIONES_MACRO.values() for d in c['opciones'].values() if d.get('id_revisor')}
    referencias |= {str(c) for c in nlp.modelo_nlp.classes_ if str(c).startswith('T_')}
    assert referencias == codigos
