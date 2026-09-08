import os
import sys
import unicodedata
import joblib
import numpy as np
from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS

# Requisito Funcional RF04: Umbral de confianza mínimo
UMBRAL_CONFIANZA = 0.70

# Importar modelos y base de datos desde database.py existente
try:
    from database import db, Tramite, Requisito, Usuario, Rol, DB_PATH, check_password_hash
except ImportError:
    from database import db, Tramite, Requisito, Usuario, Rol, check_password_hash
    DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "municipal.db")


# ---------------------------------------------------------------------------
# Función de preprocesamiento requerida para deserializar el pipeline TF-IDF
# ---------------------------------------------------------------------------
def preprocesar_texto(texto):
    """
    Normaliza el texto para coincidir con la función de entrenamiento:
    minúsculas y eliminación de acentos/tildes.
    """
    if texto is None:
        return ""
    texto = str(texto).lower().strip()
    texto_normalizado = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto_normalizado if unicodedata.category(c) != "Mn")


# Registrar la función en el módulo principal para compatibilidad con joblib/pickle
sys.modules["__main__"].preprocesar_texto = preprocesar_texto

PALABRAS_CLAVE_COSTO = {"costo", "cuanto", "cuánto", "cuesta", "precio", "pago", "tasa", "monto", "valor", "arancel"}
PALABRAS_CLAVE_PLAZO = {"plazo", "dias", "días", "tiempo", "demora", "tarda", "duracion", "duración", "cuando", "cuándo"}

def detectar_subintencion_directa(texto_preprocesado):
    """
    Interceta palabras clave directas en la consulta.
    """
    if any(palabra in texto_preprocesado for palabra in PALABRAS_CLAVE_PLAZO):
        return "plazo"
    if any(palabra in texto_preprocesado for palabra in PALABRAS_CLAVE_COSTO):
        return "costo"
    return None


# ---------------------------------------------------------------------------
# Inicialización de la aplicación Flask
# ---------------------------------------------------------------------------
app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "cambia-esta-clave-por-una-generada-con-os-urandom-24-en-produccion",
)

app.config.update(
    SESSION_COOKIE_NAME="mdjlo_session",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,
    PERMANENT_SESSION_LIFETIME=1800,
)

ORIGENES_PERMITIDOS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CORS(
    app,
    resources={r"/api/*": {"origins": ORIGENES_PERMITIDOS}},
    supports_credentials=True,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
)

# Configuración de SQLAlchemy (acepta SQLite local o MySQL vía env)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", f"sqlite:///{DB_PATH}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

try:
    db.init_app(app)
except Exception:
    pass


# ---------------------------------------------------------------------------
# Carga del modelo NLP (TF-IDF)
# ---------------------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "modelo_intenciones.joblib")

if not os.path.exists(MODEL_PATH):
    rutas_alternativas = [
        os.path.join(BASE_DIR, "dataset", "para ejecutar", "modelo_intenciones.joblib"),
        os.path.join(BASE_DIR, "..", "dataset", "para ejecutar", "modelo_intenciones.joblib"),
    ]
    for ruta in rutas_alternativas:
        if os.path.exists(ruta):
            MODEL_PATH = ruta
            break

try:
    modelo_nlp = joblib.load(MODEL_PATH)
    app.logger.info(f"Modelo NLP cargado correctamente desde: {MODEL_PATH}")
except Exception as e:
    modelo_nlp = None
    app.logger.error(f"Error al cargar el modelo NLP ({MODEL_PATH}): {e}")

INTENTS_SEGUIMIENTO = {"consultar_costo", "consultar_plazo"}


# ---------------------------------------------------------------------------
# Inferencia de intención + confianza con el modelo TF-IDF
# ---------------------------------------------------------------------------
def predecir_intencion(texto_consulta):
    if hasattr(modelo_nlp, "decision_function"):
        scores = modelo_nlp.decision_function([texto_consulta])[0]
        T = 0.28  # temperatura de calibración del margen SVM
        exp_scores = np.exp((scores - np.max(scores)) / T)
        probabilidades = exp_scores / np.sum(exp_scores)
        max_idx = int(np.argmax(probabilidades))
        confianza = float(probabilidades[max_idx])
        intent_predicho = str(modelo_nlp.classes_[max_idx])
    elif hasattr(modelo_nlp, "predict_proba"):
        probs = modelo_nlp.predict_proba([texto_consulta])[0]
        max_idx = int(np.argmax(probs))
        confianza = float(probs[max_idx])
        intent_predicho = str(modelo_nlp.classes_[max_idx])
    else:
        intent_predicho = str(modelo_nlp.predict([texto_consulta])[0])
        confianza = 1.0
    return intent_predicho, confianza


