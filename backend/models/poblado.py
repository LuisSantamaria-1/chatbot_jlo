import csv
import os
import secrets
from werkzeug.security import generate_password_hash
from backend.models.db import db
from backend.models.tramite import Tramite, Requisito
from backend.models.seguridad import Usuario, Rol
from config import CSV_TRAMITES_PATH

import re

def _limpiar_requisito(texto):
    """
    Limpia el texto de un requisito removiendo numeraciones iniciales
    para evitar redundancia visual en listas ordenadas.
    """
    if not texto:
        return ""
    return re.sub(r"^\s*\d+[\.\)]\s*", "", texto.strip()).strip()

def poblar_base_datos(csv_path=None):
    """Lee el CSV de trámites y los inserta o actualiza en la base de datos MySQL."""
    if csv_path is None:
        csv_path = CSV_TRAMITES_PATH

    if not os.path.exists(csv_path):
        print(f"Error: No se encontró el archivo CSV en {csv_path}")
        return

    with open(csv_path, mode="r", encoding="utf-8-sig") as f:
        lector = csv.DictReader(f)
        contador_nuevos = 0
        contador_actualizados = 0

        for fila in lector:
            id_tramite = (fila.get("ID") or fila.get("ID_Tramite") or fila.get("id_tramite") or "").strip()
            nombre = fila["Nombre"].strip()
            requisitos_raw = fila["Requisitos"].strip()
            costo = fila["Costo"].strip()
            plazo = fila["Plazo"].strip()

            tramite = Tramite.query.filter_by(id_tramite=id_tramite).first()

            if tramite is None:
                tramite = Tramite(id_tramite=id_tramite)
                db.session.add(tramite)
                contador_nuevos += 1
            else:
                tramite.requisitos.clear()
                contador_actualizados += 1

            tramite.nombre = nombre
            tramite.costo = costo
            tramite.plazo = plazo

            lista_requisitos = [r.strip() for r in requisitos_raw.split("|") if r.strip()]

            for orden, req_texto in enumerate(lista_requisitos, start=1):
                requisito = Requisito(
                    descripcion=_limpiar_requisito(req_texto),
                    orden=orden,
                )
                tramite.requisitos.append(requisito)

        db.session.commit()

    print(f"Poblado completo: {contador_nuevos} trámites nuevos, "
          f"{contador_actualizados} trámites actualizados.")

def inicializar_bd(csv_path=None):
    """Crea las tablas de seguridad y trámites, genera el admin por defecto y llena los trámites."""
    db.create_all()

    # 1. Crear el rol de administrador si no existe
    rol_admin = Rol.query.filter_by(nombre='Administrador').first()
    if not rol_admin:
        rol_admin = Rol(nombre='Administrador')
        db.session.add(rol_admin)
        db.session.commit()

    # 2. Crear el usuario administrador único por defecto si no existe
    admin_user = Usuario.query.filter_by(username='admin').first()
    if not admin_user:
        pwd_inicial = os.environ.get("ADMIN_INITIAL_PASSWORD")
        if not pwd_inicial:
            pwd_inicial = secrets.token_urlsafe(12)
            print(f"[SEGURIDAD] Contraseña inicial temporal generada para 'admin': {pwd_inicial}")
            print("[SEGURIDAD] Guárdela ahora; no se volverá a mostrar.")
        nuevo_admin = Usuario(
            username='admin',
            password_hash=generate_password_hash(pwd_inicial),
            rol_id=rol_admin.id
        )
        db.session.add(nuevo_admin)
        db.session.commit()
        print("Usuario administrador 'admin' creado con éxito.")

    # 3. Poblar los trámites
    poblar_base_datos(csv_path)
