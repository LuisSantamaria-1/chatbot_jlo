"""Apoyo semántico local opcional. Nunca descarga modelos ni bloquea el chat.

TF-IDF/SVC y el estado del diálogo siguen disponibles mientras se carga el
modelo multilingüe. Una similitud se usa para proponer, no para inventar datos.
"""

from functools import lru_cache
import logging
import os
import re
from threading import Lock, Thread

logger = logging.getLogger(__name__)
_modelo = None
_estado = 'sin_iniciar'
_candado = Lock()


def iniciar_semantica():
    global _estado
    if os.environ.get('CHAT_SEMANTICA', '1').lower() in {'0', 'false', 'no'}:
        return
    with _candado:
        if _estado != 'sin_iniciar':
            return
        _estado = 'cargando'
    Thread(target=_cargar, name='semantica-local', daemon=True).start()


def _cargar():
    global _modelo, _estado
    try:
        os.environ.setdefault('HF_HUB_OFFLINE', '1')
        import torch
        from sentence_transformers import SentenceTransformer
        torch.set_num_threads(1)
        nombre = os.environ.get('CHAT_MODELO_SEMANTICO', 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        modelo = SentenceTransformer(nombre, local_files_only=True, device='cpu', trust_remote_code=False)
        with _candado:
            _modelo = modelo
            _estado = 'listo'
        logger.info('Apoyo semántico multilingüe local disponible.')
    except Exception as error:
        _estado = 'no_disponible'
        logger.info('Apoyo semántico local no disponible (%s); continúa el diálogo contextual.', type(error).__name__)


def estado_semantica():
    return _estado


@lru_cache(maxsize=64)
def _documentos(macro, registros):
    with _candado:
        return _modelo.encode([texto for _, texto in registros], normalize_embeddings=True,
                              show_progress_bar=False, convert_to_numpy=True, batch_size=16)


def sugerir(macro, texto, opciones, contexto):
    """Devuelve una sugerencia suficientemente separada; nunca carga en la petición."""
    if _estado != 'listo' or len(opciones) < 2 or len(re.findall(r'\w+', texto)) < 3:
        return None
    registros = tuple((k, f'{contexto}. {frase}.') for k, datos in opciones.items()
                      for frase in [datos['etiqueta'], *datos.get('frases', ())[:10]])
    try:
        documentos = _documentos(macro, registros)
        with _candado:
            vector = _modelo.encode([texto], normalize_embeddings=True,
                                    show_progress_bar=False, convert_to_numpy=True)[0]
        puntuaciones = documentos @ vector
        por_opcion = {k: max(float(s) for (clave, _), s in zip(registros, puntuaciones) if clave == k) for k in opciones}
        orden = sorted(por_opcion, key=por_opcion.get, reverse=True)
        puntaje, margen = por_opcion[orden[0]], por_opcion[orden[0]] - por_opcion[orden[1]]
        # Solo propone una confirmación; nunca responde un costo por similitud.
        if puntaje >= 0.45 and margen >= 0.05:
            return orden[0]
    except Exception:
        logger.debug('No se pudo calcular la sugerencia semántica.', exc_info=True)
    return None
