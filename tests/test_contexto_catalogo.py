"""Regresión por HTTP con el modelo real, no solo coincidencias del resolver.

Se verifican cinco formulaciones por cada alternativa, rectificaciones de todas
ellas y la transcripción que reveló la pérdida de contexto. La sesión inicial
solo fija la familia: el ciudadano no selecciona letras ni repite títulos.
"""

import json
from pathlib import Path
import re

import pytest

from app import app
from backend.chatbot.entendimiento import normalizar_dialogo
from backend.nlp import clasificador as nlp
from casos_macros import CASOS


CONTRATO = json.loads(Path(__file__).with_name('contrato_macros.json').read_text(encoding='utf-8'))
PRIMERAS = list({(m, k): (m, k, f) for m, k, f in reversed(CASOS)}.values())


@pytest.fixture
def vecino():
    with app.test_client() as cliente:
        yield cliente


def decir(cliente, texto):
    r = cliente.post('/api/chat', json={'mensaje': texto})
    assert r.status_code == 200
    d = r.get_json()
    assert d['status'] != 'error', d
    if d['status'] != 'success':
        assert d['opciones'] == []
        assert not re.search(r'(?:^|\n)[a-k]\)', d['mensaje'])
    return d


def completar(cliente, macro, opcion, respuesta):
    # Medidas y hechos que el bot debe preguntar, nunca adivinar por similitud.
    detalles = {
        'consultar_licencia_construccion': {
            'a': 'Será la única vivienda del lote, de un piso y 120 metros cuadrados',
            'b': 'Serán tres pisos con 300 metros cuadrados en total',
            'c': 'Serán seis pisos y 3500 metros cuadrados en total',
        },
        'consultar_licencia_edificacion_no_vivienda': {
            'a': 'El área total será de 1000 metros cuadrados',
            'b': 'El área total será de 31000 metros cuadrados',
            'c': 'El área total será de 1000 metros cuadrados',
            'd': 'El área total será de 16000 metros cuadrados',
            'e': 'Tendrá capacidad para 1000 personas',
            'f': 'Tendrá capacidad para 21000 personas',
        },
    }
    if respuesta['status'] != 'success' and opcion in detalles.get(macro, {}):
        respuesta = decir(cliente, detalles[macro][opcion])
    if respuesta['status'] != 'success':
        with cliente.session_transaction() as s:
            propuesta = s.get('marco_dialogo', {}).get('propuesta')
        if propuesta:
            assert propuesta == opcion, respuesta
            respuesta = decir(cliente, 'sí, eso quiero')
    return respuesta


@pytest.mark.parametrize('macro,opcion,frase', CASOS)
def test_cinco_frases_por_alternativa_en_api(vecino, registrar, macro, opcion, frase):
    with vecino.session_transaction() as s:
        s['macro_pendiente'] = macro
    primera = decir(vecino, frase)
    if primera['status'] == 'success':
        camino = 'directo'
    else:
        with vecino.session_transaction() as s:
            camino = 'nivel ' + str(s.get('macro_nivel_pendiente', 1))
    respuesta = completar(vecino, macro, opcion, primera)
    codigo = CONTRATO[macro][opcion]['id_tramite']
    registrar('catalogo_natural/' + camino, macro, frase, codigo, respuesta.get('id_tramite'),
              respuesta.get('confianza'), respuesta['status'])
    assert respuesta.get('id_tramite') == codigo, respuesta


@pytest.mark.parametrize('macro,opcion,frase', PRIMERAS)
def test_rectificar_cualquier_alternativa(vecino, macro, opcion, frase):
    otra = next(k for k in CONTRATO[macro] if k != opcion)
    # La letra prepara un caso ya resuelto; la corrección ciudadana es natural.
    with vecino.session_transaction() as s:
        s['macro_pendiente'] = macro
    assert decir(vecino, otra)['id_tramite'] == CONTRATO[macro][otra]['id_tramite']
    respuesta = completar(vecino, macro, opcion, decir(vecino, 'No, me confundí. ' + frase))
    assert respuesta.get('id_tramite') == CONTRATO[macro][opcion]['id_tramite'], respuesta


