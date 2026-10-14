"""Entorno de Alembic (FNC-039, ADR-002).

- La URL sale de `construir_uri_bd()`, la misma regla que `create_app()`; nunca
  se escribe en `alembic.ini` ni en código.
- Los metadatos son los de `db` con todos los `app/modules/*/models.py`, para que
  `alembic revision --autogenerate` y `alembic check` comparen el esquema real.
- No llama a `create_app()`: así no corre `db.create_all()` ni el usuario semilla.
- Las pruebas pasan su propia conexión en `config.attributes['connection']`.
"""
import importlib
import pathlib
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool
from sqlalchemy.engine import make_url

from app import db
from app.utils.uri_bd import construir_uri_bd

RAIZ = pathlib.Path(__file__).resolve().parents[1]
# Flask-SQLAlchemy guarda las BD SQLite relativas en `instance/` de la raíz.
CARPETA_INSTANCIA = RAIZ / 'instance'
CARPETA_MODULOS = RAIZ / 'app' / 'modules'


def importar_modelos():
    """Importa `app/modules/*/models.py` para registrar todas las tablas en `db`."""
    for archivo in sorted(CARPETA_MODULOS.glob('*/models.py')):
        importlib.import_module(f'app.modules.{archivo.parent.name}.models')


importar_modelos()

config = context.config
if config.config_file_name is not None and not config.attributes.get('connection'):
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = db.metadata


def url_bd():
    """URL de la app; una ruta SQLite relativa se resuelve igual que en Flask."""
    url = make_url(construir_uri_bd())
    if (url.get_backend_name() == 'sqlite' and url.database
            and url.database != ':memory:'
            and not pathlib.Path(url.database).is_absolute()):
        CARPETA_INSTANCIA.mkdir(exist_ok=True)
        url = url.set(database=str(CARPETA_INSTANCIA / url.database))
    return url


def configurar(**opciones):
    context.configure(target_metadata=target_metadata, compare_type=True,
                      render_as_batch=True, **opciones)


def run_migrations_offline():
    """Genera el SQL sin conectarse (`alembic upgrade head --sql`)."""
    configurar(url=url_bd(), literal_binds=True,
               dialect_opts={'paramstyle': 'named'})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Aplica las migraciones sobre la BD."""
    conexion = config.attributes.get('connection')
    if conexion is not None:
        configurar(connection=conexion)
        with context.begin_transaction():
            context.run_migrations()
        return

    motor = create_engine(url_bd(), poolclass=pool.NullPool)
    with motor.connect() as conexion:
        configurar(connection=conexion)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
