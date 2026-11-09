"""
seguridad.py
------------
Decorador de protección de rutas administrativas (RF06) y limitador en memoria
de intentos fallidos de autenticación (Rate Limiting para admin_login).
"""

import time
import threading
import hashlib
import hmac
from functools import wraps
from collections import defaultdict
from flask import session, jsonify, redirect, url_for, request, current_app, abort
from sqlalchemy.exc import SQLAlchemyError
from backend.models import db, Usuario

MAX_INTENTOS_LOGIN = 5
VENTANA_BLOQUEO_SEGUNDOS = 300  # 5 minutos

_login_lock = threading.Lock()
# Clave: (usuario_normalizado, ip_normalizada) -> lista de timestamps (float)
_intentos_fallidos = defaultdict(list)


def reset_intentos_login():
    """Limpia el almacén de intentos fallidos en memoria (para pruebas y mantenimiento)."""
    with _login_lock:
        _intentos_fallidos.clear()


def verificar_bloqueo_login(usuario: str, ip: str):
    """
    Comprueba si la combinación (usuario, ip) se encuentra actualmente bloqueada.
    Retorna (esta_bloqueado, segundos_restantes).
    """
    ahora = time.time()
    clave = (str(usuario or "").strip().lower(), str(ip or "").strip())
    with _login_lock:
        timestamps = _intentos_fallidos[clave]
        validos = [t for t in timestamps if ahora - t < VENTANA_BLOQUEO_SEGUNDOS]
        _intentos_fallidos[clave] = validos

        if len(validos) >= MAX_INTENTOS_LOGIN:
            tiempo_antiguo = min(validos)
            segundos_restantes = int(VENTANA_BLOQUEO_SEGUNDOS - (ahora - tiempo_antiguo))
            return True, max(1, segundos_restantes)
        return False, 0


def registrar_intento_fallido(usuario: str, ip: str):
    """
    Registra un fallo de login. Retorna (bloqueado_ahora, segundos_restantes).
    """
    ahora = time.time()
    clave = (str(usuario or "").strip().lower(), str(ip or "").strip())
    with _login_lock:
        timestamps = _intentos_fallidos[clave]
        validos = [t for t in timestamps if ahora - t < VENTANA_BLOQUEO_SEGUNDOS]
        validos.append(ahora)
        _intentos_fallidos[clave] = validos

        if len(validos) >= MAX_INTENTOS_LOGIN:
            tiempo_antiguo = min(validos)
            segundos_restantes = int(VENTANA_BLOQUEO_SEGUNDOS - (ahora - tiempo_antiguo))
            return True, max(1, segundos_restantes)
        return False, 0


def registrar_login_exitoso(usuario: str, ip: str):
    """Reinicia el contador de intentos fallidos al completarse un login exitoso."""
    clave = (str(usuario or "").strip().lower(), str(ip or "").strip())
    with _login_lock:
        _intentos_fallidos.pop(clave, None)


def firma_credenciales(usuario):
    """Invalida sesiones al cambiar la contraseña, sin exponer su hash en la cookie."""
    clave = current_app.secret_key
    if isinstance(clave, str):
        clave = clave.encode("utf-8")
    return hmac.new(clave, usuario.password_hash.encode("utf-8"), hashlib.sha256).hexdigest()


def es_administrador(usuario):
    return bool(usuario and usuario.rol and usuario.rol.nombre.strip().casefold() == "administrador")


def usuario_admin_actual():
    """Comprueba la sesión firmada y los permisos vigentes en cada petición."""
    identificador = session.get("admin_user_id")
    if type(identificador) is int:
        usuario = db.session.get(Usuario, identificador)
        firma = session.get("admin_auth", "")
        if (es_administrador(usuario) and usuario.username == session.get("admin_user")
                and isinstance(firma, str) and hmac.compare_digest(firma, firma_credenciales(usuario))):
            return usuario
    for clave in ("admin_user", "admin_user_id", "admin_auth"):
        session.pop(clave, None)
    return None


def requiere_admin(f):
    """Protege tanto el HTML del panel como las operaciones administrativas."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            usuario = usuario_admin_actual()
        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.exception("No se pudo validar la sesión administrativa.")
            if not request.path.startswith("/api/"):
                abort(503)
            return jsonify({"status": "error", "mensaje": "Servicio no disponible. Intenta nuevamente más tarde."}), 503
        if usuario is None:
            if not request.path.startswith("/api/"):
                return redirect(url_for("admin.admin_login_page"))
            return jsonify({
                "status": "error",
                "mensaje": "No autorizado. Debes iniciar sesión como administrador."
            }), 401
        return f(*args, **kwargs)
    return wrapper
