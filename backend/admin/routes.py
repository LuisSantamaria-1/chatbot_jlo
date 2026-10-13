"""
routes.py
---------
Endpoints RESTful del Módulo Administrativo (RF06) y renderizado del panel web.
"""

import logging
import re
from flask import Blueprint, request, jsonify, render_template, session
from werkzeug.security import check_password_hash
from backend.models import db, Tramite, Requisito, Usuario, ConversacionLog
from backend.admin.seguridad import (
    requiere_admin,
    verificar_bloqueo_login,
    registrar_intento_fallido,
    registrar_login_exitoso,
)

logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin", methods=["GET"])
def admin_page():
    """
    Ruta del Panel Administrativo de Trámites.
    """
    return render_template("admin.html")


@admin_bp.route("/api/admin/login", methods=["POST"])
def admin_login():
    """
    Endpoint de autenticación para el panel administrativo.
    Valida exclusivamente contra la base de datos (tabla usuarios).
    Aplica límite de intentos fallidos (Rate Limiting en memoria).
    """
    try:
        data = request.get_json(silent=True) or {}
        usuario = str(data.get("usuario") or data.get("username") or "").strip()
        password = str(data.get("password") or "").strip()
        ip = request.remote_addr or "127.0.0.1"

        if usuario:
            bloqueado, restante = verificar_bloqueo_login(usuario, ip)
            if bloqueado:
                logger.warning(f"Acceso bloqueado por exceso de intentos para usuario '{usuario}'.")
                resp = jsonify({
                    "status": "error",
                    "mensaje": "Demasiados intentos fallidos. Intenta nuevamente más tarde."
                })
                resp.status_code = 429
                resp.headers["Retry-After"] = str(restante)
                return resp

        if not usuario or not password:
            return jsonify({
                "status": "error",
                "mensaje": "Usuario y contraseña requeridos"
            }), 401

        # Validar exclusivamente contra la base de datos
        if Usuario is not None:
            try:
                usuario_db = Usuario.query.filter_by(username=usuario).first()
                if usuario_db and check_password_hash(usuario_db.password_hash, password):
                    registrar_login_exitoso(usuario, ip)
                    session.permanent = True
                    session["admin_user"] = usuario_db.username
                    return jsonify({
                        "status": "success",
                        "mensaje": "Autenticación exitosa",
                        "username": usuario_db.username
                    }), 200
            except Exception as ex_db:
                logger.error(f"Error consultando tabla Usuario en login: {ex_db}")
                return jsonify({
                    "status": "error",
                    "mensaje": "Servicio no disponible. Intenta nuevamente más tarde."
                }), 503

        registrar_intento_fallido(usuario, ip)
        return jsonify({
            "status": "error",
            "mensaje": "Usuario o contraseña incorrectos"
        }), 401

    except Exception as e:
        logger.error(f"Error en POST /api/admin/login: {e}")
        return jsonify({
            "status": "error",
            "mensaje": "Ocurrió un error interno. Intenta nuevamente más tarde."
        }), 500


@admin_bp.route("/api/admin/logout", methods=["POST"])
def admin_logout():
    """
    Cierra la sesión administrativa limpiando las variables de sesión.
    Acepta peticiones con o sin sesión activa de forma idempotente.
    """
    session.clear()
    return jsonify({
        "status": "success",
        "mensaje": "Sesión cerrada correctamente"
    }), 200


@admin_bp.route("/api/admin/tramites", methods=["GET"])
@requiere_admin
def admin_listar_tramites():
    """
    RF06: Devuelve todos los trámites registrados con sus requisitos y costos.
    """
    try:
        tramites = Tramite.query.order_by(Tramite.id.asc()).all()
        resultado = []
        for t in tramites:
            resultado.append({
                "id": t.id,
                "id_tramite": t.id_tramite,
                "nombre": t.nombre,
                "costo": t.costo if t.costo else "Gratuito",
                "plazo": t.plazo if t.plazo else "Inmediato",
                "requisitos": [r.descripcion for r in t.requisitos],
            })
        return jsonify({
            "status": "success",
            "total": len(resultado),
            "tramites": resultado
        }), 200
    except Exception as e:
        logger.error(f"Error en GET /api/admin/tramites: {e}")
        return jsonify({
            "status": "error",
            "mensaje": "Ocurrió un error interno. Intenta nuevamente más tarde."
        }), 500


