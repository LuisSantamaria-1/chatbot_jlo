"""
database.py
------------
Módulo de compatibilidad retroactiva para scripts y comandos citados en la tesis.
Reenvía a la arquitectura modular en backend.models.
"""

from backend.models import (
    db,
    Tramite,
    Requisito,
    Usuario,
    Rol,
    inicializar_bd,
    poblar_base_datos,
    _limpiar_requisito,
)

if __name__ == "__main__":
    from backend import create_app
    app = create_app()
    with app.app_context():
        inicializar_bd()
        print("\n--- Verificación de datos cargados ---")
        for t in Tramite.query.all():
            print(f"[{t.id_tramite}] {t.nombre}")
