import os
import sys
import json
import pandas as pd
import numpy as np

sys.path.insert(0, os.getcwd())
from backend.nlp.preprocesamiento import preprocesar_texto
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)

sys.stdout.reconfigure(encoding='utf-8')

RANDOM_STATE = 42

# 1. Cargar datasets divididos (generados por preparar_entornos.py)
path_dataset = "data/dataset_nlp.csv" if os.path.exists("data/dataset_nlp.csv") else "dataset_nlp.csv"
path_train = "data/train_nlp.csv" if os.path.exists("data/train_nlp.csv") else "train_nlp.csv"
path_test = "data/test_nlp.csv" if os.path.exists("data/test_nlp.csv") else "test_nlp.csv"

df_dataset = pd.read_csv(path_dataset)
df_train = pd.read_csv(path_train)
df_test = pd.read_csv(path_test)

n_dataset = len(df_dataset)
n_train = len(df_train)
n_test = len(df_test)
n_clases = df_dataset["intent"].nunique()

X_train, y_train = df_train["query"], df_train["intent"]
X_test, y_test = df_test["query"], df_test["intent"]
X_full, y_full = df_dataset["query"], df_dataset["intent"]

# 2. Pipeline TF-IDF + LinearSVC idéntico al de backend/nlp/entrenamiento.py
pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(
        preprocessor=preprocesar_texto,
        ngram_range=(1, 2),
        min_df=1,
    )),
    ("clf", LinearSVC(random_state=RANDOM_STATE)),
])

# 3. Entrenar en train (80%) y evaluar en train y test
pipeline.fit(X_train, y_train)

y_train_pred = pipeline.predict(X_train)
y_test_pred = pipeline.predict(X_test)

train_acc = accuracy_score(y_train, y_train_pred)
test_acc = accuracy_score(y_test, y_test_pred)
p_macro = precision_score(y_test, y_test_pred, average="macro", zero_division=0)
r_macro = recall_score(y_test, y_test_pred, average="macro", zero_division=0)
f1_macro = f1_score(y_test, y_test_pred, average="macro", zero_division=0)
f1_weighted = f1_score(y_test, y_test_pred, average="weighted", zero_division=0)

# 4. Validación Cruzada Estratificada de 5 Folds sobre el dataset completo
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
cv_acc_scores = cross_val_score(pipeline, X_full, y_full, cv=skf, scoring="accuracy")
cv_f1_scores = cross_val_score(pipeline, X_full, y_full, cv=skf, scoring="f1_macro")

# 5. Reporte de Clasificación en Test
clases = sorted(y_test.unique())
rep_dict = classification_report(y_test, y_test_pred, zero_division=0, output_dict=True)
rep_text = classification_report(y_test, y_test_pred, zero_division=0)

# Exportar reporte_clasificacion.csv
df_rep = pd.DataFrame(rep_dict).transpose()
df_rep.to_csv("reporte_clasificacion.csv", index=True)

# Exportar distribucion_clases.csv
dist_train = df_train["intent"].value_counts().rename("train")
dist_test = df_test["intent"].value_counts().rename("test")
dist_full = df_dataset["intent"].value_counts().rename("total")
df_dist = pd.concat([dist_train, dist_test, dist_full], axis=1).fillna(0).astype(int)
df_dist["prop_test"] = (df_dist["test"] / df_dist["total"]).round(4)
df_dist.sort_index().to_csv("distribucion_clases.csv", index=True)

# 6. Top 10 peores clases por F1-Score
clases_f1 = []
for cl in clases:
    if cl in rep_dict:
        clases_f1.append({
            "clase": cl,
            "f1_score": rep_dict[cl]["f1-score"],
            "precision": rep_dict[cl]["precision"],
            "recall": rep_dict[cl]["recall"],
            "support": int(rep_dict[cl]["support"]),
        })
df_f1_sorted = pd.DataFrame(clases_f1).sort_values(by=["f1_score", "support"])
top10_peores_f1 = df_f1_sorted.head(10)

# 7. Top 10 confusiones más frecuentes (esperado -> predicho)
cm = confusion_matrix(y_test, y_test_pred, labels=clases)
confusiones = []
for i, real in enumerate(clases):
    for j, pred in enumerate(clases):
        if i != j and cm[i][j] > 0:
            confusiones.append({
                "real": real,
                "predicho": pred,
                "conteo": int(cm[i][j]),
            })
