"""Consultas ciudadanas para los 16 procedimientos fuera de las macros."""
import pytest

from app import app


CONSULTAS = [
    ('T_001', 'quiero que me entreguen informacion publica que tiene la muni'),
    ('T_003', 'quiero abrir una bodeguita con licencia provisional'),
    ('T_008', 'me piden visar el plano para rectificar los linderos'),
    ('T_013', 'somos una junta vecinal y queremos registrarnos como organizacion social'),
    ('T_027', 'quiero saber si el uso de mi local es compatible con la zona'),
    ('T_031', 'necesito una constancia de posesion para pedir agua en mi lote'),
    ('T_032', 'mi casa esta ruinosa y me piden certificar que no se puede vivir ahi'),
    ('T_033', 'me piden los parametros urbanisticos para diseñar mi construccion'),
    ('T_056', 'necesito el certificado que acredita como se llama mi calle'),
    ('T_099', 'voy a hacer un espectaculo para 2500 personas y me piden evaluar la seguridad'),
    ('T_210', 'quiero presentar la predeclaratoria de mi edificacion'),
    ('T_234', 'la resolucion de mi construccion tiene un error de escritura y quiero rectificarla'),
    ('T_244', 'necesito certificar a que distrito pertenece mi predio'),
    ('T_245', 'me piden certificar la ubicacion y medidas de mi terreno con sus linderos'),
    ('T_248', 'necesito cambiar la fecha de mi boda'),
    ('T_249', 'nos vamos a casar en otra municipalidad y necesitamos publicar el edicto aqui'),
]


@pytest.mark.parametrize('codigo,frase', CONSULTAS)
def test_tramites_fuera_de_macro_sin_codigo_ni_titulo(registrar, codigo, frase):
    with app.test_client() as c:
        d = c.post('/api/chat', json={'mensaje': frase}).get_json()
        if d['status'] == 'clarification':
            assert d.get('id_tramite_sugerido') == codigo, d
            d = c.post('/api/chat', json={'mensaje': 'sí, eso estoy buscando'}).get_json()
        registrar('catalogo_individual', 'procedimientos_individuales', frase, codigo, d.get('id_tramite'), d.get('confianza'), d['status'])
        assert d.get('id_tramite') == codigo, d
