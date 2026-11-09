"""Cobertura y aciertos del clasificador al abstenerse por margen transformado.

No interpreta el softmax del margen SVM como una probabilidad calibrada.
Usa únicamente train/test, nunca el modelo final ajustado con el 100 %.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from backend.nlp.entrenamiento import construir_pipeline
from config import REPORTS_DIR


def evaluar():
    base = Path(__file__).resolve().parent
    train = pd.read_csv(base / 'data/train_nlp.csv')
    test = pd.read_csv(base / 'data/test_nlp.csv')
    modelo = construir_pipeline().fit(train['query'], train['intent'])
    margenes = modelo.decision_function(test['query']) / .28
    probabilidades = np.exp(margenes - margenes.max(axis=1, keepdims=True))
    probabilidades /= probabilidades.sum(axis=1, keepdims=True)
    indices = probabilidades.argmax(axis=1)
    confianza = probabilidades.max(axis=1)
    aciertos = modelo.classes_[indices] == test['intent'].to_numpy()
    resultados = []
    for umbral in (0., .35, .54, .70, .80, .90):
        incluidos = confianza >= umbral
        total = int(incluidos.sum())
        resultados.append({'umbral': umbral, 'consultas':total, 'cobertura':float(incluidos.mean()),
                           'accuracy_incluidas':float(aciertos[incluidos].mean()) if total else None})
    REPORTS_DIR.mkdir(exist_ok=True)
    destino = REPORTS_DIR / 'evaluacion_umbral.json'
    destino.write_text(json.dumps(resultados, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(resultados, ensure_ascii=False))


if __name__ == '__main__':
    evaluar()
