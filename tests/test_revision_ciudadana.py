"""Consultas aportadas por el ciudadano y regresiones de varios turnos.

Los códigos sugeridos en el adjunto no son oráculos: varias consultas omiten
riesgo, ubicación o tipo de documento. Esas deben aclararse antes de dar datos.
Se usa el clasificador real y el catálogo completo en SQLite efímero.
"""
import json
from pathlib import Path
import re

import pytest

from app import app
from backend.nlp.preprocesamiento import detectar_campos_consulta

CASOS = json.loads(Path(__file__).with_name('casos_revision_ciudadana.json').read_text(encoding='utf-8'))
DIRECTOS = dict(zip(
    [2,3,4,12,13,14,15,16,17,18,19,20,21,22,24,25,26,28,30,31,33,36,39,40,42,43,46,48,53,54,55,57,59,61,74,77,78,79,80],
    ['T_002','T_006','T_005','T_049','T_012','T_011','T_010','T_247','T_047','T_051','T_052','T_054','T_053','T_050',
     'T_016','T_020','T_022','T_248','T_034','T_021','T_024','T_224','T_107','T_106','T_074','T_061','T_015','T_031',
     'T_025','T_243','T_241','T_060','T_062','T_001','T_127','T_005','T_006','T_003','T_015']))
DIRECTOS[10] = 'T_027'
PROPUESTAS = {1:'T_003', 50:'T_244', 52:'T_032', 62:'T_013'}
ACLARACIONES = {
    5:'aclarar_titular_local',6:'consultar_licencia_funcionamiento',7:'tipo_licencia',8:'explicar_concepto',
    9:'consultar_itse',11:'consultar_tramite_vehicular',23:'consultar_matrimonio_civil',27:'consultar_matrimonio_civil',
    29:'consultar_divorcio',32:'consultar_registro_canino',34:'consultar_licencia_construccion',
    35:'consultar_licencia_ampliacion_remodelacion',37:'consultar_prorroga_revalidacion_licencia',
    38:'consultar_conformidad_obra',41:'explicar_concepto',44:'consultar_independizacion_terreno_rustico',
    45:'consultar_habilitacion_urbana',47:'consultar_numeracion_municipal',51:'consultar_catastro_predial',56:'consultar_publicidad_exterior',
    58:'consultar_evento_publico',60:'aclarar_certificacion_sanitaria',63:'consultar_recurso_administrativo',
    64:'explicar_concepto',67:'consulta_general',69:'tipo_licencia',73:'consultar_licencia_funcionamiento',
    75:'consultas_multiples',76:'campos_comunes_macro',
}
ESCALARES = {12:{'costo'},14:{'plazo'},15:{'costo'},22:{'costo'},24:{'costo','plazo'},25:{'costo'},
             26:{'costo'},31:{'costo'},46:{'costo'},61:{'costo'},77:{'costo'},78:{'costo'},79:{'costo'},80:{'plazo'}}


@pytest.fixture
def vecino():
    with app.test_client() as cliente:
        yield cliente


def decir(cliente, mensaje):
    r = cliente.post('/api/chat', json={'mensaje': mensaje})
    assert r.status_code == 200, r.get_json()
    d = r.get_json()
    assert d['status'] != 'error', d
    assert not re.search(r'(?:^|\n)(?:[a-k]|[1-8])[).] ', d['mensaje']) or d['status'] == 'success', d
    if d['status'] != 'success':
        assert d['opciones'] == [], d
    else:
        assert [b['texto'] for b in d['opciones']] == ['Requisitos','Costo','Plazo','Otro trámite']
        assert d['datosTramite']['id_tramite'] == d['id_tramite']
    return d


