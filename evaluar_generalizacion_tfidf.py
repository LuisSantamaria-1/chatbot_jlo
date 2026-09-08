"""
evaluar_generalizacion_tfidf.py
---------------------------------
Corre test_generalizacion.csv (frases NUEVAS, fuera de la distribución de
entrenamiento) contra tu modelo TF-IDF + SVM ya entrenado.

Copia este script Y test_generalizacion.csv a la carpeta de tu proyecto
TF-IDF (junto a tu .joblib) y ejecútalo ahí.

AJUSTA la sección CONFIG:
- Si guardaste vectorizer y clasificador en UN SOLO Pipeline (.joblib),
  usa la opción A (la que está activa por defecto).
- Si los guardaste SEPARADOS (un .joblib para el TfidfVectorizer y otro
  para el LinearSVC), usa la opción B (coméntala/descoméntala abajo).

Uso:
    python evaluar_generalizacion_tfidf.py
"""
import unicodedata
import os
import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# ---------------------------------------------------------------------------
# CONFIG — ajusta a los nombres reales de tus archivos
# ---------------------------------------------------------------------------
TEST_CSV = os.path.join(BASE_DIR, "test_generalizacion.csv")

# Opción A (por defecto): un solo Pipeline (vectorizer + clasificador juntos)
PIPELINE_PATH = os.path.join(BASE_DIR, "modelo_intenciones.joblib")

# Opción B: vectorizer y clasificador guardados por separado.
# Descomenta estas dos líneas (y comenta la de arriba) si es tu caso:
# VECTORIZER_PATH = os.path.join(BASE_DIR, "tfidf_vectorizer.joblib")
# CLF_PATH = os.path.join(BASE_DIR, "modelo_tfidf_svm.joblib")

# --- PEGA ESTO EN TU ARCHIVO DE EVALUACIÓN ---
def preprocesar_texto(texto):
    if texto is None:
        return ""
    texto = str(texto).lower().strip()
    texto_normalizado = unicodedata.normalize("NFKD", texto)
    texto_sin_acentos = "".join(
        c for c in texto_normalizado if unicodedata.category(c) != "Mn"
    )
    return texto_sin_acentos
# ---------------------------------------------
def main():
    df = pd.read_csv(TEST_CSV)
    textos = df["query"].tolist()
    y_true = df["intent_esperado"].tolist()
    print(f"Cargadas {len(textos)} frases de generalización.")

    # --- Opción A: pipeline único ---
    pipeline = joblib.load(PIPELINE_PATH)
    y_pred = pipeline.predict(textos)

    # --- Opción B: vectorizer + clasificador separados ---
    # vectorizer = joblib.load(VECTORIZER_PATH)
    # clf = joblib.load(CLF_PATH)
    # X = vectorizer.transform(textos)
    # y_pred = clf.predict(X)

    acc = accuracy_score(y_true, y_pred)
    print(f"\n{'=' * 60}\n  TF-IDF + SVM — set de generalización\n{'=' * 60}")
    print(f"Accuracy: {acc:.4f}  ({len(textos)} frases)\n")
    print("Reporte de clasificación:")
    print(classification_report(y_true, y_pred, zero_division=0))

    print("Errores individuales:")
    hubo_error = False
    for texto, real, pred in zip(textos, y_true, y_pred):
        if real != pred:
            hubo_error = True
            print(f"  '{texto}'\n    esperado={real}  ->  predicho={pred}")
    if not hubo_error:
        print("  (ninguno)")


if __name__ == "__main__":
    main()
