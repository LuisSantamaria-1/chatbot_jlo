"""Comprueba el diálogo y cierra su servidor HTTP temporal al terminar.

Por defecto usa SQLite temporal. --mysql usa la configuración MySQL del proyecto
y registra las consultas sintéticas mediante la auditoría normal del chat.
No ocupa el puerto 5000 ni deja procesos en segundo plano.
"""
import argparse
import json
import os
from pathlib import Path
import secrets
import sys
from threading import Thread

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from config import REPORTS_DIR

CASOS = [
    ('quiero casarme con mi ñora', 'clarification', None, None),
    ('en mi casita', 'success', 'T_020', 'requisitos'),
    ('cuanto cuesta', 'success', 'T_020', 'costo'),
    ('cuanto es el plazo', 'success', 'T_020', 'plazo'),
    ('bye', 'despedida', None, None),
    ('quiero divorciarme', 'clarification', None, None),
    ('que es eso', 'clarification', None, None),
    ('no se que es divorcio ulterior', 'clarification', None, None),
    ('si', 'success', 'T_034', 'requisitos'),
    ('no, me equivoque no lo tengo', 'success', 'T_009', 'requisitos'),
    ('y cuanto cuesta', 'success', 'T_009', 'costo'),
    ('cuantos dias demora', 'success', 'T_009', 'plazo'),
    ('quiero sacar licencia para tener mi perrito', 'clarification', None, None),
    ('comun', 'success', 'T_023', 'requisitos'),
    ('cuanto cuesta', 'success', 'T_023', 'costo'),
    ('cuanto es el plazo', 'success', 'T_023', 'plazo'),
    ('me case en este distrito pero yo soy de otro que debo hacer', 'derivacion', None, None),
    ('quiero postergar mi boda', 'success', 'T_248', 'requisitos'),
    ('cuanto cuesta', 'success', 'T_248', 'costo'),
    ('y cuanto demora', 'success', 'T_248', 'plazo'),
    # Transcripción del ciudadano: cambios de asunto y rectificaciones.
    ('quiero casarme', 'clarification', None, None),
    ('en mi casita pe', 'success', 'T_020', 'requisitos'),
    ('como te llamas?', 'charla_casual', None, None),
    ('quiero tomar el puesto del mercado porque se murio mi tio el dueño', 'success', 'T_051', 'requisitos'),
    ('cuanto cuesta?', 'success', 'T_051', 'costo'),
    ('como saco permiso para un puesto de feria?', 'success', 'T_062', 'requisitos'),
    ('quiero sacar una licencia relacionada a HU', 'clarification', None, None),
    ('proyecto del estado', 'clarification', None, None),
    ('inversion publica', 'success', 'T_075', 'requisitos'),
    ('nooo, era vivienda estatal me confundi', 'success', 'T_076', 'requisitos'),
    ('era por concesion', 'success', 'T_075', 'requisitos'),
    ('estamos hablando de hu', 'clarification', None, None),
    ('construir a la vez', 'clarification', None, None),
    ('ampliar', 'clarification', None, None),
    ('si eso quiero', 'clarification', None, None),
    ('tamos remodelando el edifcio multifamiliar', 'success', 'T_145', 'requisitos'),
    ('remodelar pe tmr', 'success', 'T_145', 'requisitos'),
    ('remodelar el edificio ptmr', 'success', 'T_145', 'requisitos'),
]


def verificar(mysql=False):
    os.environ['CHAT_SEMANTICA'] = '0'
    os.environ.setdefault('SECRET_KEY', secrets.token_hex(32))
    from backend import create_app
    from backend.models import db
    from backend.models.poblado import poblar_base_datos
    from backend.chatbot import routes
    from werkzeug.serving import make_server
    import requests

    if mysql:
        app = create_app()
        with app.app_context():
            assert db.engine.dialect.name == 'mysql', 'La configuración no corresponde a MySQL.'
    else:
        class Config:
            TESTING = True
            SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
            SQLALCHEMY_TRACK_MODIFICATIONS = False
        app = create_app(Config)
        with app.app_context():
            db.create_all()
            poblar_base_datos()
        routes.registrar_conversacion = lambda **kw: None

    # La auditoría normal se conserva en la BD. Este verificador no comparte
    # la rotación del archivo de logs del servidor que usa el ciudadano.
    import logging
    from logging.handlers import RotatingFileHandler
    for logger in (logging.getLogger('backend'), app.logger):
        for handler in list(logger.handlers):
            if isinstance(handler, RotatingFileHandler):
                logger.removeHandler(handler)
                handler.close()

    servidor = make_server('127.0.0.1', 0, app, threaded=True)
    hilo = Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    cliente = requests.Session()
    cliente.trust_env = False
    url = f'http://127.0.0.1:{servidor.server_port}'
    resultados = []
    try:
        pagina = cliente.get(url, timeout=10)
        assert pagina.status_code == 200 and 'acceso-admin' in pagina.text
        js = cliente.get(url + '/static/js/chat.js', timeout=10)
        assert js.status_code == 200 and 'TIEMPO_MINIMO_PENSANDO = 3000' in js.text
        acceso = cliente.get(url + '/admin', timeout=10, allow_redirects=False)
        assert acceso.status_code == 302 and acceso.headers['Location'].endswith('/admin/login')
        login = cliente.get(url + '/admin/login', timeout=10)
        assert login.status_code == 200 and 'id="form-login"' in login.text and 'id="tabla-tramites"' not in login.text
        for recurso in ('/static/css/portal.css', '/static/images/logo-mdjlo.png', '/static/css/admin.css', '/static/js/admin.js'):
            respuesta = cliente.get(url + recurso, timeout=10)
            assert respuesta.status_code == 200 and respuesta.content, recurso
        for texto, estado, codigo, campo in CASOS:
            r = cliente.post(url + '/api/chat', json={'mensaje':texto}, timeout=20)
            datos = r.json()
            assert r.status_code == 200 and datos['status'] == estado, (texto, datos)
            if codigo:
                assert datos['id_tramite'] == codigo, (texto, datos)
                for otro in {'requisitos', 'costo', 'plazo'} - {campo}:
                    assert otro not in datos, (texto, datos)
                assert campo in datos
            resultados.append({'ciudadano':texto, 'respuesta':datos['mensaje'], 'estado':datos['status'],
                               'tramite':datos.get('id_tramite'), 'campo':campo})
    finally:
        servidor.shutdown()
        servidor.server_close()
        hilo.join(timeout=5)
        cliente.close()
    sufijo = '_mysql' if mysql else ''
    REPORTS_DIR.mkdir(exist_ok=True)
    destino = REPORTS_DIR / f'respuestas_claras{sufijo}'
    destino.with_suffix('.json').write_text(json.dumps(resultados, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    lineas = ['# Comprobación de respuestas claras', '',
              'Backend real, HTTP temporal y ' + ('MySQL.' if mysql else 'catálogo temporal SQLite.'),
              'El servidor temporal se cerró al terminar; no se utilizó el puerto 5000.', '']
    for fila in resultados:
        lineas.extend(['**Ciudadano:** ' + fila['ciudadano'], '', '**Leonardito:**', '', fila['respuesta'], ''])
    destino.with_suffix('.md').write_text('\n'.join(lineas), encoding='utf-8')
    print(json.dumps({'turnos_correctos':len(resultados), 'motor':'mysql' if mysql else 'sqlite',
                      'servidor_temporal_cerrado':True}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mysql', action='store_true')
    verificar(parser.parse_args().mysql)
