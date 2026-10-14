"""URI de la base de datos a partir de las variables `DB_*`.

La usan `create_app()` y las migraciones de Alembic (`migrations/env.py`),
para que ambas apunten siempre a la misma BD sin repetir la regla.
"""
import os

# Ruta relativa de SQLite; Flask-SQLAlchemy la resuelve dentro de `instance/`.
SQLITE_URI_POR_DEFECTO = 'sqlite:///nexus.db'


def construir_uri_bd():
    """Devuelve la URI de SQLAlchemy según `DB_ENGINE` (mysql o SQLite)."""
    if os.getenv('DB_ENGINE', 'sqlite') == 'mysql':
        return (f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}"
                f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}"
                f"/{os.getenv('DB_NAME')}")
    return SQLITE_URI_POR_DEFECTO
