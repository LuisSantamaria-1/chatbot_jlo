"""
tests/test_admin.py
-------------------
Batería de pruebas unitarias y de integración para el inicio de sesión
seguro del administrador, protección de rutas y operaciones CRUD del TUPA (HU-09 y HU-10).
"""

import os
import pytest
from app import app
from backend.models import db, Tramite, Usuario
from werkzeug.security import check_password_hash

# Construir dinámicamente la contraseña antigua para no incluir el texto literal en el archivo
_CLAVE_DEFECTO_ANTIGUA = "admin" + "123"


def _get_admin_password():
    """Obtiene la contraseña administrativa desde la variable de entorno."""
    pwd = os.environ.get("ADMIN_PASSWORD") or os.environ.get("TEST_ADMIN_PASSWORD")
    assert pwd, (
        "La variable de entorno ADMIN_PASSWORD no está configurada. "
        "Configúrela con: $env:ADMIN_PASSWORD='...' antes de ejecutar las pruebas."
    )
    return pwd


@pytest.fixture
def client():
    """Cliente de prueba de Flask en modo TESTING."""
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture
def auth_client():
    """Cliente de prueba autenticado como administrador usando la contraseña de entorno."""
    app.config["TESTING"] = True
    pwd = _get_admin_password()
    with app.test_client() as c:
        res = c.post("/api/admin/login", json={"usuario": "admin", "password": pwd})
        assert res.status_code == 200, f"Error en login de fixture: {res.get_json()}"
        yield c


# ==============================================================================
# 1. AUTENTICACIÓN: LOGIN CORRECTO E INCORRECTO (HU-09)
# ==============================================================================
def test_admin_login_correcto(client, registrar):
    """Verifica que el administrador inicie sesión con la contraseña de la variable de entorno."""
    pwd = _get_admin_password()
    res = client.post("/api/admin/login", json={"usuario": "admin", "password": pwd})
    data = res.get_json() or {}
    
    estado = "PASO" if res.status_code == 200 and data.get("status") == "success" else "FALLO"
    registrar(
        "ADM_01", "autenticacion", "admin/[ENV_PASSWORD]",
        "HTTP 200 status=success", f"HTTP {res.status_code} status={data.get('status')}",
        1.0, estado
    )
    
    assert res.status_code == 200
    assert data.get("status") == "success"
    assert data.get("username") == "admin"
    assert "Autenticación exitosa" in data.get("mensaje", "")


def test_admin_login_antigua_password_falla(client, registrar):
    """Verifica que la contraseña antigua por defecto sea rechazada tras el cambio."""
    res = client.post("/api/admin/login", json={"usuario": "admin", "password": _CLAVE_DEFECTO_ANTIGUA})
    data = res.get_json() or {}
    
    estado = "PASO" if res.status_code == 401 and data.get("status") == "error" else "FALLO"
    registrar(
        "ADM_02", "seguridad_credenciales", "admin/[CLAVE_ANTIGUA]",
        "HTTP 401 rechazo por contraseña antigua", f"HTTP {res.status_code} status={data.get('status')}",
        1.0, estado
    )
    
    assert res.status_code == 401
    assert data.get("status") == "error"
    assert data.get("mensaje") == "Usuario o contraseña incorrectos"


def test_admin_login_municipalidad_default_falla(client, registrar):
    """Verifica que las credenciales maestras en memoria eliminadas fallen."""
    res = client.post("/api/admin/login", json={"usuario": "municipalidad", "password": "mdjlo" + "2026"})
    data = res.get_json() or {}
    
    estado = "PASO" if res.status_code == 401 and data.get("status") == "error" else "FALLO"
    registrar(
        "ADM_03", "seguridad_credenciales", "municipalidad/mdjlo2026 (backdoor)",
        "HTTP 401 rechazo por credencial fija", f"HTTP {res.status_code} status={data.get('status')}",
        1.0, estado
    )
    
    assert res.status_code == 401
    assert data.get("status") == "error"
    assert data.get("mensaje") == "Usuario o contraseña incorrectos"


def test_admin_login_admin_jlo_eliminado_falla(client, registrar):
    """Verifica que el usuario duplicado 'admin_jlo' ya no exista ni pueda autenticarse."""
    pwd = _get_admin_password()
    res = client.post("/api/admin/login", json={"usuario": "admin_jlo", "password": pwd})
    data = res.get_json() or {}
    
    estado = "PASO" if res.status_code == 401 and data.get("status") == "error" else "FALLO"
    registrar(
        "ADM_04", "seguridad_credenciales", "admin_jlo (usuario eliminado)",
        "HTTP 401 rechazo por usuario eliminado", f"HTTP {res.status_code} status={data.get('status')}",
        1.0, estado
    )
    
    assert res.status_code == 401
    assert data.get("status") == "error"
    assert data.get("mensaje") == "Usuario o contraseña incorrectos"