confusiones = sorted(confusiones, key=lambda x: x["conteo"], reverse=True)
top10_confusiones = confusiones[:10]

# Guardar detalle de confusión y errores
detalle_conf = {}
for i, cl in enumerate(clases):
    conf_con = {}
    for j, otra in enumerate(clases):
        if i != j and cm[i][j] > 0:
            conf_con[otra] = int(cm[i][j])
    detalle_conf[cl] = {
        "precision": rep_dict[cl]["precision"],
        "recall": rep_dict[cl]["recall"],
        "f1-score": rep_dict[cl]["f1-score"],
        "support": rep_dict[cl]["support"],
        "confused_with": conf_con,
    }

with open("confusion_detalle.json", "w", encoding="utf-8") as f:
    json.dump(detalle_conf, f, indent=2, ensure_ascii=False)

errores_list = []
for txt, real, pred in zip(X_test, y_test, y_test_pred):
    if real != pred:
        errores_list.append({"texto": txt, "esperado": real, "predicho": pred})

with open("errores_detalle.json", "w", encoding="utf-8") as f:
    json.dump(errores_list, f, indent=2, ensure_ascii=False)

# ==============================================================================
# SALIDA FORMAL POR CONSOLA
# ==============================================================================
print("=" * 70)
print("             MÉTRICAS DEL MODELO TF-IDF + LinearSVC (MDJLO)            ")
print("=" * 70)
print(f"1. Filas por archivo:")
print(f"   - dataset_nlp.csv (total maestro): {n_dataset} filas")
print(f"   - train_nlp.csv (entrenamiento 80%): {n_train} filas ({n_train/n_dataset*100:.2f}%)")
print(f"   - test_nlp.csv (prueba 20%):         {n_test} filas ({n_test/n_dataset*100:.2f}%)")
print(f"\n2. Número de clases (intenciones): {n_clases}")
print(f"\n3. Métricas en conjunto de prueba (Test 20%, 224 ejemplos):")
print(f"   - Accuracy:    {test_acc:.4f} ({test_acc * 100:.2f}%)")
print(f"   - F1 Macro:    {f1_macro:.4f} ({f1_macro * 100:.2f}%)")
print(f"   - F1 Ponderado:{f1_weighted:.4f} ({f1_weighted * 100:.2f}%)")
print(f"   - Precisión Macro: {p_macro:.4f} ({p_macro * 100:.2f}%)")
print(f"   - Recall Macro:    {r_macro:.4f} ({r_macro * 100:.2f}%)")
print(f"\n4. Accuracy en entrenamiento (Train 80%, 896 ejemplos):")
print(f"   - Accuracy Train: {train_acc:.4f} ({train_acc * 100:.2f}%)")
print(f"\n5. Validación Cruzada Estratificada de 5 Folds (Dataset completo):")
print(f"   - Folds Accuracy: {[round(float(s), 4) for s in cv_acc_scores]}")
print(f"   - Accuracy CV (5-fold): {cv_acc_scores.mean():.4f} (+/- {cv_acc_scores.std():.4f})")
print(f"   - Folds F1 Macro: {[round(float(s), 4) for s in cv_f1_scores]}")
print(f"   - F1 Macro CV (5-fold): {cv_f1_scores.mean():.4f} (+/- {cv_f1_scores.std():.4f})")

print("\n" + "=" * 70)
print("6. TOP 10 PEORES CLASES POR F1-SCORE (Conjunto de Prueba):")
print("=" * 70)
print(f"{'Intención':<35} | {'F1-Score':<8} | {'Prec':<6} | {'Rec':<6} | {'Support':<7}")
print("-" * 70)
for _, r in top10_peores_f1.iterrows():
    print(f"{r['clase']:<35} | {r['f1_score']:<8.4f} | {r['precision']:<6.4f} | {r['recall']:<6.4f} | {int(r['support']):<7}")

print("\n" + "=" * 70)
print("7. TOP 10 CONFUSIONES MÁS FRECUENTES (Esperado -> Predicho):")
print("=" * 70)
print(f"{'Clase Esperada (Real)':<32} -> {'Clase Predicha':<32} | {'Casos':<5}")
print("-" * 70)
for c in top10_confusiones:
    print(f"{c['real']:<32} -> {c['predicho']:<32} | {c['conteo']:<5}")

print("\n" + "=" * 70)
print("8. REPORTE COMPLETO DE CLASIFICACIÓN (Test 20%):")
print("=" * 70)
print(rep_text)
