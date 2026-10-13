"""
entrenamiento.py
----------------
Entrenamiento y serialización del clasificador de intenciones (TF-IDF + LinearSVC).
"""

import os
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, classification_report

from config import CSV_DATASET_PATH, MODEL_PATH, DATA_DIR
from backend.nlp.preprocesamiento import preprocesar_texto

RANDOM_STATE = 42

def cargar_dataset(csv_path=CSV_DATASET_PATH):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"No se encontró el archivo CSV en: {csv_path}")

    df = pd.read_csv(csv_path)
    df = df.dropna(subset=["query", "intent"])
    return df


def construir_pipeline():
    """
    Pipeline: preprocesamiento (dentro del propio TfidfVectorizer vía el
    parámetro `preprocessor`) -> TF-IDF -> LinearSVC.
    """
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            preprocessor=preprocesar_texto,
            ngram_range=(1, 2),   # unigramas y bigramas
            min_df=1,
        )),
        ("clf", LinearSVC(random_state=RANDOM_STATE)),
    ])
    return pipeline


def entrenar_y_evaluar(df):
    X = df["query"]
    y = df["intent"]

    pipeline = construir_pipeline()

    # 1) Validación cruzada estratificada
    n_por_clase_min = y.value_counts().min()
    cv_folds = min(3, n_por_clase_min)

    if cv_folds >= 2:
        skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=RANDOM_STATE)
        scores_cv = cross_val_score(pipeline, X, y, cv=skf, scoring="accuracy")
        print(f"Accuracy por validación cruzada ({cv_folds}-fold): "
              f"{scores_cv.mean():.4f} (+/- {scores_cv.std():.4f})")
    else:
        print("Dataset muy pequeño para validación cruzada; se omite ese paso.")

    # 2) Evaluación con los conjuntos fijos train/test (80/20)
    train_path = DATA_DIR / "train_nlp.csv"
    test_path = DATA_DIR / "test_nlp.csv"
    df_train = pd.read_csv(train_path).dropna(subset=["query", "intent"])
    df_test = pd.read_csv(test_path).dropna(subset=["query", "intent"])

    X_train, y_train = df_train["query"], df_train["intent"]
    X_test, y_test = df_test["query"], df_test["intent"]

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    print(f"\nAccuracy en el conjunto de prueba (test_nlp.csv 20% - {len(df_test)} ejemplos): {acc:.4f}")
    print("\nReporte de clasificación (test 20%):")
    print(classification_report(y_test, y_pred, zero_division=0))

    # 3) Reentrenar con el 100% de los datos para el modelo final exportado
    modelo_final = construir_pipeline()
    modelo_final.fit(X, y)

    return modelo_final


def exportar_modelo(modelo, path=MODEL_PATH):
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    joblib.dump(modelo, path)
    print(f"\nModelo exportado exitosamente en: {path}")


if __name__ == "__main__":
    print("Cargando dataset...")
    df = cargar_dataset()
    print(f"Total de ejemplos: {len(df)} | Clases: {sorted(df['intent'].unique())}\n")

    print("Entrenando modelo (TF-IDF + LinearSVC)...\n")
    modelo_final = entrenar_y_evaluar(df)

    exportar_modelo(modelo_final)

    # También actualizar copia en raíz si existe para compatibilidad
    exportar_modelo(modelo_final, "modelo_intenciones.joblib")

    # Prueba rápida de inferencia
    ejemplos_prueba = [
        "cuanto cuesta sacar la licencia de mi bodega",
        "perdi mi permiso de funcionamiento que hago",
        "que requisitos piden para el divorcio municipal",
    ]
    print("\n--- Prueba rápida de inferencia ---")
    for texto in ejemplos_prueba:
        pred = modelo_final.predict([texto])[0]
        print(f"'{texto}' -> {pred}")