@pytest.mark.parametrize('caso', CASOS['independientes'], ids=lambda c:str(c['numero']))
def test_ochenta_consultas_reales(vecino, caso):
    n = caso['numero']
    d = decir(vecino, caso['consulta'])
    if n in DIRECTOS:
        assert d.get('id_tramite') == DIRECTOS[n], d
    elif n in PROPUESTAS:
        assert d.get('id_tramite_sugerido') == PROPUESTAS[n], d
        assert not d.get('id_tramite'), d
    elif n in ACLARACIONES:
        assert d.get('intent') == ACLARACIONES[n], d
        assert not d.get('id_tramite'), d
    elif n == 49:
        assert d['intent'] == 'explicar_concepto' and 'predio' in d['mensaje']
    elif n == 65:
        assert d['status'] == 'saludo'
    else:
        assert n in {66,68,70,71,72}
        assert d['status'] == 'fallback' and not d.get('datosTramite'), d
    if n in ESCALARES:
        assert {c for c in ('requisitos','costo','plazo') if c in d} == ESCALARES[n], d
    if n == 76:
        assert d['plazo'] == '20 días hábiles'
    if n == 80:
        assert 'Inmediato (0 días hábiles)' in d['mensaje']


@pytest.mark.parametrize('inicio', ['T_015','quiero hacer una habilitacion urbana'])
@pytest.mark.parametrize('numero', [2,3,4,5,6,8,12,13,14,15,16,17,18,23,24,27,29,33,36,42,44,46,49,60,61,63,64,67,68,69,71,72,74,75,77,78,79,80])
def test_nueva_consulta_no_hereda_otro_asunto(vecino, inicio, numero):
    decir(vecino, inicio)
    caso = CASOS['independientes'][numero-1]
    d = decir(vecino, caso['consulta'])
    if numero in DIRECTOS:
        assert d.get('id_tramite') == DIRECTOS[numero], d
    elif numero in ACLARACIONES:
        assert d['intent'] == ACLARACIONES[numero], d
    else:
        assert not d.get('id_tramite'), d
    if numero in ESCALARES:
        assert {c for c in ('requisitos','costo','plazo') if c in d} == ESCALARES[numero], d


def test_transcripcion_completa_sin_menus_ni_errores(vecino):
    rs = [decir(vecino, q) for q in CASOS['conversacion']]
    for turno in (7,16,17,18,21):
        assert rs[turno-1]['status'] == 'clarification', (turno,rs[turno-1])
    for turno,codigo in {15:'T_079',37:'T_095',41:'T_012',45:'T_247',55:'T_016',71:'T_103',
                         94:'T_060',102:'T_029',110:'T_016',126:'T_016',127:'T_016',
                         129:'T_005',130:'T_006',131:'T_003',132:'T_015'}.items():
        assert rs[turno-1].get('id_tramite') == codigo, (turno,rs[turno-1])
    assert rs[32]['intent'] == 'consultar_licencia_funcionamiento'
    assert rs[58]['status'] == 'clarification'  # Otro matrimonio, falta el lugar.
    assert rs[77]['intent'] == 'consultar_habilitacion_urbana'
    assert rs[36].get('costo') and not rs[36].get('requisitos')
    assert rs[40].get('requisitos') and not rs[40].get('costo')
    for indice in (125,128):
        assert rs[indice].get('costo') and not rs[indice].get('requisitos')


def test_pregunta_de_riesgo_conserva_costo(vecino):
    decir(vecino,'cuanto sale la licencia para un restaurant grande, riesgo alto creo q es')
    d = decir(vecino,'sí, riesgo alto')
    assert d['id_tramite'] == 'T_067' and d.get('costo') and not d.get('requisitos')
    assert decir(vecino,'ya me demoro la licencia, cuantos dias son pe')['id_tramite'] == 'T_067'


def test_renovar_itse_despues_de_explicacion(vecino):
    decir(vecino,'T_015')
    decir(vecino,'q es eso del ITSE para mi polleria')
    decir(vecino,'mi certificado de defensa civil ya vencio, como lo renuevo y cuanto cuesta')
    d = decir(vecino,'bajo')
    assert d['id_tramite'] == 'T_095' and d.get('costo') and not d.get('requisitos')


@pytest.mark.parametrize('respuesta,codigo', [('la licencia del negocio','T_004'),('la propiedad del local',None)])
def test_distingue_propiedad_de_licencia(vecino,respuesta,codigo):
    decir(vecino,CASOS['independientes'][4]['consulta'])
    d = decir(vecino,respuesta)
    assert d.get('id_tramite') == codigo, d


