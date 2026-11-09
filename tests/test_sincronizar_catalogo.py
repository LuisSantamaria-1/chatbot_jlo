"""Regresión: carga completa, respaldo e idempotencia de la sincronización."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.models import db, Tramite, Requisito
from scripts import sincronizar_catalogo


@pytest.fixture
def directorio_catalogo():
    # Temporal dentro del proyecto para evitar restricciones de permisos de Windows.
    # Se elimina al terminar la prueba, sin dejar una carpeta scratch vacía.
    with TemporaryDirectory(prefix='.pytest_catalogo_', dir=Path(__file__).resolve().parents[1]) as temporal:
        yield Path(temporal)


def test_sincronizacion_respalda_y_no_repite_cambios(directorio_catalogo, monkeypatch):
    tmp_path = directorio_catalogo
    uri = 'sqlite:///' + (tmp_path / 'catalogo.sqlite').as_posix()
    engine = create_engine(uri)
    db.metadata.create_all(engine)
    with Session(engine) as sesion, sesion.begin():
        sesion.add(Tramite(id_tramite='T_015', nombre='Nombre antiguo', costo='Anterior', plazo='Anterior',
                          requisitos=[Requisito(descripcion='Requisito anterior', orden=1)]))
    engine.dispose()
    monkeypatch.setattr(sincronizar_catalogo, 'SQLALCHEMY_DATABASE_URI', uri)
    monkeypatch.setattr(sincronizar_catalogo, 'BASE_DIR', tmp_path)
    previo = sincronizar_catalogo.sincronizar()
    assert previo['nuevos'] == 238 and previo['actualizaciones'] == 1
    assert not previo['aplicado']
    aplicado = sincronizar_catalogo.sincronizar(aplicar=True)
    with open(aplicado['respaldo'], encoding='utf-8') as archivo:
        respaldo = json.load(archivo)
    assert len(respaldo) == 1 and respaldo[0]['nombre'] == 'Nombre antiguo'
    final = sincronizar_catalogo.sincronizar(aplicar=True)
    assert final['registros_bd_antes'] == 239
    assert final['nuevos'] == 0 and final['actualizaciones'] == 0
    assert not final['aplicado']
