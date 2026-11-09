"""Huella del código cargado al arrancar, para verificar reinicios locales."""
from hashlib import sha256
from pathlib import Path


def revision_codigo():
    raiz = Path(__file__).resolve().parents[1]
    archivos = [raiz / 'app.py', raiz / 'config.py', *sorted((raiz / 'backend').rglob('*.py'))]
    huella = sha256()
    for archivo in archivos:
        huella.update(archivo.relative_to(raiz).as_posix().encode())
        huella.update(archivo.read_bytes())
    return huella.hexdigest()[:12]