@pytest.mark.parametrize('respuesta,codigo', [('el certificado del restaurante','T_028'),('el carnet personal para manipular alimentos',None)])
def test_distingue_carnet_de_certificado(vecino,respuesta,codigo):
    decir(vecino,CASOS['independientes'][59]['consulta'])
    d = decir(vecino,respuesta)
    assert d.get('id_tramite') == codigo, d


def test_cambia_de_asunto_antes_de_responder_aclaracion(vecino):
    decir(vecino,CASOS['independientes'][4]['consulta'])
    d = decir(vecino,CASOS['independientes'][5]['consulta'])
    assert d['status'] == 'clarification' and not d.get('id_tramite')
    assert decir(vecino,'sí')['id_tramite'] == 'T_067'


def test_rectifica_grupo_resuelto(vecino):
    decir(vecino,'quiero una habilitacion urbana')
    decir(vecino,'terreno residencial')
    decir(vecino,'por etapas')
    assert decir(vecino,'si')['id_tramite'] == 'T_079'
    assert decir(vecino,'no me confundi es por residencial')['status'] == 'clarification'
    assert decir(vecino,'terreno residencial sin habilitar')['id_tramite'] == 'T_077'


def test_consulta_doble_conserva_campos_de_cada_asunto(vecino):
    assert decir(vecino,CASOS['independientes'][74]['consulta'])['intent'] == 'consultas_multiples'
    d = decir(vecino,'muni')
    assert d['id_tramite'] == 'T_016' and d.get('costo') and not d.get('requisitos'), d
    assert decir(vecino,'cuantos dias tarda el matrimonio civil')['plazo'] == '20 días hábiles'
    d = decir(vecino,'es gratis el cese de actividades')
    assert d['id_tramite'] == 'T_005' and d.get('costo') and not d.get('requisitos'), d
    decir(vecino,'continuar con la otra')
    d = decir(vecino,'quiero obtener uno por primera vez')
    assert d['id_tramite'] == 'T_014' and d.get('requisitos') and not d.get('costo'), d


@pytest.mark.parametrize('salida',['chau','ya no quiero nada','otro tramite','no es lo que pregunte'])
def test_cierra_consultas_pendientes(vecino,salida):
    decir(vecino,CASOS['independientes'][74]['consulta'])
    decir(vecino,salida)
    with vecino.session_transaction() as s:
        assert not s.get('consultas_en_espera')


@pytest.mark.parametrize('texto,esperado', [
    ('necesito mi certificado de numeracion cuanto es',('costo',)),
    ('en que tiempo me entregan el certificado de numeracion',('plazo',)),
    ('cuanto es el plazo',('plazo',)),
    ('cuanto sale casarse en la muni y que dias se demora todo',('costo','plazo')),
    ('es gratis el cese de actividades',('costo',)),
    ('que documentos necesito',('requisitos',)),
])
def test_campos_segun_lo_pedido(texto,esperado):
    assert detectar_campos_consulta(texto) == esperado


def test_revision_del_servidor_es_la_cargada_al_arrancar(vecino):
    r = vecino.get('/')
    assert r.headers['X-Leonardito-Revision'] == app.config['CODIGO_REVISION']


def test_plazo_no_comun_si_existe_alternativa_con_revisor(vecino):
    d=decir(vecino,'cuanto demora aprobar una habilitacion urbana modalidad d')
    assert d['status']=='clarification' and d['intent']=='consultar_habilitacion_urbana'
    assert 'plazo' not in d  # 48 días por comisión y 5 por revisor; falta el caso.


@pytest.mark.parametrize('codigo',['T_221','T_222','T_223'])
def test_conserva_dias_calendario(vecino,codigo):
    d=decir(vecino,'cuanto demora '+codigo)
    assert 'calendario' in d['plazo'] and 'calendario' in d['mensaje']
    assert 'hábiles' not in d['mensaje']


def test_taller_no_se_interpreta_como_vivienda(vecino):
    d=decir(vecino,'Necesito permiso para construir un taller de servicios.')
    assert d['id_tramite']=='T_129',d
