"""Requisitos, costo y plazo se explican por separado en todo el catálogo."""
import csv

import pytest
from app import app
from config import CSV_TRAMITES_PATH


@pytest.fixture
def vecino():
    with app.test_client() as c:
        yield c


def decir(c, texto):
    r = c.post('/api/chat', json={'mensaje':texto})
    assert r.status_code == 200
    return r.get_json()


with open(CSV_TRAMITES_PATH, encoding='utf-8-sig', newline='') as f:
    CATALOGO = list(csv.DictReader(f))


@pytest.mark.parametrize('fila', CATALOGO, ids=lambda r:r['ID_Tramite'])
def test_campos_separados_para_cada_tramite(vecino, fila):
    requisitos = decir(vecino, fila['ID_Tramite'])
    assert requisitos['id_tramite'] == fila['ID_Tramite']
    assert requisitos['nombre'] == fila['Nombre']
    assert requisitos['requisitos'] == [r.strip() for r in fila['Requisitos'].split('|') if r.strip()]
    assert 'costo' not in requisitos and 'plazo' not in requisitos
    assert 'El costo para' not in requisitos['mensaje'] and 'El plazo para' not in requisitos['mensaje']
    assert '¿Te ayudo con otro trámite?' not in requisitos['mensaje']
    costo = decir(vecino, 'cuanto cuesta')
    assert costo['costo'] == fila['Costo']
    assert costo['nombre'] in costo['mensaje']
    assert 'plazo' not in costo and 'requisitos' not in costo
    assert 'El plazo para' not in costo['mensaje']
    plazo = decir(vecino, 'cuanto demora')
    assert plazo['plazo'] == fila['Plazo']
    assert plazo['nombre'] in plazo['mensaje']
    assert 'costo' not in plazo and 'requisitos' not in plazo
    assert 'El costo para' not in plazo['mensaje']


def test_nombre_y_valor_explicitos(vecino):
    decir(vecino, 'quiero registrar a mi perro')
    decir(vecino, 'comun')
    costo = decir(vecino, 'cuanto cuesta')
    assert costo['mensaje'] == 'El costo para «Inscripción en registro canino municipal» es S/ 20.10.'
    plazo = decir(vecino, 'cuanto es el plazo')
    assert plazo['mensaje'] == 'El plazo para «Inscripción en registro canino municipal» es de 7 días hábiles.'


def test_explicar_conceptos_no_selecciona_el_tramite(vecino):
    decir(vecino, 'quiero divorciarme')
    explicacion = decir(vecino, 'que es eso')
    assert explicacion['intent'] == 'explicar_concepto'
    assert 'id_tramite' not in explicacion
    otra = decir(vecino, 'no se que es divorcio ulterior')
    assert otra['intent'] == 'explicar_concepto' and 'id_tramite' not in otra
    assert decir(vecino, 'no')['id_tramite'] == 'T_009'


def test_corrige_documento_despues_de_resolver(vecino):
    decir(vecino, 'quiero divorciarme')
    assert decir(vecino, 'si')['id_tramite'] == 'T_034'
    assert decir(vecino, 'no, me equivoque no lo tengo')['id_tramite'] == 'T_009'


def test_costo_pendiente_y_casita(vecino):
    decir(vecino, 'cuanto cuesta el tramite para casarme')
    datos = decir(vecino, 'en mi casita')
    assert datos['id_tramite'] == 'T_020'
    assert 'requisitos' not in datos and 'plazo' not in datos
    assert datos['costo'] == 'S/ 290.10'


@pytest.mark.parametrize('frase', ['quiero casarme con mi ñora', 'necesito casarme con mi flaca'])
def test_pareja_no_es_evidencia_del_local(vecino, monkeypatch, frase):
    monkeypatch.setattr('backend.chatbot.entendimiento.sugerir', lambda *a: 'a')
    respuesta = decir(vecino, frase)
    assert respuesta['status'] == 'clarification'
    assert '¿Dónde' in respuesta['mensaje']
    assert '¿te refieres' not in respuesta['mensaje']


@pytest.mark.parametrize('frase', ['quiero postergar mi boda', 'postergar mi boda', 'necesito aplazar mi matrimonio', 'quiero reprogramar la ceremonia'])
def test_operacion_especifica_no_abre_matrimonio_generico(vecino, frase):
    decir(vecino, 'quiero casarme')
    respuesta = decir(vecino, frase)
    assert respuesta['id_tramite'] == 'T_248'


def test_perrito_y_despedida_con_decision_pendiente(vecino):
    respuesta = decir(vecino, 'quiero sacar licencia para tener mi perrito')
    assert respuesta['intent'] == 'consultar_registro_canino'
    assert decir(vecino, 'bye')['status'] == 'despedida'
    with vecino.session_transaction() as s:
        assert 'macro_pendiente' not in s


def test_matrimonio_celebrado_no_se_confunde_con_casarse(vecino):
    decir(vecino, 'T_023')
    respuesta = decir(vecino, 'me case en este distrito pero yo soy de otro que debo hacer')
    assert respuesta['intent'] == 'consulta_no_registrada'
    assert 'id_tramite' not in respuesta
    with vecino.session_transaction() as s:
        assert 'tramite_actual' not in s


def test_siglas_se_expanden_sin_alterar_requisito_oficial(vecino):
    datos = decir(vecino, 'T_023')
    assert 'FUT (Formulario Único de Trámite)' in datos['mensaje']
    assert 'FUT (Formulario Único de Trámite)' not in datos['requisitos'][0]
