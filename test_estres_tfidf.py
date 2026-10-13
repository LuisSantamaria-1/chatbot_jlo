import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.metrics import classification_report, accuracy_score
import warnings
warnings.filterwarnings('ignore')

# 1. Dataset de Entrenamiento Original
try:
    df_train = pd.read_csv("train_nlp.csv")
except FileNotFoundError:
    print("Error: train_nlp.csv no encontrado.")
    exit()

vectorizador = TfidfVectorizer()
X_train_tfidf = vectorizador.fit_transform(df_train["query"])
clf_tfidf = LinearSVC(random_state=42).fit(X_train_tfidf, df_train["intent"])

# 2. Dataset de Estrés (25 Casos de Prueba Rigurosos)
datos_estres = [
    # Paráfrasis complejas y sinónimos puros
    ("Deseo contraer nupcias con mi conyuge", "consultar_matrimonio_civil"),
    ("Que documentos exigen para casarme por civil", "consultar_matrimonio_civil"),
    ("voy a vender otra mercaderia en mi local comercial", "T_002"),
    ("modificacion de rubro para mi tienda", "T_002"),
    ("perdi la resolucion municipal necesito otra", "T_005"),
    ("quiero una copia de mi autorizacion de funcionamiento", "T_005"),
    ("cual es la tarifa de ese documento", "consultar_costo"),
    ("cuanto dinero debo llevar a la caja", "consultar_costo"),
    ("necesito el permiso para levantar un muro en mi casa", "T_010"),
    ("autorizacion para edificar un segundo piso", "T_010"),
    
    # Lenguaje ciudadano sin normalizar (mala ortografía directa)
    ("qiero aser una bodega en mi ksa", "T_004"),
    ("kuanto demora el tramite de la lincencia", "consultar_plazo"),
    ("req pa abrir mi tiendita al toke", "T_003"),
    ("se me extravio el carton de mi negocio", "T_005"),
    
    # Falsos positivos (Trampas con palabras clave)
    ("fui a la municipalidad para sacar mi licencia pero estaba cerrado, hola", "saludo"),
    ("hola buenas tardes vengo a preguntar", "saludo"),
    ("gracias por el plazo y el costo chau", "despedida"),
    ("hasta luego no quiero tramitar nada", "despedida"),
    
    # Fuera de dominio (Deben ser rechazados)
    ("requisitos para renovar pasaporte", "fuera_de_dominio"),
    ("como preparar ceviche norteño", "fuera_de_dominio"),
    ("donde pago la papeleta de transito", "fuera_de_dominio"),
    ("horario de atencion del banco de la nacion", "fuera_de_dominio"),
    ("quiero sacar cita en essalud", "fuera_de_dominio"),
    ("tramite de divorcio notarial", "fuera_de_dominio"),
    ("cuanto cuesta el pasaje a lima", "fuera_de_dominio")
]

X_estres = [item[0] for item in datos_estres]
y_true = [item[1] for item in datos_estres]

# 3. Predicción y Evaluación Cuantitativa
X_estres_tfidf = vectorizador.transform(X_estres)
y_pred = clf_tfidf.predict(X_estres_tfidf)

print("="*50)
print("  EVALUACIÓN DE ESTRÉS SEMÁNTICO: TF-IDF + SVM")
print("="*50)
print(f"Accuracy (Test de Estrés): {accuracy_score(y_true, y_pred):.4f}\n")
print(classification_report(y_true, y_pred, zero_division=0))