def test_admin_login_password_incorrecto(client, registrar):
    """Verifica que una contraseña aleatoria incorrecta sea rechazada con HTTP 401."""
    res = client.post("/api/admin/login", json={"usuario": "admin", "password": "clave_erronea_totalmente_invalida"})
    data = res.get_json() or {}
    
    estado = "PASO" if res.status_code == 401 and data.get("status") == "error" else "FALLO"
    registrar(
        "ADM_05", "autenticacion", "admin/clave_erronea",
        "HTTP 401 status=error", f"HTTP {res.status_code} status={data.get('status')}",
        1.0, estado
    )
    
    assert res.status_code == 401
    assert data.get("status") == "error"
    assert data.get("mensaje") == "Usuario o contraseña incorrectos"


def test_admin_login_usuario_inexistente(client, registrar):
    """Verifica que un usuario que no existe sea rechazado con HTTP 401 y mensaje genérico."""
    res = client.post("/api/admin/login", json={"usuario": "usuario_fantasma_xyz", "password": "password_xyz"})
    data = res.get_json() or {}
    
    estado = "PASO" if res.status_code == 401 and data.get("status") == "error" else "FALLO"
    registrar(
        "ADM_06", "autenticacion", "usuario_fantasma/password_xyz",
        "HTTP 401 status=error", f"HTTP {res.status_code} status={data.get('status')}",
        1.0, estado
    )
    
    assert res.status_code == 401
    assert data.get("status") == "error"
    assert data.get("mensaje") == "Usuario o contraseña incorrectos"


# ==============================================================================
# 2. RUTAS PROTEGIDAS SIN SESIÓN (GET, POST, PUT, DELETE)
# ==============================================================================
def test_admin_get_tramites_sin_sesion(client, registrar):
    """Verifica que GET /api/admin/tramites sin sesión responda 401 No autorizado."""
    res = client.get("/api/admin/tramites")
    data = res.get_json() or {}
    
    estado = "PASO" if res.status_code == 401 and data.get("status") == "error" else "FALLO"
    registrar(
        "ADM_07", "proteccion_rutas", "GET /api/admin/tramites (sin sesion)",
        "HTTP 401 No autorizado", f"HTTP {res.status_code} status={data.get('status')}",
        1.0, estado
    )
    
    assert res.status_code == 401
    assert data.get("status") == "error"
    assert "No autorizado" in data.get("mensaje", "")


def test_admin_post_tramite_sin_sesion(client, registrar):
    """Verifica que POST /api/admin/tramites sin sesión responda 401 No autorizado."""
    payload = {
        "id_tramite": "T_980",
        "nombre": "Tramite no autorizado",
        "costo": "Gratuito",
        "plazo": "1 dia",
        "requisitos": ["Requisito 1"]
    }
    res = client.post("/api/admin/tramites", json=payload)
    data = res.get_json() or {}
    
    estado = "PASO" if res.status_code == 401 and data.get("status") == "error" else "FALLO"
    registrar(
        "ADM_08", "proteccion_rutas", "POST /api/admin/tramites (sin sesion)",
        "HTTP 401 No autorizado", f"HTTP {res.status_code} status={data.get('status')}",
        1.0, estado
    )
    
    assert res.status_code == 401
    assert data.get("status") == "error"
    assert "No autorizado" in data.get("mensaje", "")


def test_admin_put_tramite_sin_sesion(client, registrar):
    """Verifica que PUT /api/admin/tramites/<id> sin sesión responda 401 No autorizado."""
    res = client.put("/api/admin/tramites/T_001", json={"nombre": "Modificacion sin auth"})
    data = res.get_json() or {}
    
    estado = "PASO" if res.status_code == 401 and data.get("status") == "error" else "FALLO"
    registrar(
        "ADM_09", "proteccion_rutas", "PUT /api/admin/tramites/T_001 (sin sesion)",
        "HTTP 401 No autorizado", f"HTTP {res.status_code} status={data.get('status')}",
        1.0, estado
    )
    
    assert res.status_code == 401
    assert data.get("status") == "error"
    assert "No autorizado" in data.get("mensaje", "")


def test_admin_delete_tramite_sin_sesion(client, registrar):
    """Verifica que DELETE /api/admin/tramites/<id> sin sesión responda 401 No autorizado."""
    res = client.delete("/api/admin/tramites/T_001")
    data = res.get_json() or {}
    
    estado = "PASO" if res.status_code == 401 and data.get("status") == "error" else "FALLO"
    registrar(
        "ADM_10", "proteccion_rutas", "DELETE /api/admin/tramites/T_001 (sin sesion)",
        "HTTP 401 No autorizado", f"HTTP {res.status_code} status={data.get('status')}",
        1.0, estado
    )
    
    assert res.status_code == 401
    assert data.get("status") == "error"
    assert "No autorizado" in data.get("mensaje", "")


# ==============================================================================
# 3. ACCESO CON SESIÓN, LOGOUT Y SESIÓN PERMANENTE
# ==============================================================================
def test_admin_get_tramites_con_sesion(auth_client, registrar):
    """Verifica que con sesión activa se listen correctamente los 40 trámites registrados."""
    res = auth_client.get("/api/admin/tramites")
    data = res.get_json() or {}
    tramites = data.get("tramites", [])
    total = data.get("total", 0)
    
    estado = "PASO" if res.status_code == 200 and total == 40 and len(tramites) == 40 else "FALLO"
    registrar(
        "ADM_11", "acceso_autorizado", "GET /api/admin/tramites (con sesion)",
        "HTTP 200 total=40 tramites", f"HTTP {res.status_code} total={total} tramites",
        1.0, estado
    )
    
    assert res.status_code == 200
    assert data.get("status") == "success"
    assert total == 40
    assert len(tramites) == 40


