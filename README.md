# 🏛️ Sistema Inteligente de Chatbot para la Municipalidad Distrital de José Leonardo Ortiz (MDJLO)

> **Título de la Investigación:** Sistema inteligente basado en chatbot para apoyar la orientación sobre requisitos procedimentales en la Municipalidad de José Leonardo Ortiz  
> **Asignatura:** Seminario de Tesis I  
> **Hito:** Hito 2 (50% - Cierre del Núcleo Funcional)  
> **Metodología Híbrida:** Scrum / CRISP-DM  

---

## 📌 Descripción del Proyecto

Este proyecto consiste en un **sistema web inteligente basado en Procesamiento de Lenguaje Natural (NLP)** diseñado para orientar a los ciudadanos del distrito de José Leonardo Ortiz sobre los trámites, requisitos procedimentales, costos y plazos estipulados en el **TUPA (Texto Único de Procedimientos Administrativos)** de la MDJLO.

El sistema está impulsado por el asistente virtual **"Leonardito"**, respaldado por un modelo de clasificación semántica **TF-IDF + SVM (LinearSVC)** que reconoce intenciones en tiempo real, gestiona memoria conversacional contextual, filtra consultas fuera de dominio y proporciona un panel administrativo seguro para la gestión del catálogo de trámites.

---

## 🛠️ Arquitectura y Tecnologías Utilizadas

- **Lenguaje:** Python 3.10+
- **Framework Web Backend:** Flask, Flask-Cors
- **Base de Datos & ORM:** SQLite / Flask-SQLAlchemy (`municipal.db`)
- **Procesamiento de Lenguaje Natural (IA):** Scikit-Learn (TF-IDF Vectorizer + LinearSVC), Joblib
- **Frontend:** HTML5, JavaScript (Vanilla ES6), Tailwind CSS (CDN)
- **Seguridad:** Werkzeug Passwords (hashing de credenciales), Gestión de Sesiones HTTP-Only

---

## 📁 Estructura del Repositorio

```text
chatbot_jlo/
│
├── app.py                            # Servidor principal Flask y endpoints API (/api/chat, /api/admin/*)
├── database.py                       # Modelos ORM (Tramite, Requisito, Usuario, Rol) y poblado desde CSV
├── train_nlp.py                      # Script de entrenamiento del modelo NLP (TF-IDF + SVM)
├── evaluar_tfidf.py                  # Evaluación del modelo en test split 80/20 (Accuracy: 90.28%)
├── evaluar_generalizacion_tfidf.py   # Evaluación de generalización en 84 frases inéditas (Accuracy: 95.24%)
├── preparar_entornos.py              # Helper de preparación de entorno de desarrollo
├── modelo_intenciones.joblib         # Pipeline NLP entrenado y serializado
├── tramites.csv                      # Base de conocimiento inicial extraída del TUPA de la MDJLO
├── dataset_nlp.csv                   # Dataset consolidado de entrenamiento y prueba
├── train_nlp.csv / test_nlp.csv      # Divisores del dataset (80% train / 20% test)
├── test_generalizacion.csv           # Set de pruebas de generalización (84 consultas inéditas)
│
├── templates/
│   ├── index.html                    # Interfaz pública del Portal Municipal con el Chatbot "Leonardito"
│   └── admin.html                    # Panel Administrativo (CRUD de Trámites y Requisitos)
│
├── data/ & tests/                    # Datasets estructurados en formato NLU/Rasa (opcional / respaldo)
├── requirements.txt                  # Archivo de dependencias Python requeridas
└── .gitignore                        # Reglas de exclusión para Git (ignora .venv, __pycache__, etc.)
```

---

## 🚀 Guía de Instalación y Configuración Paso a Paso

Sigue estos pasos para desplegar y ejecutar el proyecto localmente:

### 1. Clonar el Repositorio
```bash
git clone https://github.com/TU_USUARIO/chatbot_jlo.git
cd chatbot_jlo
```

### 2. Crear y Activar un Entorno Virtual (Recomendado)
- **En Windows (PowerShell / CMD):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\activate
  ```
- **En Linux / macOS:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 3. Instalar las Dependencias
```bash
pip install -r requirements.txt
```

### 4. Inicializar y Poblar la Base de Datos Relacional
Ejecuta el script `database.py` para crear las tablas en `municipal.db` y cargar los trámites del TUPA desde `tramites.csv`:
```bash
python database.py
```
> *Salida esperada: `Poblado completo: X trámites nuevos...` y creación del usuario admin por defecto.*

### 5. Verificar o Re-entrenar el Modelo de IA (NLP)
Si deseas volver a generar el archivo `modelo_intenciones.joblib`:
```bash
python train_nlp.py
```
Para verificar la precisión del modelo en el conjunto de generalización:
```bash
python evaluar_generalizacion_tfidf.py
```
> *Salida esperada: `Accuracy: 0.9524 (84 frases)`.*

### 6. Ejecutar la Aplicación Web
```bash
python app.py
```
Abre tu navegador web e ingresa a: **`http://localhost:5000`**

---

## 📖 Manual de Uso del Sistema

### 💬 1. Módulo del Ciudadano (Chatbot "Leonardito")
Accede a `http://localhost:5000` para interactuar con la interfaz del chatbot.

- **Consulta de Requisitos:** Escribe preguntas como *"¿Qué necesito para sacar licencia de funcionamiento?"* o *"Requisitos para cambio de giro"*.
- **Memoria Contextual:** Después de consultar por un trámite, puedes preguntar directamente *"¿Cuánto cuesta?"* o *"¿Cuánto tarda?"* y el chatbot responderá basándose en el contexto actual.
- **Consultas Directas:** Puedes consultar en una sola frase como *"¿Cuál es el costo del duplicado de licencia?"*.
- **Filtro de Seguridad / Fallback:** Consultas no relacionadas con trámites municipales (ej. *"¿Quién es el alcalde?"* o *"¿Cuándo pasa la basura?"*) son detectadas automáticamente por el umbral de confianza (`UMBRAL_CONFIANZA = 0.70`), emitiendo una respuesta preventiva.

---

### ⚙️ 2. Módulo de Administración (`/admin`)
Accede a `http://localhost:5000/admin` o haz clic en **"⚙️ Panel Admin (RF06)"** en la barra superior.

- **Credenciales:**
  - **Usuario:** `admin`
  - **Contraseña:** Configurada mediante la variable de entorno `ADMIN_PASSWORD` (o generada aleatoriamente al inicializar la BD).
- **Funcionalidades CRUD:**
  - **Ver Catálogo:** Lista todos los trámites, costos, plazos y requisitos.
  - **Crear Trámite:** Añadir un nuevo procedimiento administrativo al TUPA.
  - **Editar Trámite:** Actualizar nombres, montos, días de atención o agregar/remover requisitos.
  - **Eliminar Trámite:** Eliminar procedimientos en cascada de la base de datos.

---

## 📊 Resultados del Componente Inteligente (NLP)

| Dataset de Evaluación | Nº de Consultas | Algoritmo | Exactitud (Accuracy) |
| :--- | :---: | :---: | :---: |
| **Test Split (20% interno)** | 144 | TF-IDF + LinearSVC | **90.28%** |
| **Set de Generalización (Inédito)** | 84 | TF-IDF + LinearSVC | **95.24%** |

---

## 📜 Licencia y Créditos
Desarrollado para el proyecto de tesis de la **Municipalidad Distrital de José Leonardo Ortiz (MDJLO)**.
