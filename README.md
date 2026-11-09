# Chatbot municipal MDJLO

Sistema de orientación sobre requisitos, costos y plazos de la Municipalidad Distrital de José Leonardo Ortiz. Proyecto de tesis con Flask, SQLAlchemy, MySQL/MariaDB y un clasificador TF-IDF + LinearSVC.

El catálogo contiene **239 trámites** y el conjunto NLP contiene **3427 ejemplos y 61 intenciones**. El portal ciudadano y el panel administrativo se sirven desde Flask con HTML, CSS y JavaScript. Entorno comprobado: Python 3.14 en Windows.

La [revisión general de interpretación y contexto](docs/revision_contexto_general.md) explica la resolución con frases naturales, las rectificaciones y la cobertura por API de las 39 familias y los procedimientos individuales del catálogo.

## Archivos del proyecto

```text
app.py                       Entrada del servidor Flask
config.py                    Rutas, conexión a BD y configuración
database.py                 Creación de tablas y carga inicial del catálogo
backend/
  admin/                     Autenticación y administración de trámites
  chatbot/                   API, diálogo, respuestas y auditoría
  models/                    Modelos de base de datos y carga del CSV
  nlp/                       Normalización, clasificación y entrenamiento
templates/                   Portal ciudadano y panel administrativo
static/                      CSS, JavaScript y logotipo del portal
data/
  tramites.csv               Catálogo fuente de trámites y requisitos
  dataset_nlp.csv            Maestro de ejemplos NLP
  train_nlp.csv              Partición de entrenamiento
  test_nlp.csv               Partición de evaluación
  modelo_intenciones.joblib  Modelo utilizado por el chatbot
tests/                       Pruebas automáticas y sus datos de referencia
scripts/
  sincronizar_catalogo.py     Comparación y actualización del catálogo con respaldo
  reset_admin_password.py     Recuperación de la cuenta administrativa
  verificar_respuestas_claras.py  Comprobación HTTP con servidor temporal
  prueba_carga.py             Medición de rendimiento y carga
  server_runner.py            Servidor auxiliar de las pruebas de carga
preparar_entornos.py          Generación de la partición NLP 80/20
train_nlp.py                  Entrenamiento y exportación del modelo
evaluar_tfidf.py              Métricas, validación cruzada y errores del clasificador
evaluar_umbral.py             Cobertura y aciertos según el umbral de decisión
setup_mysql.py               Instalación inicial desde el SQL
generar_sql_mysql.py          Regeneración del SQL desde el catálogo
database_mysql.sql           Estructura y catálogo para una instalación nueva
requirements.txt             Dependencias de ejecución y entrenamiento
requirements-dev.txt         Dependencias de pruebas
requirements-semantic.txt    Apoyo semántico local opcional
```

`reports/` contiene informes regenerables, `logs/` los registros de ejecución y `backups/` los respaldos creados al sincronizar la BD. Se crean cuando son necesarios y están excluidos de Git. `.venv/` contiene las dependencias locales.

## Instalación y arranque

Desde PowerShell, en la carpeta del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Inicia MySQL/MariaDB, por ejemplo desde el panel de XAMPP. La conexión predeterminada es `mysql+pymysql://root:@127.0.0.1:3306/municipal_db`. Puedes establecer otra mediante `DATABASE_URL` o `MYSQL_URL` antes de ejecutar Python.

Configura una clave de sesión para los comandos administrativos:

```powershell
$env:SECRET_KEY = .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

Para una **instalación nueva**, crea `municipal_db` desde tu administrador de MySQL:

```sql
CREATE DATABASE IF NOT EXISTS municipal_db CHARACTER SET utf8mb4 COLLATE utf8mb4_spanish_ci;
```

Luego inicializa las tablas y el catálogo:

```powershell
.\.venv\Scripts\python.exe database.py
```

Se crea el usuario `admin` si no existe. Su contraseña se toma de `ADMIN_INITIAL_PASSWORD`; si no se configura, se genera una contraseña temporal y se muestra una vez en la terminal.

Como alternativa para una instalación nueva, `setup_mysql.py` importa `database_mysql.sql` y crea la BD. **Ese SQL recrea las tablas de catálogo y usuarios**: para una instalación existente utiliza el sincronizador descrito abajo.

El modelo entrenado ya está incluido en `data/`. Inicia el sistema:

```powershell
.\.venv\Scripts\python.exe app.py
```

Abre [el portal ciudadano](http://localhost:5000/) o [Administración](http://localhost:5000/admin). Detén el servidor con Ctrl+C. Si el puerto está ocupado, el comando informa que hay otra instancia abierta. Al ejecutar directamente `app.py` sin clave ni `FLASK_DEBUG`, se activa el modo de desarrollo con una clave efímera; en producción configura una `SECRET_KEY` estable.

## Uso y mantenimiento

El chatbot solicita aclaraciones cuando hay varias alternativas y conserva el trámite activo para seguimientos como «cuánto cuesta» o «cuál es el plazo». Cada respuesta muestra los campos solicitados. La información procede del catálogo local; si una modalidad, sede u horario no está registrado, se deriva a la municipalidad.

El panel permite consultar, crear, editar y eliminar trámites.

El acceso por `/admin` o `/admin/` exige una sesión válida y el rol de administrador; sin ella se redirige a `/admin/login`. El servidor comprueba la cuenta y sus permisos en cada petición y rechaza sesiones anteriores a un cambio de contraseña. Las API administrativas responden 401 cuando no hay una sesión autorizada. Cerrar sesión también bloquea la entrada por la URL directa.

El panel utiliza el logotipo institucional, estilos y JavaScript locales. La tabla admite desplazamiento vertical y horizontal, encabezado fijo, búsqueda por nombre o código y ordenación. Los formularios de registro, edición y confirmación se adaptan a escritorio y móvil.

Para recuperar el acceso administrativo:

```powershell
.\.venv\Scripts\python.exe scripts/reset_admin_password.py
```

Para comparar el catálogo CSV con la base existente sin modificarla:

```powershell
.\.venv\Scripts\python.exe scripts/sincronizar_catalogo.py
```

Añade `--aplicar` para sincronizar con respaldo en `backups/`. El sincronizador conserva los trámites adicionales, usuarios y conversaciones.

## Pruebas y evaluación

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
.\.venv\Scripts\python.exe -m pytest tests -q
```

Las pruebas utilizan SQLite en memoria y credenciales efímeras. Cubren diálogo, macros, los 239 trámites, sesiones, administración, seguridad, auditoría y sincronización. No alteran el MySQL real. Para exportar los casos que usan el registro CSV, añade `--reporte-csv reports/pruebas_resultados.csv`.

Comprobación adicional con peticiones HTTP y un servidor temporal que se cierra al terminar:

```powershell
.\.venv\Scripts\python.exe scripts/verificar_respuestas_claras.py
```

Con `--mysql` utiliza la conexión real y registra las 38 consultas de comprobación en la auditoría habitual. Los informes se guardan en `reports/`. Después de exportar el registro CSV a `reports/dialogo_catalogo.csv`, `python scripts/informar_cobertura_dialogo.py` genera una tabla de 925 frases de macros y 16 consultas de procedimientos individuales. La prueba de carga está disponible con `python scripts/prueba_carga.py`; usa la conexión configurada, genera tráfico sintético y exporta sus métricas en `reports/`.

Tras editar el maestro NLP, el flujo de preparación, evaluación y entrenamiento es:

```powershell
.\.venv\Scripts\python.exe preparar_entornos.py
.\.venv\Scripts\python.exe evaluar_tfidf.py
.\.venv\Scripts\python.exe evaluar_umbral.py
.\.venv\Scripts\python.exe train_nlp.py
```

La partición es estratificada, con semilla 42 y sin consultas normalizadas compartidas entre train y test. La evaluación entrena únicamente con el conjunto train; el modelo final se exporta después de entrenar con todo el maestro. No se debe presentar su resultado sobre datos de entrenamiento como evaluación independiente. La confianza basada en el margen SVM no equivale a una probabilidad calibrada.

El apoyo semántico es opcional: `requirements-semantic.txt` contiene sus dependencias y `CHAT_MODELO_SEMANTICO` permite elegir el modelo local. No descarga modelos durante el chat y el diálogo continúa si el apoyo no está disponible. Puedes desactivarlo con `CHAT_SEMANTICA=0`.

## Verificación de la limpieza (3 de noviembre de 2026)

2410 pruebas aprobadas después de la limpieza y la actualización administrativa, incluidas las de acceso directo sin sesión, cuenta sin permisos, sesión vencida, cookie alterada, cierre de sesión y revocación por cambio de cuenta o contraseña. Se comprobó el panel en navegador con una base temporal: acceso, búsqueda, ordenación, scroll, registro, edición, cancelación de eliminación y cierre de sesión, con vistas de escritorio y móvil.

Se comprobaron también por HTTP el portal y sus recursos estáticos, además de 20 turnos de conversación con SQLite y otros 20 con MySQL. El catálogo MySQL coincide con los 239 registros del CSV. La preparación conserva los mismos archivos de datos y modelo; la evaluación reproduce 91.40 % de accuracy y 91.08 % de F1 macro en las 686 consultas de test.