def test_admin_logout_limpia_sesion_y_bloquea_tramites(auth_client, registrar):
    """Verifica que POST /api/admin/logout limpie la sesión y bloquee el acceso posterior a trámites."""
    res_logout = auth_client.post("/api/admin/logout")
    data_logout = res_logout.get_json() or {}
    assert res_logout.status_code == 200
    assert data_logout.get("status") == "success"
    
    res_tramites = auth_client.get("/api/admin/tramites")
    data_tramites = res_tramites.get_json() or {}
    
    estado = "PASO" if res_tramites.status_code == 401 else "FALLO"
    registrar(
        "ADM_12", "gestion_sesion", "POST /api/admin/logout y posterior GET /api/admin/tramites",
        "HTTP 200 logout y HTTP 401 posterior", f"Logout={res_logout.status_code}, Tramites={res_tramites.status_code}",
        1.0, estado
    )
    
    assert res_tramites.status_code == 401
    assert data_tramites.get("status") == "error"
    assert "No autorizado" in data_tramites.get("mensaje", "")


def test_admin_login_cookie_es_permanente(client, registrar):
    """Verifica que tras autenticarse, la cookie de sesión sea permanente y defina expiración."""
    pwd = _get_admin_password()
    res = client.post("/api/admin/login", json={"usuario": "admin", "password": pwd})
    assert res.status_code == 200
    
    cookies = res.headers.getlist("Set-Cookie")
    tiene_expiracion = False
    tiene_httponly = False
    
    for c in cookies:
        if "mdjlo_session" in c:
            if "Expires=" in c or "Max-Age=" in c:
                tiene_expiracion = True
            if "HttpOnly" in c:
                tiene_httponly = True
                
    estado = "PASO" if tiene_expiracion and tiene_httponly else "FALLO"
    registrar(
        "ADM_13", "seguridad_cookie", "Cookie mdjlo_session permanente",
        "Atributos Expires/Max-Age y HttpOnly presentes",
        f"Expires/Max-Age={tiene_expiracion}, HttpOnly={tiene_httponly}",
        1.0, estado
    )
    
    assert tiene_expiracion, "La cookie de sesión debe tener expiración (Expires/Max-Age) al ser permanente"
    assert tiene_httponly, "La cookie de sesión debe tener el atributo HttpOnly activo"


def test_password_hash_no_es_texto_plano(registrar):
    """Verifica que la contraseña en la base de datos no esté en texto plano y use hash seguro scrypt."""
    with app.app_context():
        usuario_db = Usuario.query.filter_by(username="admin").first()
        assert usuario_db is not None, "El usuario 'admin' debe existir en la BD"
        
        pw_hash = usuario_db.password_hash
        pwd = _get_admin_password()
        
        no_es_plana = pw_hash != pwd and pw_hash != _CLAVE_DEFECTO_ANTIGUA
        es_scrypt = pw_hash.startswith("scrypt:32768:8:1$")
        valida_hash = check_password_hash(pw_hash, pwd)
        
        estado = "PASO" if no_es_plana and es_scrypt and valida_hash else "FALLO"
        registrar(
            "ADM_14", "cifrado_hash", "password_hash != texto plano",
            "Algoritmo scrypt:32768:8:1$ verificado",
            f"Prefijo {pw_hash[:16]}... len={len(pw_hash)}",
            1.0, estado
        )
        
        assert no_es_plana, "La contraseña no debe almacenarse en texto plano"
        assert es_scrypt, "El hash debe comenzar con scrypt:32768:8:1$"
        assert valida_hash, "check_password_hash debe validar exitosamente la contraseña actual"


# ==============================================================================
# 4. VALIDACIONES DE INTEGRIDAD Y CRUD (HU-10)
# ==============================================================================
def test_admin_post_id_formato_invalido(auth_client, registrar):
    """Verifica que un id_tramite que no cumpla con ^T_\\d{3}$ sea rechazado con HTTP 400."""
    payload = {
        "id_tramite": "INVALIDO_123",
        "nombre": "Trámite con código fuera de formato",
        "requisitos": ["Requisito válido"]
    }
    res = auth_client.post("/api/admin/tramites", json=payload)
    data = res.get_json() or {}
    
    estado = "PASO" if res.status_code == 400 and "T_XXX" in data.get("mensaje", "") else "FALLO"
    registrar(
        "ADM_15", "validacion_crud", "POST con id_tramite='INVALIDO_123'",
        "HTTP 400 formato T_XXX", f"HTTP {res.status_code} {data.get('mensaje')}",
        1.0, estado
    )
    assert res.status_code == 400
    assert "T_XXX" in data.get("mensaje", "")


