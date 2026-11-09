"""Genera los conjuntos CSV de entrenamiento y prueba sin consultas compartidas."""

import pandas as pd
from sklearn.model_selection import train_test_split

from backend.nlp.preprocesamiento import preprocesar_texto
from config import CSV_DATASET_PATH, DATA_DIR


def preparar():
    df = pd.read_csv(CSV_DATASET_PATH).dropna(subset=["query", "intent"])
    df["intent"] = df["intent"].astype(str).str.strip()
    df["query"] = df["query"].astype(str).str.strip()
    df = df[df["query"] != ""]
    normalizados = df["query"].map(preprocesar_texto)
    colisiones = df.assign(normalizado=normalizados).groupby("normalizado")["intent"].nunique()
    if (colisiones > 1).any():
        raise ValueError("Hay consultas normalizadas con intenciones distintas; corrige las etiquetas antes de dividir el dataset.")
    df = df.loc[~normalizados.duplicated()].copy()

    train, test = train_test_split(df, test_size=0.20, random_state=42, stratify=df["intent"])
    assert not set(train["query"].map(preprocesar_texto)) & set(test["query"].map(preprocesar_texto)), "Hay fuga de consultas entre train y test."
    train.to_csv(DATA_DIR / "train_nlp.csv", index=False)
    test.to_csv(DATA_DIR / "test_nlp.csv", index=False)
    print(f"Split completado: train_nlp.csv ({len(train)} filas), test_nlp.csv ({len(test)} filas), {df['intent'].nunique()} intenciones.")


if __name__ == "__main__":
    preparar()