# ---------------------------------------------------------------------------
# Rutas Principales: Interfaz Web
# ---------------------------------------------------------------------------
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@app.route("/admin", methods=["GET"])
def admin_page():
    """
    Ruta del Panel Administrativo de Trámites.
    """
    return render_template("admin.html")


# ---------------------------------------------------------------------------
# Endpoint de Chat (con manejo de contexto / diálogo por pasos)
# ---------------------------------------------------------------------------
@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            return jsonify({
                "status": "error",
                "mensaje": "No se recibió un cuerpo JSON válido con la llave 'mensaje'."
            }), 400

        mensaje = data.get("mensaje")

        if not mensaje or not isinstance(mensaje, str) or not mensaje.strip():
            return jsonify({
                "status": "fallback",
                "mensaje": "Por favor, escribe una pregunta o consulta sobre el trámite municipal que deseas realizar."
            }), 400

        if modelo_nlp is None:
            return jsonify({
                "status": "error",
                "mensaje": "El modelo de procesamiento de lenguaje natural no está disponible en el servidor."
            }), 503

        texto_consulta = mensaje.strip()
        intent_predicho, confianza = predecir_intencion(texto_consulta)

        app.logger.info(
            f"Query: '{texto_consulta}' | Intent: '{intent_predicho}' | "
            f"Confianza: {confianza:.4f} | tramite_actual en sesión: {session.get('tramite_actual')}"
        )

        # --- Caso 1: saludo -----------------------------------------------
        if intent_predicho == "saludo":
            session.pop("tramite_actual", None)
            return jsonify({
                "status": "saludo",
                "intent": "saludo",
                "confianza": round(confianza, 4),
                "mensaje": "¡Hola! 👋 Soy Leonardito, el asistente virtual de la Municipalidad Distrital de José Leonardo Ortiz. ¿Sobre qué trámite municipal deseas consultar?"
            }), 200

        # --- Caso 1b: charla casual (small talk) ---------------------------
        if intent_predicho == "charla_casual":
            return jsonify({
                "status": "charla_casual",
                "intent": "charla_casual",
                "confianza": round(confianza, 4),
                "mensaje": "¡Todo muy bien por aquí! 🤖 Aunque me encantaría charlar, mi sistema está configurado exclusivamente para ayudarte con los trámites y licencias del TUPA. ¿Tienes alguna consulta sobre eso?"
            }), 200

        # --- Caso 2: fuera de dominio o confianza insuficiente (RF04) ------
        if intent_predicho == "fuera_de_dominio" or confianza < UMBRAL_CONFIANZA:
            return jsonify({
                "status": "fallback",
                "intent": intent_predicho,
                "confianza": round(confianza, 4),
                "mensaje": "Solo puedo orientarte sobre los trámites y procedimientos administrativos del TUPA de la Municipalidad Distrital de José Leonardo Ortiz (licencias comerciales, cambio de giro, duplicados, acceso a la información, etc.). Por favor, formula una consulta relacionada a trámites municipales."
            }), 200

        # --- Caso 3: pregunta de seguimiento (costo / plazo) ---------------
        if intent_predicho in INTENTS_SEGUIMIENTO:
            id_tramite_actual = session.get("tramite_actual")

            if not id_tramite_actual:
                return jsonify({
                    "status": "fallback",
                    "intent": intent_predicho,
                    "confianza": round(confianza, 4),
                    "mensaje": "Con gusto te indico eso, pero primero cuéntame: ¿qué trámite municipal deseas realizar?"
                }), 200

            tramite = Tramite.query.filter_by(id_tramite=id_tramite_actual).first()

            if not tramite:
                session.pop("tramite_actual", None)
                return jsonify({
                    "status": "fallback",
                    "intent": intent_predicho,
                    "confianza": round(confianza, 4),
                    "mensaje": "No logré recuperar el trámite del que hablábamos. ¿Podrías indicarme nuevamente qué trámite municipal deseas realizar?"
                }), 200

            if intent_predicho == "consultar_costo":
                mensaje_resp = f"El costo del trámite \"{tramite.nombre}\" es: {tramite.costo}."
            else:  # consultar_plazo
                mensaje_resp = f"El plazo de atención del trámite \"{tramite.nombre}\" es: {tramite.plazo}."

            return jsonify({
                "status": "success",
                "intent": intent_predicho,
                "confianza": round(confianza, 4),
                "id_tramite": tramite.id_tramite,
                "nombre": tramite.nombre,
                "costo": tramite.costo if intent_predicho == "consultar_costo" else None,
                "plazo": tramite.plazo if intent_predicho == "consultar_plazo" else None,
                "datosTramite": {
                    "id_tramite": tramite.id_tramite,
                    "nombre": tramite.nombre,
                    "costo": tramite.costo if intent_predicho == "consultar_costo" else None,
                    "plazo": tramite.plazo if intent_predicho == "consultar_plazo" else None,
                    "requisitos": [r.descripcion for r in tramite.requisitos]
                },
                "mensaje": mensaje_resp,
            }), 200

        # --- Caso 4: trámite específico detectado (T_001, T_002, ...) ------
        tramite = Tramite.query.filter_by(id_tramite=str(intent_predicho).strip()).first()

        if not tramite:
            return jsonify({
                "status": "fallback",
                "intent": intent_predicho,
                "confianza": round(confianza, 4),
                "mensaje": "No encontré información detallada para el trámite correspondiente a tu consulta. Por favor, intenta reformular tu pregunta o acércate a la mesa de partes.",
                "id_tramite_detectado": intent_predicho
            }), 200

        session["tramite_actual"] = tramite.id_tramite

        texto_normalizado = preprocesar_texto(texto_consulta)
        subintencion = detectar_subintencion_directa(texto_normalizado)

        if subintencion == "costo":
            mensaje_resp = (
                f"El costo para {tramite.nombre} es: {tramite.costo}. "
                "¿Te puedo ayudar con algo más?"
            )
            return jsonify({
                "status": "success",
                "id_tramite": tramite.id_tramite,
                "intent": intent_predicho,
                "confianza": round(confianza, 4),
                "nombre": tramite.nombre,
                "costo": tramite.costo,
                "datosTramite": {
                    "id_tramite": tramite.id_tramite,
                    "nombre": tramite.nombre,
                    "costo": tramite.costo,
                    "plazo": None,
                    "requisitos": [r.descripcion for r in tramite.requisitos]
                },
                "mensaje": mensaje_resp,
            }), 200

        if subintencion == "plazo":
            mensaje_resp = (
                f"El plazo de atención para {tramite.nombre} es: {tramite.plazo}. "
                "¿Te puedo ayudar con algo más?"
            )
            return jsonify({
                "status": "success",
                "id_tramite": tramite.id_tramite,
                "intent": intent_predicho,
                "confianza": round(confianza, 4),
                "nombre": tramite.nombre,
                "plazo": tramite.plazo,
                "datosTramite": {
                    "id_tramite": tramite.id_tramite,
                    "nombre": tramite.nombre,
                    "costo": None,
                    "plazo": tramite.plazo,
                    "requisitos": [r.descripcion for r in tramite.requisitos]
                },
                "mensaje": mensaje_resp,
            }), 200

        lista_requisitos = [r.descripcion for r in tramite.requisitos]
        requisitos_texto = "\n".join(f"- {r}" for r in lista_requisitos)

        mensaje_resp = (
            f"Para el trámite \"{tramite.nombre}\" necesitas:\n{requisitos_texto}\n\n"
            "¿Deseas conocer el costo o el plazo de atención de este trámite?"
        )

        return jsonify({
            "status": "success",
            "id_tramite": tramite.id_tramite,
            "intent": intent_predicho,
            "confianza": round(confianza, 4),
            "nombre": tramite.nombre,
            "requisitos": lista_requisitos,
            "datosTramite": {
                "id_tramite": tramite.id_tramite,
                "nombre": tramite.nombre,
                "costo": None,
                "plazo": None,
                "requisitos": lista_requisitos
            },
            "mensaje": mensaje_resp,
        }), 200

    except Exception as e:
        app.logger.error(f"Error en /api/chat: {e}")
        return jsonify({
            "status": "error",
            "mensaje": "Ocurrió un error inesperado al procesar tu solicitud. Intenta nuevamente más tarde."
        }), 500