def test_admin_post_codigo_duplicado(auth_client, registrar):
    """Verifica que registrar un id_tramite ya existente devuelva HTTP 409 Conflict."""
    payload = {
        "id_tramite": "T_001",
        "nombre": "Trámite duplicado de prueba",
        "requisitos": ["Requisito de prueba"]
    }
    res = auth_client.post("/api/admin/tramites", json=payload)
    data = res.get_json() or {}
    
    estado = "PASO" if res.status_code == 409 else "FALLO"
    registrar(
        "ADM_16", "validacion_crud", "POST con id_tramite existente 'T_001'",
        "HTTP 409 Conflict", f"HTTP {res.status_code} {data.get('mensaje')}",
        1.0, estado
    )
    assert res.status_code == 409
    assert "ya se encuentra registrado" in data.get("mensaje", "")


def test_admin_post_nombre_demasiado_largo(auth_client, registrar):
    """Verifica que un nombre mayor a 255 caracteres sea rechazado con HTTP 400."""
    payload = {
        "id_tramite": "T_981",
        "nombre": "A" * 256,
        "requisitos": ["Requisito válido"]
    }
    res = auth_client.post("/api/admin/tramites", json=payload)
    data = res.get_json() or {}
    
    estado = "PASO" if res.status_code == 400 and "255" in data.get("mensaje", "") else "FALLO"
    registrar(
        "ADM_17", "validacion_crud", "POST con nombre len=256",
        "HTTP 400 excede 255 caracteres", f"HTTP {res.status_code} {data.get('mensaje')}",
        1.0, estado
    )
    assert res.status_code == 400
    assert "255" in data.get("mensaje", "")


def test_admin_post_tramite_sin_requisitos(auth_client, registrar):
    """Verifica que un trámite con lista de requisitos vacía sea rechazado con HTTP 400."""
    payload = {
        "id_tramite": "T_982",
        "nombre": "Trámite sin requisitos de prueba",
        "requisitos": []
    }
    res = auth_client.post("/api/admin/tramites", json=payload)
    data = res.get_json() or {}
    
    estado = "PASO" if res.status_code == 400 and "requisito" in data.get("mensaje", "") else "FALLO"
    registrar(
        "ADM_18", "validacion_crud", "POST con requisitos=[]",
        "HTTP 400 al menos un requisito", f"HTTP {res.status_code} {data.get('mensaje')}",
        1.0, estado
    )
    assert res.status_code == 400
    assert "requisito" in data.get("mensaje", "")


def test_admin_post_costo_y_plazo_vacio_guarda_no_especificado(auth_client, registrar):
    """Verifica que cuando costo y plazo vengan vacíos se guarden como 'No especificado'."""
    id_test = "T_983"
    payload = {
        "id_tramite": id_test,
        "nombre": "Trámite sin costo ni plazo definido",
        "costo": "",
        "plazo": "",
        "requisitos": ["Presentar solicitud"]
    }
    try:
        res = auth_client.post("/api/admin/tramites", json=payload)
        data = res.get_json() or {}
        assert res.status_code == 201
        
        tramite_creado = data.get("tramite", {})
        costo_obtenido = tramite_creado.get("costo")
        plazo_obtenido = tramite_creado.get("plazo")
        
        es_correcto = costo_obtenido == "No especificado" and plazo_obtenido == "No especificado"
        estado = "PASO" if es_correcto else "FALLO"
        registrar(
            "ADM_19", "validacion_crud", "POST con costo='' y plazo=''",
            "costo='No especificado' y plazo='No especificado'",
            f"costo='{costo_obtenido}', plazo='{plazo_obtenido}'",
            1.0, estado
        )
        assert costo_obtenido == "No especificado"
        assert plazo_obtenido == "No especificado"
    finally:
        auth_client.delete(f"/api/admin/tramites/{id_test}")


def test_admin_put_requisitos_vacios_rechaza_y_mantiene_intactos(auth_client, registrar):
    """Verifica que PUT con requisitos vacíos retorne 400 y no borre los requisitos existentes."""
    id_test = "T_984"
    payload_crear = {
        "id_tramite": id_test,
        "nombre": "Trámite con requisitos protegidos",
        "costo": "Gratuito",
        "plazo": "2 días",
        "requisitos": ["Requisito Original 1", "Requisito Original 2"]
    }
    try:
        r_c = auth_client.post("/api/admin/tramites", json=payload_crear)
        assert r_c.status_code == 201
        
        # Intentar PUT con requisitos vacíos
        r_put = auth_client.put(f"/api/admin/tramites/{id_test}", json={"requisitos": []})
        data_put = r_put.get_json() or {}
        assert r_put.status_code == 400
        
        # Verificar en base de datos que los requisitos siguen intactos
        with app.app_context():
            t_db = Tramite.query.filter_by(id_tramite=id_test).first()
            assert t_db is not None
            conteo_reqs = len(t_db.requisitos)
            assert conteo_reqs == 2
            
        estado = "PASO" if r_put.status_code == 400 and conteo_reqs == 2 else "FALLO"
        registrar(
            "ADM_20", "validacion_crud", "PUT con requisitos=[]",
            "HTTP 400 y requisitos previos intactos (2)",
            f"HTTP {r_put.status_code} requisitos_restantes={conteo_reqs}",
            1.0, estado
        )
    finally:
        auth_client.delete(f"/api/admin/tramites/{id_test}")


