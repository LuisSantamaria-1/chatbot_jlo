import pandas as pd
from sklearn.model_selection import train_test_split
import os

print("Cargando dataset_maestro.csv...")
try:
    # 1. Leemos el archivo maestro que has estado editando manualmente
    df_maestro = pd.read_csv("dataset_nlp.csv")
except FileNotFoundError:
    print("Error: No se encontró dataset_maestro.csv en esta carpeta.")
    exit()

# 2. LIMPIEZA CRÍTICA: Eliminar espacios en blanco accidentales
# Esto corrige el error de "least populated classes have only 1 member"
# fusionando clases mal escritas como ' T_003' con 'T_003'
df_maestro["intent"] = df_maestro["intent"].astype(str).str.strip()
df_maestro["query"] = df_maestro["query"].astype(str).str.strip()

# Limpiar posibles filas vacías que Excel a veces deja al final
df_maestro = df_maestro.dropna(subset=["query", "intent"])
df_maestro = df_maestro[df_maestro["query"] != ""]

print(f"Total de ejemplos listos: {len(df_maestro)}")
print(f"Clases detectadas: {list(df_maestro['intent'].unique())}")

# 3. Split 80/20 Estratificado (misma proporción de clases)
df_train, df_test = train_test_split(
    df_maestro, 
    test_size=0.20, 
    random_state=42, 
    stratify=df_maestro["intent"]
)

df_train.to_csv("train_nlp.csv", index=False)
df_test.to_csv("test_nlp.csv", index=False)
if os.path.exists("data"):
    df_train.to_csv("data/train_nlp.csv", index=False)
    df_test.to_csv("data/test_nlp.csv", index=False)
print(f"Split completado: train_nlp.csv ({len(df_train)} filas) y test_nlp.csv ({len(df_test)} filas).")

# 4. Función para convertir CSV a YAML estructurado de Rasa
def csv_to_rasa_yaml(df, yaml_path):
    os.makedirs(os.path.dirname(yaml_path), exist_ok=True)
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write('version: "3.1"\n\nnlu:\n')
        for intent, grupo in df.groupby("intent"):
            f.write(f"- intent: {intent}\n")
            f.write(f"  examples: |\n")
            for query in grupo["query"]:
                f.write(f"    - {query}\n")

# 5. Generación de los archivos para Rasa
csv_to_rasa_yaml(df_train, "data/nlu_train.yml")
csv_to_rasa_yaml(df_test, "tests/nlu_test.yml")
print("Archivos nlu_train.yml y nlu_test.yml generados exitosamente para Rasa.")