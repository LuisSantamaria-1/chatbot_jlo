#!/usr/bin/env python
"""
scripts/reset_admin_password.py
--------------------------------
Script administrativo seguro para restablecer la contraseña del usuario 'admin'
en la base de datos municipal_db y eliminar el usuario duplicado 'admin_jlo'.

Uso interactivo:
    python scripts/reset_admin_password.py
Uso desatendido / CI:
    ADMIN_NEW_PASSWORD="nueva_clave_secreta" python scripts/reset_admin_password.py
"""

import os
import sys
import getpass

# Agregar directorio raíz al PYTHONPATH
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from app import app
from backend.models import db, Usuario, Rol
from werkzeug.security import generate_password_hash


def reset_admin_password():
    with app.app_context():
        # 1. Eliminar usuario duplicado 'admin_jlo' si existe
        admin_jlo = Usuario.query.filter_by(username="admin_jlo").first()
        if admin_jlo:
            db.session.delete(admin_jlo)
            db.session.commit()
            print("[OK] Usuario duplicado 'admin_jlo' eliminado correctamente de la base de datos.")

        # 2. Obtener nueva contraseña de forma segura
        env_password = os.environ.get("ADMIN_NEW_PASSWORD")
        if env_password:
            nueva_pwd = env_password.strip()
        else:
            nueva_pwd = getpass.getpass("Ingrese la nueva contraseña para 'admin': ").strip()
            confirmacion = getpass.getpass("Confirme la nueva contraseña: ").strip()
            if nueva_pwd != confirmacion:
                print("[ERROR] Las contraseñas no coinciden. Operación abortada.")
                sys.exit(1)

        if not nueva_pwd or len(nueva_pwd) < 8:
            print("[ERROR] La contraseña debe tener al menos 8 caracteres. Operación abortada.")
            sys.exit(1)

        # 3. Localizar o crear usuario 'admin'
        admin = Usuario.query.filter_by(username="admin").first()
        if not admin:
            rol_admin = Rol.query.filter_by(nombre="Administrador").first()
            if not rol_admin:
                rol_admin = Rol(nombre="Administrador")
                db.session.add(rol_admin)
                db.session.commit()
            admin = Usuario(
                username="admin",
                password_hash=generate_password_hash(nueva_pwd),
                rol_id=rol_admin.id
            )
            db.session.add(admin)
        else:
            admin.password_hash = generate_password_hash(nueva_pwd)

        db.session.commit()
        print("[ÉXITO] Contraseña del usuario 'admin' actualizada exitosamente en la base de datos.")
        print("[SEGURIDAD] La contraseña ha sido cifrada con el algoritmo seguro scrypt.")


if __name__ == "__main__":
    reset_admin_password()