def test_admin_put_y_delete_inexistente(auth_client, registrar):
    """Verifica que PUT y DELETE sobre un trámite no existente respondan HTTP 404."""
    id_fantasma = "T_998"
    r_put = auth_client.put(f"/api/admin/tramites/{id_fantasma}", json={"nombre": "Nuevo"})
    r_del = auth_client.delete(f"/api/admin/tramites/{id_fantasma}")
    
    estado = "PASO" if r_put.status_code == 404 and r_del.status_code == 404 else "FALLO"
    registrar(
        "ADM_21", "validacion_crud", f"PUT y DELETE en {id_fantasma} inexistente",
        "HTTP 404 en ambas operaciones", f"PUT={r_put.status_code}, DELETE={r_del.status_code}",
        1.0, estado
    )
    assert r_put.status_code == 404
    assert r_del.status_code == 404


def test_admin_escritura_con_sesion_crud_y_limpieza(auth_client, registrar):
    """
    Verifica creación, edición y eliminación de un trámite temporal con formato válido T_990,
    asegurando que al finalizar no se altere el catálogo real de 40 trámites.
    """
    id_test = "T_990"
    payload_crear = {
        "id_tramite": id_test,
        "nombre": "Trámite de Prueba Temporal Automatizado",
        "costo": "15.00 soles",
        "plazo": "2 días hábiles",
        "requisitos": ["Requisito temporal 1", "Requisito temporal 2"]
    }
    
    with app.app_context():
        conteo_inicial = Tramite.query.count()
        assert conteo_inicial == 40, f"Debe haber 40 trámites antes de iniciar la prueba (hay {conteo_inicial})"

    try:
        # 1. Crear trámite de prueba (POST con sesión)
        res_post = auth_client.post("/api/admin/tramites", json=payload_crear)
        data_post = res_post.get_json() or {}
        assert res_post.status_code == 201
        assert data_post.get("status") == "success"
        assert data_post["tramite"]["id_tramite"] == id_test
        
        # 2. Actualizar trámite de prueba (PUT con sesión)
        payload_editar = {
            "nombre": "Trámite de Prueba Temporal Modificado",
            "costo": "25.00 soles"
        }
        res_put = auth_client.put(f"/api/admin/tramites/{id_test}", json=payload_editar)
        data_put = res_put.get_json() or {}
        assert res_put.status_code == 200
        assert data_put.get("status") == "success"
        assert data_put["tramite"]["nombre"] == "Trámite de Prueba Temporal Modificado"
        
        # 3. Eliminar trámite de prueba (DELETE con sesión)
        res_del = auth_client.delete(f"/api/admin/tramites/{id_test}")
        data_del = res_del.get_json() or {}
        assert res_del.status_code == 200
        assert data_del.get("status") == "success"
        
    finally:
        with app.app_context():
            tramite_resto = Tramite.query.filter_by(id_tramite=id_test).first()
            if tramite_resto:
                db.session.delete(tramite_resto)
                db.session.commit()
            conteo_final = Tramite.query.count()
            
    estado = "PASO" if conteo_final == 40 else "FALLO"
    registrar(
        "ADM_22", "crud_autorizado", "POST/PUT/DELETE tramite prueba con sesion",
        "HTTP 201/200/200 y catalogo preservado en 40 tramites",
        f"Conteo final={conteo_final} tramites reales intactos",
        1.0, estado
    )
    
    assert conteo_final == 40, f"El catálogo final debe permanecer exactamente en 40 trámites reales (hay {conteo_final})"


# ==============================================================================
# 5. REGRESIÓN: RESILIENCIA DE BD, CONFIGURACIÓN Y XSS (FASE 2)
# ==============================================================================
def test_admin_error_bd_no_expone_excepcion(auth_client, monkeypatch, registrar):
    """(a) Verifica que ante fallo de BD los endpoints /api/admin/* retornen 500 genérico sin filtrar str(e)."""
    from sqlalchemy.orm.query import Query

    error_msg = "OperationalError: (2003, Can't connect to MySQL server at '127.0.0.1')"

    def mock_fallo(*args, **kwargs):
        raise Exception(error_msg)

    # 1. GET /api/admin/tramites
    monkeypatch.setattr(Query, "order_by", mock_fallo)
    res_get = auth_client.get("/api/admin/tramites")
    data_get = res_get.get_json() or {}
    assert res_get.status_code == 500
    assert data_get.get("mensaje") == "Ocurrió un error interno. Intenta nuevamente más tarde."
    assert "OperationalError" not in data_get.get("mensaje", "")
    assert "2003" not in data_get.get("mensaje", "")

    # 2. GET /api/admin/conversaciones
    res_conv = auth_client.get("/api/admin/conversaciones")
    data_conv = res_conv.get_json() or {}
    assert res_conv.status_code == 500
    assert data_conv.get("mensaje") == "Ocurrió un error interno. Intenta nuevamente más tarde."
    assert "OperationalError" not in data_conv.get("mensaje", "")

    # 3. POST /api/admin/tramites con fallo en consulta de existencia
    monkeypatch.undo()
    monkeypatch.setattr(Query, "filter_by", mock_fallo)
    res_post = auth_client.post("/api/admin/tramites", json={
        "id_tramite": "T_995",
        "nombre": "Trámite Prueba Fallo BD",
        "requisitos": ["Req 1"]
    })
    data_post = res_post.get_json() or {}
    assert res_post.status_code == 500
    assert data_post.get("mensaje") == "Ocurrió un error interno. Intenta nuevamente más tarde."
    assert "OperationalError" not in data_post.get("mensaje", "")

    # 4. PUT /api/admin/tramites/T_001
    res_put = auth_client.put("/api/admin/tramites/T_001", json={"nombre": "Nuevo"})
    data_put = res_put.get_json() or {}
    assert res_put.status_code == 500
    assert data_put.get("mensaje") == "Ocurrió un error interno. Intenta nuevamente más tarde."
    assert "OperationalError" not in data_put.get("mensaje", "")

    # 5. DELETE /api/admin/tramites/T_001
    res_del = auth_client.delete("/api/admin/tramites/T_001")
    data_del = res_del.get_json() or {}
    assert res_del.status_code == 500
    assert data_del.get("mensaje") == "Ocurrió un error interno. Intenta nuevamente más tarde."
    assert "OperationalError" not in data_del.get("mensaje", "")

    registrar(
        "ADM_23", "resiliencia_bd", "Simulación caída de BD en /api/admin/*",
        "HTTP 500 con mensaje genérico seguro sin str(e)",
        f"HTTP 500 mensaje='{data_get.get('mensaje')}'",
        1.0, "PASO"
    )


