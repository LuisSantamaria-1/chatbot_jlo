"""
train_nlp.py
------------
Entrenamiento del clasificador de intenciones para el chatbot municipal.

Pipeline:
    1. Preprocesamiento de texto (minúsculas + remoción de acentos).
    2. Vectorización TF-IDF.
    3. Clasificación con LinearSVC (SVM lineal).

El dataset (dataset_nlp.csv) es pequeño (15 ejemplos / 5 clases), por lo que,
además del accuracy en un split train/test, se reporta un accuracy promedio
por validación cruzada estratificada (más confiable con pocos datos).

Al final se exporta el pipeline completo (preprocesamiento + TF-IDF + SVM)
en un único archivo .joblib, listo para cargar en Flask con:

    import joblib
    modelo = joblib.load("modelo_intenciones.joblib")
    intent_predicha = modelo.predict(["cuanto cuesta la licencia de bodega"])[0]

Uso:
    python train_nlp.py
"""

import os
import unicodedata

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, classification_report

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CSV_PATH = os.path.join(BASE_DIR, "dataset_nlp.csv")
MODEL_PATH = os.path.join(BASE_DIR, "modelo_intenciones.joblib")

RANDOM_STATE = 42


# ---------------------------------------------------------------------------
# Preprocesamiento de texto
# ---------------------------------------------------------------------------

def preprocesar_texto(texto):
    """
    Normaliza el texto de entrada:
      1. Convierte a minúsculas.
      2. Remueve acentos/tildes (á -> a, ñ se mantiene como ñ->n aquí
         de forma consciente, ya que unicodedata.normalize con NFKD
         descompone también la ñ; esto es aceptable para TF-IDF ya que
         normaliza variaciones ortográficas comunes en consultas de usuarios).
    """
    if texto is None:
        return ""
    texto = str(texto).lower().strip()
    # NFKD separa los caracteres base de sus marcas diacríticas (acentos),
    # luego filtramos esas marcas (categoría Unicode 'Mn').
    texto_normalizado = unicodedata.normalize("NFKD", texto)
    texto_sin_acentos = "".join(
        c for c in texto_normalizado if unicodedata.category(c) != "Mn"
    )
    return texto_sin_acentos


# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------

def cargar_dataset(csv_path=CSV_PATH):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"No se encontró el archivo CSV en: {csv_path}")

    df = pd.read_csv(csv_path)
    df = df.dropna(subset=["query", "intent"])
    return df


# ---------------------------------------------------------------------------
# Entrenamiento
# ---------------------------------------------------------------------------

def construir_pipeline():
    """
    Pipeline: preprocesamiento (dentro del propio TfidfVectorizer vía el
    parámetro `preprocessor`) -> TF-IDF -> LinearSVC.

    Al usar `preprocessor=preprocesar_texto` dentro del vectorizador,
    el mismo pipeline exportado se encarga de limpiar cualquier texto
    nuevo automáticamente (no hace falta preprocesar manualmente en Flask).
    """
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            preprocessor=preprocesar_texto,
            ngram_range=(1, 2),   # unigramas y bigramas: útil para frases cortas
            min_df=1,
        )),
        ("clf", LinearSVC(random_state=RANDOM_STATE)),
    ])
    return pipeline


def entrenar_y_evaluar(df):
    X = df["query"]
    y = df["intent"]

    pipeline = construir_pipeline()

    # --- 1) Validación cruzada estratificada (más robusta con dataset pequeño) ---
    n_clases = y.nunique()
    n_por_clase_min = y.value_counts().min()
    cv_folds = min(3, n_por_clase_min)  # evita error si alguna clase tiene pocos ejemplos

    if cv_folds >= 2:
        skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=RANDOM_STATE)
        scores_cv = cross_val_score(pipeline, X, y, cv=skf, scoring="accuracy")
        print(f"Accuracy por validación cruzada ({cv_folds}-fold): "
              f"{scores_cv.mean():.4f} (+/- {scores_cv.std():.4f})")
    else:
        print("Dataset muy pequeño para validación cruzada; se omite ese paso.")

    # --- 2) Split train/test simple, para tener un accuracy de referencia ---
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=RANDOM_STATE, stratify=y
    )

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    print(f"\nAccuracy en el conjunto de prueba (holdout 30%): {acc:.4f}")
    print("\nReporte de clasificación (holdout):")
    print(classification_report(y_test, y_pred, zero_division=0))

    # --- 3) Reentrenar con el 100% de los datos para el modelo final exportado ---
    # (en un dataset de producción real, se recomienda mantener un test set
    # separado y no reentrenar con todo; aquí se hace porque el dataset de
    # ejemplo es muy pequeño y se busca maximizar el uso de los datos disponibles)
    modelo_final = construir_pipeline()
    modelo_final.fit(X, y)

    return modelo_final


def exportar_modelo(modelo, path=MODEL_PATH):
    joblib.dump(modelo, path)
    print(f"\nModelo exportado exitosamente en: {path}")


# ---------------------------------------------------------------------------
# Ejecución directa: python train_nlp.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Cargando dataset...")
    df = cargar_dataset()
    print(f"Total de ejemplos: {len(df)} | Clases: {sorted(df['intent'].unique())}\n")

    print("Entrenando modelo (TF-IDF + LinearSVC)...\n")
    modelo_final = entrenar_y_evaluar(df)

    exportar_modelo(modelo_final)

    # Prueba rápida de inferencia con una consulta nueva
    ejemplos_prueba = [
        "cuanto cuesta sacar la licencia de mi bodega",
        "perdi mi permiso de funcionamiento que hago",
        "quiero informacion sobre normas municipales",
    ]
    print("\n--- Prueba rápida de inferencia ---")
    for texto in ejemplos_prueba:
        pred = modelo_final.predict([texto])[0]
        print(f"'{texto}' -> {pred}")