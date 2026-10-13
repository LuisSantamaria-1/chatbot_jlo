from backend.admin.routes import admin_bp
from backend.admin.seguridad import requiere_admin

__all__ = ["admin_bp", "requiere_admin"]