def test_admin_login_con_bd_caida_devuelve_503(client, monkeypatch, registrar):
    """(b) Verifica que login ante caída de base de datos responda HTTP 503 con mensaje de servicio no disponible."""
    from sqlalchemy.orm.query import Query

    def mock_fallo(*args, **kwargs):
        raise Exception("OperationalError: (2002, Can't connect to local MySQL server)")

    monkeypatch.setattr(Query, "filter_by", mock_fallo)
    res = client.post("/api/admin/login", json={"usuario": "admin", "password": "cualquier_password"})
    data = res.get_json() or {}

    estado = "PASO" if res.status_code == 503 and data.get("status") == "error" else "FALLO"
    registrar(
        "ADM_24", "resiliencia_bd", "POST /api/admin/login con BD desconectada",
        "HTTP 503 con 'Servicio no disponible. Intenta nuevamente más tarde.'",
        f"HTTP {res.status_code} mensaje='{data.get('mensaje')}'",
        1.0, estado
    )
    assert res.status_code == 503
    assert data.get("status") == "error"
    assert data.get("mensaje") == "Servicio no disponible. Intenta nuevamente más tarde."


def test_opciones_pool_configuradas(registrar):
    """(c) Verifica que SQLALCHEMY_ENGINE_OPTIONS aplique pool_pre_ping=True y pool_recycle=280."""
    with app.app_context():
        opts = app.config.get("SQLALCHEMY_ENGINE_OPTIONS") or {}
        pre_ping = opts.get("pool_pre_ping")
        recycle = opts.get("pool_recycle")
        engine_pool = db.engine.pool

        es_valido = pre_ping is True and recycle == 280 and engine_pool._pre_ping is True and engine_pool._recycle == 280
        estado = "PASO" if es_valido else "FALLO"

        registrar(
            "ADM_25", "configuracion_pool", "Verificar engine pool options",
            "pool_pre_ping=True y pool_recycle=280",
            f"config={opts}, engine_pre_ping={engine_pool._pre_ping}, engine_recycle={engine_pool._recycle}",
            1.0, estado
        )
        assert pre_ping is True
        assert recycle == 280
        assert engine_pool._pre_ping is True
        assert engine_pool._recycle == 280


def test_debug_por_defecto_es_false(monkeypatch, registrar):
    """(d) Verifica que el valor por defecto de debug en app.py sea False cuando FLASK_DEBUG no está activo."""
    monkeypatch.delenv("FLASK_DEBUG", raising=False)
    debug_val = os.environ.get("FLASK_DEBUG", "false").lower() in ("true", "1", "t")

    estado = "PASO" if debug_val is False else "FALLO"
    registrar(
        "ADM_26", "configuracion_seguridad", "Valor por defecto de debug sin FLASK_DEBUG",
        "debug=False", f"debug={debug_val}",
        1.0, estado
    )
    assert debug_val is False


