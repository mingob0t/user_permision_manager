"""Migración 0011 (FNC-122): columna `users.pref_theme`."""
from alembic import command
from sqlalchemy import inspect, text

from tests.test_migraciones import migrar, motor_vacio  # noqa: F401 (fixture)


def _columnas(motor):
    return {c['name'] for c in inspect(motor).get_columns('users')}


def test_upgrade_agrega_la_columna_con_sistema_en_filas_existentes(
        motor_vacio):  # noqa: F811
    migrar(motor_vacio, command.upgrade, '0010')
    with motor_vacio.begin() as conexion:
        conexion.execute(text(
            "INSERT INTO users (email, role, is_active) "
            "VALUES ('a@pruebas.local', 'usuario', 1)"))

    migrar(motor_vacio, command.upgrade, '0011')

    assert 'pref_theme' in _columnas(motor_vacio)
    with motor_vacio.connect() as conexion:
        assert conexion.execute(
            text('SELECT pref_theme FROM users')).scalars().all() == ['sistema']


def test_downgrade_quita_la_columna(motor_vacio):  # noqa: F811
    migrar(motor_vacio, command.upgrade, '0011')

    migrar(motor_vacio, command.downgrade, '0010')

    assert 'pref_theme' not in _columnas(motor_vacio)
