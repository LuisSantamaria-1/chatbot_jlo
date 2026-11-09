"""Recuperación local de alternativas para aclarar paráfrasis, sin inventar datos.

El índice se construye con la configuración de TODAS las macros. La similitud
solo propone una confirmación; nunca sustituye al resolver estricto ni decide
requisitos, riesgo, medidas, modalidad o importes.
"""

from functools import lru_cache
import csv
import re

from sklearn.feature_extraction.text import TfidfVectorizer

from backend.nlp import clasificador as nlp


_AUXILIARES = set('''a al de del el la los las un una unos unas y o en para por con
mi mis su sus se me lo le es era son sea ser que quiero quisiera queremos necesito
necesitamos deseo saber conocer sacar solicitar tramitar gestionar hacer obtener
como puedo podrian ayudarme eso ese esa este esta caso tramite permiso licencia
informacion consulta consultar orientacion sobre acerca favor ayudame dime
pe pues favor porfa si no pero ahora mejor estoy estamos tamos'''.split())
_AUXILIARES.update({'hola','buenas','oye','oe','por','ps'})


def contenido(texto):
    # Variantes regulares en el índice de propuestas, nunca en el resolver
    # estricto: «lotes fusionados» puede sugerir «fusionar/acumular lotes».
    def lema(palabra):
        if len(palabra) >= 7:
            return re.sub(r'(?:ados|adas|ado|ada)$', 'ar', palabra)
        return palabra
    return ' '.join(lema(p) for p in texto.split() if p not in _AUXILIARES)


@lru_cache(maxsize=128)
def _indice(registros):
    textos = [contenido(t) for _, t in registros]
    palabra = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
    caracteres = TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), sublinear_tf=True)
    return palabra, palabra.fit_transform(textos), caracteres, caracteres.fit_transform(textos)


def proponer(macro, texto, opciones, preferida=None):
    """Alternativa candidata: el ciudadano debe confirmarla antes de resolver."""
    # Importación diferida: entendimiento utiliza este módulo al final del turno.
    from backend.chatbot.entendimiento import normalizar_dialogo
    tema = set(macro.removeprefix('consultar_').split('_'))
    consulta = contenido(' '.join(p for p in normalizar_dialogo(texto).split() if p not in tema))
    if not consulta or len(opciones) < 2:
        return None
    registros = tuple((k, normalizar_dialogo(frase)) for k, d in opciones.items()
                      for frase in [d['etiqueta'], *d.get('frases', ()),
                                    *sorted(d.get('palabras', ())),
                                    *(' '.join(g) for g in d.get('todas', ()))])
    palabra, matriz, caracteres, matriz_c = _indice(registros)
    puntos = .7 * (matriz @ palabra.transform([consulta]).T).toarray().ravel()
    puntos += .3 * (matriz_c @ caracteres.transform([consulta]).T).toarray().ravel()
    por_opcion = {k: max(float(s) for (clave, _), s in zip(registros, puntos) if clave == k)
                  for k in opciones}
    orden = sorted(por_opcion, key=por_opcion.get, reverse=True)
    primera, segunda = (por_opcion[k] for k in orden[:2])
    # Dos señales independientes pueden corroborar una propuesta débil de ML.
    # Sigue siendo una pregunta: jamás entrega datos sin la confirmación.
    if preferida in por_opcion and por_opcion[preferida] >= .30 and primera - por_opcion[preferida] <= .08:
        return preferida
    # Exigir palabras compartidas además de caracteres evita luz/luces,
    # lotes/sublotes u otro/otra como única evidencia. No hay difflib.
    tokens = set(consulta.split())
    apoyo = any(tokens & set(contenido(t).split()) for k, t in registros if k == orden[0])
    if apoyo and primera >= .50 and primera - segunda >= .12:
        return orden[0]
    # Un fragmento de una alternativa es una selección conversacional válida
    # para CONFIRMAR: «por etapas» después de preguntar por las dos opciones.
    if tokens and any(len(p)>=5 for p in tokens):
        fragmentos={k for k,t in registros if tokens <= set(contenido(t).split())}
        if len(fragmentos)==1:
            return next(iter(fragmentos))
    return None


@lru_cache(maxsize=4)
def _catalogo_individual(fichas, version_entrenamiento):
    from config import DATA_DIR
    cubiertos = {d[c] for m in nlp.INTENCIONES_MACRO.values() for d in m['opciones'].values()
                 for c in ('id_tramite', 'id_revisor') if d.get(c)}
    opciones = {codigo: {'etiqueta': nombre, 'frases': []}
                for codigo, nombre in fichas if codigo not in cubiertos}
    # Solo entrenamiento: la partición de prueba no entra en la recuperación.
    fuente = DATA_DIR / 'train_nlp.csv'
    if fuente.exists():
        with fuente.open(encoding='utf-8-sig', newline='') as archivo:
            for fila in csv.DictReader(archivo):
                if fila['intent'] in opciones:
                    opciones[fila['intent']]['frases'].append(fila['query'])
    return opciones


def buscar_catalogo(texto, fichas, preferida=None):
    """Procedimientos individuales sin macro; también exigen confirmación."""
    from config import DATA_DIR
    archivo = DATA_DIR / 'train_nlp.csv'
    opciones = _catalogo_individual(tuple(sorted(fichas)), archivo.stat().st_mtime_ns if archivo.exists() else None)
    return proponer('catalogo_municipal', texto, opciones, preferida)


@lru_cache(maxsize=2)
def _familias(version_entrenamiento):
    from config import DATA_DIR
    opciones={k:{'etiqueta':k.removeprefix('consultar_').replace('_',' '),'frases':[]} for k in nlp.INTENCIONES_MACRO}
    archivo=DATA_DIR/'train_nlp.csv'
    if archivo.exists():
        with archivo.open(encoding='utf-8-sig',newline='') as fuente:
            for fila in csv.DictReader(fuente):
                if fila['intent'] in opciones:
                    opciones[fila['intent']]['frases'].append(fila['query'])
    return opciones


def recuperar_familia(texto, preferida=None):
    """Recupera una familia para preguntar atributos, nunca una tarifa por similitud."""
    from config import DATA_DIR
    archivo=DATA_DIR/'train_nlp.csv'
    return proponer('familias_municipales',texto,_familias(archivo.stat().st_mtime_ns if archivo.exists() else None),preferida)