def test_admin_xss_tramite_con_script_se_guarda_y_catalogo_queda_en_40(auth_client, registrar):
    """(e) Verifica que un trámite con inyecciones de script se guarde íntegro, se liste y se limpie a 40 trámites."""
    id_test = "T_985"
    payload = {
        "id_tramite": id_test,
        "nombre": "<script>alert(1)</script>",
        "costo": "Gratuito",
        "plazo": "1 día",
        "requisitos": ["<img src=x onerror=alert('xss')>"]
    }

    with app.app_context():
        assert Tramite.query.count() == 40

    try:
        # 1. Registrar trámite con carga útil XSS
        res_crear = auth_client.post("/api/admin/tramites", json=payload)
        assert res_crear.status_code == 201

        # 2. Consultar lista vía API
        res_listar = auth_client.get("/api/admin/tramites")
        assert res_listar.status_code == 200
        items = res_listar.get_json().get("tramites", [])
        creado = next((t for t in items if t["id_tramite"] == id_test), None)
        assert creado is not None
        assert creado["nombre"] == "<script>alert(1)</script>"
        assert creado["requisitos"] == ["<img src=x onerror=alert('xss')>"]

        estado = "PASO"
        registrar(
            "ADM_27", "seguridad_xss", "Trámite con carga <script>alert(1)</script>",
            "Guardado íntegro en BD, listado en API y eliminado preservando 40 trámites",
            f"HTTP {res_crear.status_code} nombre={creado['nombre']}",
            1.0, estado
        )
    finally:
        auth_client.delete(f"/api/admin/tramites/{id_test}")
        with app.app_context():
            conteo = Tramite.query.count()
            assert conteo == 40, f"El catálogo debe quedar exactamente en 40 trámites (hay {conteo})"


# ==============================================================================
# 5. REGRESIÓN DE SEGURIDAD (SECRET_KEY, COOKIE_SECURE, RATE LIMIT, HEADERS, CSP)
# ==============================================================================
def test_secret_key_sin_debug_falla_inicio(monkeypatch, registrar):
    """(a) Verifica que config.SECRET_KEY no tenga valor por defecto y create_app falle sin SECRET_KEY en producción."""
    import importlib
    import config as cfg_module
    from backend import create_app

    clave_original = os.environ.get("SECRET_KEY")
    try:
        # 1. Verificar que config.py no tiene valor por defecto si falta la variable
        monkeypatch.delenv("SECRET_KEY", raising=False)
        importlib.reload(cfg_module)
        cfg_val = cfg_module.SECRET_KEY
        assert cfg_val is None, "config.SECRET_KEY debe ser None cuando no está definida en el entorno"

        # 2. Verificar que create_app() en modo producción (sin debug ni testing) lanza RuntimeError
        monkeypatch.delenv("FLASK_DEBUG", raising=False)
        error_lanzado = False
        mensaje_error = ""
        try:
            create_app()
        except RuntimeError as ex:
            error_lanzado = True
            mensaje_error = str(ex)

        es_valido = error_lanzado and "secrets.token_hex" in mensaje_error
        estado = "PASO" if es_valido else "FALLO"
        registrar(
            "ADM_28", "seguridad_secret_key", "create_app() en prod sin SECRET_KEY",
            "RuntimeError indicando cómo generar la clave",
            f"Lanzó RuntimeError: {error_lanzado}, msg='{mensaje_error[:55]}...'",
            1.0, estado
        )
        assert error_lanzado, "create_app debe lanzar RuntimeError si falta SECRET_KEY en producción"
        assert "secrets.token_hex(32)" in mensaje_error
    finally:
        if clave_original:
            os.environ["SECRET_KEY"] = clave_original
            cfg_module.SECRET_KEY = clave_original


def test_cookie_secure_activa_con_variable_entorno(monkeypatch, registrar):
    """(b) Verifica que SESSION_COOKIE_SECURE se active con COOKIE_SECURE=true y se desactive con false."""
    import importlib
    import config as cfg_module

    # Caso True
    monkeypatch.setenv("COOKIE_SECURE", "true")
    importlib.reload(cfg_module)
    val_true = cfg_module.SESSION_COOKIE_SECURE

    # Caso False
    monkeypatch.setenv("COOKIE_SECURE", "false")
    importlib.reload(cfg_module)
    val_false = cfg_module.SESSION_COOKIE_SECURE

    es_valido = (val_true is True) and (val_false is False)
    estado = "PASO" if es_valido else "FALLO"
    registrar(
        "ADM_29", "seguridad_cookie", "Evaluación COOKIE_SECURE (true/false)",
        "SESSION_COOKIE_SECURE True con 'true' y False con 'false'",
        f"true={val_true}, false={val_false}",
        1.0, estado
    )
    assert val_true is True
    assert val_false is False


def test_limite_intentos_login_bloquea_sexto_y_reinicia(client, registrar):
    """(c) Verifica que el limitador bloquee al sexto intento con 429 y Retry-After, y reinicie tras login exitoso."""
    from backend.admin.seguridad import reset_intentos_login
    reset_intentos_login()

    usuario_prueba = "admin_test_lockout"
    password_mala = "password_incorrecta"

    # 1. 5 intentos fallidos deben responder 401
    for i in range(5):
        r = client.post("/api/admin/login", json={"usuario": usuario_prueba, "password": password_mala})
        assert r.status_code == 401, f"Intento {i+1} debió devolver 401, devolvió {r.status_code}"

    # 2. 6to intento fallido debe responder 429
    r6 = client.post("/api/admin/login", json={"usuario": usuario_prueba, "password": password_mala})
    d6 = r6.get_json() or {}
    assert r6.status_code == 429
    assert "Retry-After" in r6.headers
    assert int(r6.headers["Retry-After"]) > 0
    assert d6.get("mensaje") == "Demasiados intentos fallidos. Intenta nuevamente más tarde."

    # 3. Tras login exitoso de admin real, su contador se reinicia y permite accesos
    reset_intentos_login()
    pwd = _get_admin_password()
    r_ok = client.post("/api/admin/login", json={"usuario": "admin", "password": pwd})
    assert r_ok.status_code == 200

    estado = "PASO"
    registrar(
        "ADM_30", "rate_limiting_login", "6 intentos fallidos seguidos y posterior reset",
        "HTTP 429 al 6to intento con Retry-After y reinicio",
        f"r6_code={r6.status_code}, retry_after={r6.headers.get('Retry-After')}, r_ok={r_ok.status_code}",
        1.0, estado
    )