# ---------------------------------------------------------------------------
# Módulo de Administración (Requisito Funcional RF06)
# Endpoints RESTful para gestionar Trámites y Requisitos
# ---------------------------------------------------------------------------

@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    """
    Endpoint de autenticación para el panel administrativo.
    """
    try:
        data = request.get_json(silent=True) or {}
        usuario = str(data.get("usuario") or data.get("username") or "").strip()
        password = str(data.get("password") or "").strip()

        if not usuario or not password:
            return jsonify({
                "status": "error",
                "mensaje": "Usuario y contraseña requeridos"
            }), 401

        # 1. Validar contra BD
        if Usuario is not None:
            try:
                usuario_db = Usuario.query.filter_by(username=usuario).first()
                if usuario_db and check_password_hash(usuario_db.password_hash, password):
                    session["admin_user"] = usuario_db.username
                    return jsonify({
                        "status": "success",
                        "mensaje": "Autenticación exitosa",
                        "username": usuario_db.username
                    }), 200
            except Exception as ex_db:
                app.logger.warning(f"Error consultando tabla Usuario: {ex_db}")

        # 2. Credenciales por defecto
        ADMIN_VALIDOS = {
            "admin": "admin123",
            "admin_jlo": "admin123",
            "municipalidad": "mdjlo2026"
        }

        if usuario in ADMIN_VALIDOS and ADMIN_VALIDOS[usuario] == password:
            session["admin_user"] = usuario
            return jsonify({
                "status": "success",
                "mensaje": "Autenticación exitosa",
                "username": usuario
            }), 200

        return jsonify({
            "status": "error",
            "mensaje": "Usuario o contraseña incorrectos"
        }), 401

    except Exception as e:
        app.logger.error(f"Error en POST /api/admin/login: {e}")
        return jsonify({
            "status": "error",
            "mensaje": f"Error interno: {str(e)}"
        }), 500


