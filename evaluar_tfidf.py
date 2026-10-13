import pandas as pd
import unicodedata
import json
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# 1. Preprocesamiento
def preprocesar_texto(texto):
    if texto is None: return ""
    texto = str(texto).lower().strip()
    texto_normalizado = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto_normalizado if unicodedata.category(c) != "Mn")

print("Cargando datasets divididos (80/20)...")
# 2. Cargar los archivos pre-divididos
df_train = pd.read_csv("train_nlp.csv")
df_test = pd.read_csv("test_nlp.csv")

X_train, y_train = df_train["query"], df_train["intent"]
X_test, y_test = df_test["query"], df_test["intent"]

# 3. Construir y entrenar el Pipeline TF-IDF + SVM
print("Entrenando modelo TF-IDF + LinearSVC...")
pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(preprocessor=preprocesar_texto, ngram_range=(1, 2))),
    ("clf", LinearSVC(random_state=42)),
])
pipeline.fit(X_train, y_train)

# 4. Evaluación en el conjunto de prueba (20%)
y_pred = pipeline.predict(X_test)
acc = accuracy_score(y_test, y_pred)

print("\n" + "="*40)
print("   RESULTADOS FINALES: TF-IDF + SVM")
print("="*40)
print(f"Accuracy Exacto (Test 20%): {acc:.4f}\n")
print(classification_report(y_test, y_pred, zero_division=0))

# ---------------------------------------------------------------------------
# 5. Detalle de confusión por clase (qué se confunde con qué, y cuántas veces)
# ---------------------------------------------------------------------------
clases = sorted(y_test.unique())
cm = confusion_matrix(y_test, y_pred, labels=clases)
reporte_dict = classification_report(y_test, y_pred, zero_division=0, output_dict=True)

resultado = {}
for i, clase in enumerate(clases):
    confundido_con = {}
    for j, otra_clase in enumerate(clases):
        if i != j and cm[i][j] > 0:
            confundido_con[otra_clase] = int(cm[i][j])
    metricas = reporte_dict.get(clase, {})
    resultado[clase] = {
        "precision": metricas.get("precision", 0),
        "recall": metricas.get("recall", 0),
        "f1-score": metricas.get("f1-score", 0),
        "support": metricas.get("support", 0),
        "confused_with": confundido_con,
    }

print("\n" + "="*40)
print("   DETALLE DE CONFUSIÓN POR CLASE")
print("="*40)
print(json.dumps(resultado, indent=2, ensure_ascii=False))

with open("confusion_detalle.json", "w", encoding="utf-8") as f:
    json.dump(resultado, f, indent=2, ensure_ascii=False)
print("\nGuardado también en confusion_detalle.json")