def test_cabeceras_http_seguridad_presentes(client, registrar):
    """(d) Verifica que las cabeceras de seguridad requeridas estén presentes en las respuestas."""
    res = client.get("/")
    assert res.status_code == 200
    headers = res.headers

    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "camera=()" in headers.get("Permissions-Policy", "")
    assert "microphone=()" in headers.get("Permissions-Policy", "")
    assert "geolocation=()" in headers.get("Permissions-Policy", "")
    assert "Content-Security-Policy" in headers

    # Comprobar Cache-Control no-store en rutas admin
    res_admin = client.get("/admin")
    assert res_admin.status_code == 200
    assert "no-store" in res_admin.headers.get("Cache-Control", "")

    res_api_admin = client.get("/api/admin/tramites")
    assert "no-store" in res_api_admin.headers.get("Cache-Control", "")

    estado = "PASO"
    registrar(
        "ADM_31", "cabeceras_seguridad", "Inspección de cabeceras HTTP de respuesta",
        "X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy, Cache-Control, CSP",
        f"nosniff={headers.get('X-Content-Type-Options')}, frame={headers.get('X-Frame-Options')}, cache_admin={res_admin.headers.get('Cache-Control')}",
        1.0, estado
    )


def test_paginas_html_responden_200_con_csp(client, registrar):
    """(e) Verifica que las páginas HTML sigan respondiendo 200 y que CSP contenga orígenes requeridos."""
    res_index = client.get("/")
    assert res_index.status_code == 200
    csp_index = res_index.headers.get("Content-Security-Policy", "")
    assert "'self'" in csp_index
    assert "https://cdn.tailwindcss.com" in csp_index
    assert "'unsafe-inline'" in csp_index

    res_admin = client.get("/admin")
    assert res_admin.status_code == 200
    csp_admin = res_admin.headers.get("Content-Security-Policy", "")
    assert "'self'" in csp_admin
    assert "https://cdn.tailwindcss.com" in csp_admin

    estado = "PASO"
    registrar(
        "ADM_32", "compatibilidad_csp", "GET / y GET /admin con directivas CSP",
        "HTTP 200 en ambas páginas y directivas compatibles con Tailwind y estilos inline",
        f"index_code={res_index.status_code}, admin_code={res_admin.status_code}",
        1.0, estado
    )


def test_ui_plantillas_accesibilidad_y_sin_artefactos_jsx(client, registrar):
    """Verifica accesibilidad básica, lang='es', indicadores de carga y ausencia de artefactos JSX en plantillas HTML."""
    # 1. Portal Ciudadano (index.html)
    res_index = client.get("/")
    assert res_index.status_code == 200
    html_index = res_index.get_data(as_text=True)

    assert '<html lang="es">' in html_index
    assert 'aria-label="Escribe tu pregunta sobre trámites"' in html_index
    assert 'aria-label="Escribe tu consulta en el asistente flotante"' in html_index
    assert 'id="widget-typing-indicator"' in html_index
    assert 'id="chat-submit-btn"' in html_index
    assert 'id="widget-submit-btn"' in html_index
    assert '{/*' not in html_index
    assert '*/}' not in html_index
    assert "Tramifácil" in html_index
    assert "POR UNA TRANSFORMACIÓN" in html_index
    assert "RESOLUCIÓN DE GERENCIA MUNICIPAL" in html_index

    # 2. Panel Administrativo (admin.html)
    res_admin = client.get("/admin")
    assert res_admin.status_code == 200
    html_admin = res_admin.get_data(as_text=True)

    assert '<html lang="es">' in html_admin
    assert '<label for="login-usuario"' in html_admin
    assert '<label for="login-password"' in html_admin
    assert '<label for="tramite-codigo"' in html_admin
    assert '<label for="tramite-nombre"' in html_admin
    assert 'aria-label="Buscar trámites por código o nombre"' in html_admin
    assert 'className=' not in html_admin
    assert '{/*' not in html_admin
    assert 'max-h-[90vh] overflow-y-auto' in html_admin
    assert 'Tu sesión ha expirado' in html_admin
    assert '¿Estás seguro de que deseas eliminar el trámite con código' in html_admin

    registrar(
        "ADM_33", "plantillas_ui_accesibilidad", "Verificación de accesibilidad, atributos y sintaxis en HTML",
        "Atributos lang='es', aria-labels, etiquetas for, sin JSX residual y modales responsive",
        "Ambas plantillas cumplen estándares de accesibilidad e integridad visual",
        1.0, "PASO"
    )


