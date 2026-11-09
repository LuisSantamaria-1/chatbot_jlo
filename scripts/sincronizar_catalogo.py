r"""Compara el CSV con la BD. --aplicar sincroniza con respaldo y transacción.

Uso: .venv\Scripts\python.exe scripts/sincronizar_catalogo.py [--aplicar]
No modifica usuarios ni conversaciones, y no elimina trámites adicionales.
"""

import argparse
import csv
from datetime import datetime
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.orm import Session, selectinload
from backend.models import Tramite, Requisito
from config import BASE_DIR, CSV_TRAMITES_PATH, SQLALCHEMY_DATABASE_URI


def sincronizar(aplicar=False):
    with open(CSV_TRAMITES_PATH, encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.DictReader(archivo))
    codigos = [fila["ID_Tramite"].strip() for fila in filas]
    if len(filas) != 239 or len(set(codigos)) != 239 or any(not re.fullmatch(r"T_\d{3}", codigo) for codigo in codigos):
        raise ValueError("El catálogo debe contener 239 códigos T_XXX únicos.")
    for fila in filas:
        if any(not fila[campo].strip() for campo in ("Nombre", "Requisitos", "Costo", "Plazo")):
            raise ValueError(f"Datos incompletos en {fila['ID_Tramite']}")
        if len(fila["Nombre"].strip()) > 1024:
            raise ValueError(f"Nombre demasiado largo en {fila['ID_Tramite']}")

    engine = create_engine(SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
    try:
        columna_nombre = next(c for c in inspect(engine).get_columns("tramites") if c["name"] == "nombre")
        longitud_actual = getattr(columna_nombre["type"], "length", None)
        ampliar_nombre = longitud_actual is not None and longitud_actual < max(len(f["Nombre"].strip()) for f in filas)
        with Session(engine) as sesion:
            actuales = {tramite.id_tramite: tramite for tramite in sesion.scalars(select(Tramite))}
            datos_respaldo = [t.to_dict() for t in actuales.values()]
            nuevos = []
            cambios = []
            for fila in filas:
                tramite = actuales.get(fila["ID_Tramite"])
                requisitos = [r.strip() for r in fila["Requisitos"].split("|") if r.strip()]
                if not requisitos or any(re.match(r"^\s*\d+[.)]", r) for r in requisitos):
                    raise ValueError(f"Requisitos sin limpiar en {fila['ID_Tramite']}")
                esperado = (fila["Nombre"].strip(), fila["Costo"].strip(), fila["Plazo"].strip(), requisitos)
                if tramite is None:
                    nuevos.append((fila["ID_Tramite"], esperado))
                elif (tramite.nombre, tramite.costo, tramite.plazo, [r.descripcion for r in tramite.requisitos]) != esperado:
                    cambios.append((tramite.id_tramite, esperado))

            resultado = {"registros_bd_antes": len(actuales), "registros_csv": len(filas),
                         "nuevos": len(nuevos), "actualizaciones": len(cambios),
                         "extras_bd": sorted(set(actuales) - set(codigos)),
                         "ampliar_nombre_a_1024": ampliar_nombre, "aplicado": False}
        if aplicar and (nuevos or cambios or ampliar_nombre):
            carpeta = BASE_DIR / "backups"
            carpeta.mkdir(exist_ok=True)
            respaldo = carpeta / f"respaldo_catalogo_{datetime.now():%Y%m%d_%H%M%S_%f}.json"
            with respaldo.open("x", encoding="utf-8") as archivo:
                json.dump(datos_respaldo, archivo, ensure_ascii=False, indent=2)
            # MySQL confirma DDL de forma implícita. Ampliar antes de abrir
            # la transacción de datos; nunca intentar reducir esta columna.
            if ampliar_nombre:
                if engine.dialect.name != "mysql":
                    raise RuntimeError("Amplía la columna nombre a 1024 antes de sincronizar.")
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE tramites MODIFY COLUMN nombre VARCHAR(1024) NOT NULL"))
            with Session(engine) as sesion, sesion.begin():
                actuales = {t.id_tramite: t for t in sesion.scalars(select(Tramite))}
                for codigo, (nombre, costo, plazo, requisitos) in nuevos + cambios:
                    tramite = actuales.get(codigo)
                    if tramite is None:
                        tramite = Tramite(id_tramite=codigo)
                        sesion.add(tramite)
                    tramite.nombre, tramite.costo, tramite.plazo = nombre, costo, plazo
                    tramite.requisitos = [Requisito(descripcion=r, orden=i) for i, r in enumerate(requisitos, 1)]
                sesion.flush()
                # Leer otra vez desde el servidor detecta truncamientos
                # incluso si MySQL está configurado sin modo estricto.
                sesion.expire_all()
                guardados = {t.id_tramite: t for t in sesion.scalars(select(Tramite).options(selectinload(Tramite.requisitos)))}
                for fila in filas:
                    t = guardados[fila["ID_Tramite"]]
                    esperado = (fila["Nombre"].strip(), fila["Costo"].strip(), fila["Plazo"].strip(), [r.strip() for r in fila["Requisitos"].split("|") if r.strip()])
                    if (t.nombre, t.costo, t.plazo, [r.descripcion for r in t.requisitos]) != esperado:
                        raise RuntimeError(f"La BD no conservó los datos íntegros de {t.id_tramite}; se revierte la carga.")
            resultado.update(aplicado=True, respaldo=str(respaldo))
        return resultado
    finally:
        engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aplicar", action="store_true")
    args = parser.parse_args()
    print(json.dumps(sincronizar(args.aplicar), ensure_ascii=False, indent=2))
