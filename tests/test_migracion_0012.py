"""Migración 0012 (FNC-132): temas retirados de `users.pref_theme`.

- esmeralda y rosa pasan a claro; obsidiana y violeta, a oscuro.
- Cualquier otro valor fuera de la lista pasa a sistema.
- Es idempotente y el `downgrade` no cambia datos.
"""
import pytest
from alembic import command
from sqlalchemy import text

from tests.test_migraciones import migrar, motor_vacio  # noqa: F401 (fixture)

CONVERSION = {
    'sistema': 'sistema', 'claro': 'claro', 'oscuro': 'oscuro',
    'esmeralda': 'claro', 'rosa': 'claro',
    'obsidiana': 'oscuro', 'violeta': 'oscuro',
    'neon': 'sistema', '': 'sistema', 'OSCURO': 'sistema',
}


def _insertar(motor, temas):
    with motor.begin() as conexion:
        for i, tema in enumerate(temas):
            conexion.execute(
                text("INSERT INTO users (email, role, is_active, pref_theme) "
                     "VALUES (:e, 'usuario', 1, :t)"),
                {'e': f'u{i}@pruebas.local', 't': tema})


def _temas(motor):
    with motor.connect() as conexion:
        filas = conexion.execute(text(
            'SELECT email, pref_theme FROM users ORDER BY id')).all()
    return [t for _, t in filas]


@pytest.mark.parametrize('viejo,nuevo', sorted(CONVERSION.items()))
def test_upgrade_convierte_cada_valor(motor_vacio, viejo, nuevo):  # noqa: F811
    migrar(motor_vacio, command.upgrade, '0011')
    _insertar(motor_vacio, [viejo])

    migrar(motor_vacio, command.upgrade, '0012')

    assert _temas(motor_vacio) == [nuevo]


def test_upgrade_con_todos_los_valores_deja_solo_los_validos(
        motor_vacio):  # noqa: F811
    migrar(motor_vacio, command.upgrade, '0011')
    _insertar(motor_vacio, list(CONVERSION))

    migrar(motor_vacio, command.upgrade, '0012')

    assert _temas(motor_vacio) == list(CONVERSION.values())
    assert set(_temas(motor_vacio)) <= {'sistema', 'claro', 'oscuro'}


def test_es_idempotente(motor_vacio):  # noqa: F811
    migrar(motor_vacio, command.upgrade, '0011')
    _insertar(motor_vacio, list(CONVERSION))
    migrar(motor_vacio, command.upgrade, '0012')
    primera = _temas(motor_vacio)

    migrar(motor_vacio, command.downgrade, '0011')
    migrar(motor_vacio, command.upgrade, '0012')

    assert _temas(motor_vacio) == primera


def test_downgrade_no_cambia_los_datos_ni_la_columna(motor_vacio):  # noqa: F811
    migrar(motor_vacio, command.upgrade, '0011')
    _insertar(motor_vacio, ['violeta', 'rosa'])
    migrar(motor_vacio, command.upgrade, '0012')

    migrar(motor_vacio, command.downgrade, '0011')

    assert _temas(motor_vacio) == ['oscuro', 'claro']
