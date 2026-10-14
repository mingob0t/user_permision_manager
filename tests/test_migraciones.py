"""Migraciones de Alembic (FNC-039, ADR-002).

- `alembic upgrade head` sobre un SQLite vacío crea las mismas tablas y
  columnas que los modelos.
- No hay migraciones pendientes respecto de los modelos (autogenerate vacío).
- La bajada a `base` deja la BD vacía y se puede volver a subir.
- Hay una sola cabeza (sin ramas sin fusionar entre tareas paralelas).
"""
import pathlib

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect

from app import db

RAIZ = pathlib.Path(__file__).resolve().parents[1]
TABLA_VERSIONES = 'alembic_version'


@pytest.fixture
def motor_vacio(app, tmp_path):
    """SQLite vacío y aparte del de la app; `app` deja cargados todos los modelos."""
    motor = create_engine(f"sqlite:///{tmp_path / 'migraciones.db'}")
    yield motor
    motor.dispose()


def config_alembic(conexion):
    config = Config(str(RAIZ / 'alembic.ini'))
    config.attributes['connection'] = conexion
    return config


def migrar(motor, accion, revision):
    with motor.begin() as conexion:
        accion(config_alembic(conexion), revision)


def columnas(inspector, tabla):
    return {c['name'] for c in inspector.get_columns(tabla)}


def test_upgrade_head_crea_las_tablas_y_columnas_de_los_modelos(motor_vacio):
    migrar(motor_vacio, command.upgrade, 'head')

    inspector = inspect(motor_vacio)
    tablas = set(inspector.get_table_names()) - {TABLA_VERSIONES}
    assert tablas == set(db.metadata.tables)
    for nombre, tabla in db.metadata.tables.items():
        assert columnas(inspector, nombre) == {c.name for c in tabla.columns}, nombre


def test_no_hay_cambios_de_modelos_sin_migracion(motor_vacio):
    migrar(motor_vacio, command.upgrade, 'head')

    with motor_vacio.connect() as conexion:
        contexto = MigrationContext.configure(
            conexion, opts={'compare_type': True})
        diferencias = compare_metadata(contexto, db.metadata)
    assert diferencias == [], (
        'Hay cambios de modelos sin migración: '
        'alembic revision --autogenerate -m "..."')


def test_alembic_check_no_detecta_pendientes(motor_vacio):
    migrar(motor_vacio, command.upgrade, 'head')

    with motor_vacio.connect() as conexion:
        command.check(config_alembic(conexion))


def test_downgrade_a_base_vacia_la_bd_y_se_puede_volver_a_subir(motor_vacio):
    migrar(motor_vacio, command.upgrade, 'head')
    migrar(motor_vacio, command.downgrade, 'base')

    assert set(inspect(motor_vacio).get_table_names()) <= {TABLA_VERSIONES}

    migrar(motor_vacio, command.upgrade, 'head')
    assert set(inspect(motor_vacio).get_table_names()) - {TABLA_VERSIONES} \
        == set(db.metadata.tables)


def test_hay_una_sola_cabeza():
    script = ScriptDirectory.from_config(Config(str(RAIZ / 'alembic.ini')))
    assert len(script.get_heads()) == 1, script.get_heads()