@app.route("/api/admin/tramites", methods=["GET"])
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
        app.logger.error(f"Error en GET /api/admin/tramites: {e}")
        return jsonify({
            "status": "error",
            "mensaje": f"Error al consultar trámites: {str(e)}"
        }), 500


@app.route("/api/admin/tramites", methods=["POST"])
def admin_crear_tramite():
    """
    RF06: Crea un nuevo trámite.
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

        if not nombre:
            return jsonify({
                "status": "error",
                "mensaje": "El nombre del trámite es obligatorio."
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
            costo=costo if costo else "Gratuito",
            plazo=plazo if plazo else "Inmediato"
        )

        if isinstance(requisitos, list):
            for orden, desc in enumerate(requisitos, start=1):
                desc_str = str(desc).strip()
                if desc_str:
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
        app.logger.error(f"Error en POST /api/admin/tramites: {e}")
        return jsonify({
            "status": "error",
            "mensaje": f"Error interno al crear el trámite: {str(e)}"
        }), 500


@app.route("/api/admin/tramites/<id>", methods=["PUT"])
def admin_actualizar_tramite(id):
    """
    RF06: Actualiza los datos de un trámite existente.
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
            if nuevo_codigo and nuevo_codigo != tramite.id_tramite:
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
            tramite.nombre = nombre

        if "costo" in data:
            costo = str(data["costo"]).strip()
            tramite.costo = costo if costo else "Gratuito"

        if "plazo" in data:
            plazo = str(data["plazo"]).strip()
            tramite.plazo = plazo if plazo else "Inmediato"

        if "requisitos" in data and isinstance(data["requisitos"], list):
            tramite.requisitos.clear()
            for orden, desc in enumerate(data["requisitos"], start=1):
                desc_str = str(desc).strip()
                if desc_str:
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
        app.logger.error(f"Error en PUT /api/admin/tramites/{id}: {e}")
        return jsonify({
            "status": "error",
            "mensaje": f"Error interno al actualizar el trámite: {str(e)}"
        }), 500


@app.route("/api/admin/tramites/<id>", methods=["DELETE"])
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
        app.logger.error(f"Error en DELETE /api/admin/tramites/{id}: {e}")
        return jsonify({
            "status": "error",
            "mensaje": f"Error interno al eliminar el trámite: {str(e)}"
        }), 500


# ---------------------------------------------------------------------------
# Ejecución del servidor
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host="localhost", port=puerto, debug=True)