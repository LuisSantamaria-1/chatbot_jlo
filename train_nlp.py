"""
train_nlp.py
------------
Módulo de compatibilidad retroactiva para entrenamiento de NLP.
Reenvía a backend.nlp.entrenamiento.
"""

from backend.nlp.entrenamiento import (
    cargar_dataset,
    construir_pipeline,
    entrenar_y_evaluar,
    exportar_modelo,
)

if __name__ == "__main__":
    df = cargar_dataset()
    modelo = entrenar_y_evaluar(df)
    exportar_modelo(modelo)