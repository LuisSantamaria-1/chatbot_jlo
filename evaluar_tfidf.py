import pandas as pd
import unicodedata
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, classification_report

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