@admin_bp.route("/api/admin/tramites", methods=["POST"])
@requiere_admin
def admin_crear_tramite():
    """
    RF06: Crea un nuevo trámite con validaciones estrictas de formato y requisitos.
    """
    try:
        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            return jsonify({
                "status": "error",
                "mensaje": "Se requiere un cuerpo JSON válido con los datos del trámite."
            }), 400

        id_tramite = str(data.get("id_tramite", "")).strip()
        nombre = str(data.get("nombre", "")).strip()
        costo = str(data.get("costo", "")).strip()
        plazo = str(data.get("plazo", "")).strip()
        requisitos = data.get("requisitos", [])

        if not id_tramite:
            return jsonify({
                "status": "error",
                "mensaje": "El código del trámite (id_tramite) es obligatorio."
            }), 400

        if not re.match(r"^T_\d{3}$", id_tramite):
            return jsonify({
                "status": "error",
                "mensaje": "El código del trámite debe cumplir con el formato T_XXX (ejemplo: T_001)."
            }), 400

        if len(id_tramite) > 20:
            return jsonify({
                "status": "error",
                "mensaje": "El código del trámite no puede exceder los 20 caracteres."
            }), 400

        if not nombre:
            return jsonify({
                "status": "error",
                "mensaje": "El nombre del trámite es obligatorio."
            }), 400

        if len(nombre) > 255:
            return jsonify({
                "status": "error",
                "mensaje": "El nombre del trámite no puede exceder los 255 caracteres."
            }), 400

        if not isinstance(requisitos, list):
            return jsonify({
                "status": "error",
                "mensaje": "El campo 'requisitos' debe ser una lista."
            }), 400

        reqs_limpios = [str(r).strip() for r in requisitos if str(r).strip()]
        if not reqs_limpios:
            return jsonify({
                "status": "error",
                "mensaje": "El trámite debe contener al menos un requisito no vacío."
            }), 400

        tramite_existente = Tramite.query.filter_by(id_tramite=id_tramite).first()
        if tramite_existente:
            return jsonify({
                "status": "error",
                "mensaje": f"El código de trámite '{id_tramite}' ya se encuentra registrado."
            }), 409

        nuevo_tramite = Tramite(
            id_tramite=id_tramite,
            nombre=nombre,
            costo=costo if costo else "No especificado",
            plazo=plazo if plazo else "No especificado"
        )

        for orden, desc_str in enumerate(reqs_limpios, start=1):
            nuevo_tramite.requisitos.append(
                Requisito(descripcion=desc_str, orden=orden)
            )

        db.session.add(nuevo_tramite)
        db.session.commit()

        return jsonify({
            "status": "success",
            "mensaje": f"Trámite '{nuevo_tramite.nombre}' registrado con éxito.",
            "tramite": {
                "id": nuevo_tramite.id,
                "id_tramite": nuevo_tramite.id_tramite,
                "nombre": nuevo_tramite.nombre,
                "costo": nuevo_tramite.costo,
                "plazo": nuevo_tramite.plazo,
                "requisitos": [r.descripcion for r in nuevo_tramite.requisitos]
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error en POST /api/admin/tramites: {e}")
        return jsonify({
            "status": "error",
            "mensaje": "Ocurrió un error interno. Intenta nuevamente más tarde."
        }), 500


@admin_bp.route("/api/admin/tramites/<id>", methods=["PUT"])
@requiere_admin
def admin_actualizar_tramite(id):
    """
    RF06: Actualiza los datos de un trámite existente con validaciones de integridad.
    """
    try:
        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            return jsonify({
                "status": "error",
                "mensaje": "Se requiere un cuerpo JSON válido con los datos a actualizar."
            }), 400

        tramite = None
        if str(id).isdigit():
            tramite = Tramite.query.get(int(id))
        if not tramite:
            tramite = Tramite.query.filter_by(id_tramite=str(id).strip()).first()

        if not tramite:
            return jsonify({
                "status": "error",
                "mensaje": f"No se encontró el trámite con identificador '{id}'."
            }), 404

        if "id_tramite" in data:
            nuevo_codigo = str(data["id_tramite"]).strip()
            if not nuevo_codigo:
                return jsonify({
                    "status": "error",
                    "mensaje": "El código del trámite no puede estar vacío."
                }), 400
            if not re.match(r"^T_\d{3}$", nuevo_codigo):
                return jsonify({
                    "status": "error",
                    "mensaje": "El código del trámite debe cumplir con el formato T_XXX (ejemplo: T_001)."
                }), 400
            if len(nuevo_codigo) > 20:
                return jsonify({
                    "status": "error",
                    "mensaje": "El código del trámite no puede exceder los 20 caracteres."
                }), 400
            if nuevo_codigo != tramite.id_tramite:
                colision = Tramite.query.filter_by(id_tramite=nuevo_codigo).first()
                if colision and colision.id != tramite.id:
                    return jsonify({
                        "status": "error",
                        "mensaje": f"El código '{nuevo_codigo}' ya está registrado en otro trámite."
                    }), 409
                tramite.id_tramite = nuevo_codigo

        if "nombre" in data:
            nombre = str(data["nombre"]).strip()
            if not nombre:
                return jsonify({
                    "status": "error",
                    "mensaje": "El nombre del trámite no puede estar vacío."
                }), 400
            if len(nombre) > 255:
                return jsonify({
                    "status": "error",
                    "mensaje": "El nombre del trámite no puede exceder los 255 caracteres."
                }), 400
            tramite.nombre = nombre

        if "costo" in data:
            costo = str(data["costo"]).strip()
            tramite.costo = costo if costo else "No especificado"

        if "plazo" in data:
            plazo = str(data["plazo"]).strip()
            tramite.plazo = plazo if plazo else "No especificado"

        if "requisitos" in data:
            if not isinstance(data["requisitos"], list):
                return jsonify({
                    "status": "error",
                    "mensaje": "El campo 'requisitos' debe ser una lista."
                }), 400
            reqs_limpios = [str(desc).strip() for desc in data["requisitos"] if str(desc).strip()]
            if not reqs_limpios:
                return jsonify({
                    "status": "error",
                    "mensaje": "La lista de requisitos no puede quedar vacía. Se mantienen los requisitos existentes."
                }), 400
            tramite.requisitos.clear()
            for orden, desc_str in enumerate(reqs_limpios, start=1):
                tramite.requisitos.append(
                    Requisito(descripcion=desc_str, orden=orden)
                )

        db.session.commit()

        return jsonify({
            "status": "success",
            "mensaje": f"Trámite '{tramite.nombre}' actualizado con éxito.",
            "tramite": {
                "id": tramite.id,
                "id_tramite": tramite.id_tramite,
                "nombre": tramite.nombre,
                "costo": tramite.costo,
                "plazo": tramite.plazo,
                "requisitos": [r.descripcion for r in tramite.requisitos]
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error en PUT /api/admin/tramites/{id}: {e}")
        return jsonify({
            "status": "error",
            "mensaje": "Ocurrió un error interno. Intenta nuevamente más tarde."
        }), 500


@admin_bp.route("/api/admin/tramites/<id>", methods=["DELETE"])
@requiere_admin
def admin_eliminar_tramite(id):
    """
    RF06: Elimina un trámite de la base de datos.
    """
    try:
        tramite = None
        if str(id).isdigit():
            tramite = Tramite.query.get(int(id))
        if not tramite:
            tramite = Tramite.query.filter_by(id_tramite=str(id).strip()).first()

        if not tramite:
            return jsonify({
                "status": "error",
                "mensaje": f"No se encontró el trámite con identificador '{id}'."
            }), 404

        nombre_tramite = tramite.nombre
        id_tramite = tramite.id_tramite

        db.session.delete(tramite)
        db.session.commit()

        return jsonify({
            "status": "success",
            "mensaje": f"Trámite '{nombre_tramite}' ({id_tramite}) y sus requisitos asociados fueron eliminados correctamente."
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error en DELETE /api/admin/tramites/{id}: {e}")
        return jsonify({
            "status": "error",
            "mensaje": "Ocurrió un error interno. Intenta nuevamente más tarde."
        }), 500


@admin_bp.route("/api/admin/conversaciones", methods=["GET"])
@requiere_admin
def admin_listar_conversaciones():
    """
    Lista el historial de conversaciones registradas con paginación (RF08).
    Parámetros de consulta:
        page (int, default=1): Número de página solicitada.
        limit (int, default=20, máx=100): Cantidad de registros por página.
    """
    try:
        page = max(1, request.args.get("page", 1, type=int))
        limit = min(100, max(1, request.args.get("limit", 20, type=int)))

        query = ConversacionLog.query.order_by(ConversacionLog.id.desc())
        total = query.count()
        paginacion = query.paginate(page=page, per_page=limit, error_out=False)

        return jsonify({
            "status": "success",
            "total": total,
            "page": page,
            "limit": limit,
            "paginas": paginacion.pages,
            "conversaciones": [c.to_dict() for c in paginacion.items],
        }), 200

    except Exception as e:
        logger.error(f"Error en GET /api/admin/conversaciones: {e}")
        return jsonify({
            "status": "error",
            "mensaje": "Ocurrió un error interno. Intenta nuevamente más tarde."
        }), 500
