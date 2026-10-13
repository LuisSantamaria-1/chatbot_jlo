"""
seguridad.py
------------
Decorador de protección de rutas administrativas (RF06) y limitador en memoria
de intentos fallidos de autenticación (Rate Limiting para admin_login).
"""

import time
import threading
from functools import wraps
from collections import defaultdict
from flask import session, jsonify

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


def requiere_admin(f):
    """
    Exige que exista session["admin_user"] (seteado por /api/admin/login)
    antes de ejecutar la ruta. Sin esto, cualquiera con la URL puede crear,
    editar o borrar trámites sin haber iniciado sesión.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_user"):
            return jsonify({
                "status": "error",
                "mensaje": "No autorizado. Debes iniciar sesión como administrador."
            }), 401
        return f(*args, **kwargs)
    return wrapper