def test_transcripcion_del_ciudadano(vecino):
    pasos = [
        ('quiero casarme', None, 'consultar_matrimonio_civil'),
        ('en mi casita pe', 'T_020', None),
        ('como te llamas?', None, 'charla_casual'),
        ('quiero tomar el puesto del mercado porque se murio mi tio el dueño', 'T_051', None),
        ('cuanto cuesta?', 'T_051', None),
        ('como saco permiso para un puesto de feria?', 'T_062', None),
        ('quiero sacar una licencia relacionada a HU', None, 'consultar_habilitacion_urbana'),
        ('proyecto del estado', None, 'consultar_habilitacion_urbana'),
        ('inversion publica', 'T_075', None),
        ('nooo, era vivienda estatal me confundi', 'T_076', None),
        ('era por concesion', 'T_075', None),
        ('estamos hablando de hu', None, 'consultar_habilitacion_urbana'),
        ('construir a la vez', None, 'consultar_habilitacion_urbana'),
        ('ampliar', None, 'consultar_licencia_ampliacion_remodelacion'),
        ('si eso quiero', None, 'consultar_licencia_ampliacion_remodelacion'),
        ('tamos remodelando el edifcio multifamiliar', 'T_145', None),
        ('remodelar pe tmr', 'T_145', None),
        ('remodelar el edificio ptmr', 'T_145', None),
    ]
    for frase, codigo, intent in pasos:
        r = decir(vecino, frase)
        if codigo:
            assert r.get('id_tramite') == codigo, (frase, r)
        else:
            assert r.get('intent') == intent, (frase, r)


@pytest.mark.parametrize('frase', ['edifcio multifamiliar', 'edfiicio multifamiliar', 'edificio multifamiliar'])
def test_erratas_largas_sin_exigir_frase_exacta(vecino, frase):
    decir(vecino, 'quiero ampliar')
    r = decir(vecino, 'estamos remodelando el ' + frase + ' pe')
    assert r.get('id_tramite') == 'T_145', r


@pytest.mark.parametrize('palabra', ['luz', 'luces', 'lotes', 'sublotes', 'otro', 'otra', 'cambio', 'pequeno', 'pequena'])
def test_normalizacion_no_confunde_palabras_validas(palabra):
    assert normalizar_dialogo(palabra) == palabra


def test_indice_lexico_solo_propone_nunca_resuelve(vecino, monkeypatch):
    # Palabras conocidas en otro orden; sin modelo semántico ni frase exacta.
    monkeypatch.setattr('backend.chatbot.entendimiento.sugerir', lambda *args: None)
    with vecino.session_transaction() as s:
        s['macro_pendiente'] = 'consultar_lotes_urbanos'
    frase = 'los lotes quiero que terminen fusionados'
    assert not nlp.coincidencias_intencion_macro('consultar_lotes_urbanos', frase)
    r = decir(vecino, frase)
    assert r['status'] == 'clarification' and not r.get('datosTramite'), r
    with vecino.session_transaction() as s:
        assert s['marco_dialogo'].get('propuesta') == 'b', r
    r = decir(vecino, 'sí, eso quiero')
    assert r['id_tramite'] == 'T_061'


@pytest.mark.parametrize('frase,codigo', [
    ('Quiero demoler todo mi inmueble de mas de cinco pisos', 'T_141'),
    ('Quiero demoler dos pisos con explosivos', 'T_141'),
    ('Quiero demoler dos pisos con sotano', 'T_123'),
    ('Quiero demoler solo una parte de mi casa de dos pisos', 'T_121'),
])
def test_medidas_no_anulan_condiciones_especiales(vecino, frase, codigo):
    r = decir(vecino, frase)
    assert r.get('id_tramite') == codigo, r


def test_limite_inferior_no_equivale_a_medida_exacta(vecino):
    r = decir(vecino, 'quiero construir un mercado con mas de 1000 metros cuadrados')
    assert r['status'] == 'clarification' and not r.get('id_tramite'), r
    assert decir(vecino, '16000')['id_tramite'] == 'T_151'


def test_negacion_de_una_alternativa_no_la_selecciona(vecino):
    decir(vecino, 'quiero casarme')
    r = decir(vecino, 'no quiero que nos case el alcalde')
    assert r['status'] == 'clarification' and not r.get('id_tramite'), r
    assert decir(vecino, 'en mi casa')['id_tramite'] == 'T_020'
