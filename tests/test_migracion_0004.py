"""Migración 0004 (FNC-043): vacía `auth_config.ldap_pass` (SEG-08)."""
from alembic import command
from sqlalchemy import inspect, text

from tests.test_migraciones import migrar, motor_vacio  # noqa: F401 (fixture)

CLAVE = 'clave-ldap-heredada-ficticia'


def _insertar_fila(motor):
    with motor.begin() as conexion:
        conexion.execute(text(
            "INSERT INTO auth_config (ldap_host, ldap_pass) "
            "VALUES ('ldap.pruebas.invalid', :clave)"), {'clave': CLAVE})


def _claves(motor):
    with motor.connect() as conexion:
        return conexion.execute(
            text('SELECT ldap_pass FROM auth_config')).scalars().all()


def test_upgrade_vacia_la_clave_y_conserva_la_columna(motor_vacio):  # noqa: F811
    migrar(motor_vacio, command.upgrade, '0003')
    _insertar_fila(motor_vacio)

    migrar(motor_vacio, command.upgrade, '0004')

    assert _claves(motor_vacio) == [None]
    columnas = {c['name'] for c in inspect(motor_vacio).get_columns('auth_config')}
    assert 'ldap_pass' in columnas


def test_downgrade_no_restaura_la_clave(motor_vacio):  # noqa: F811
    migrar(motor_vacio, command.upgrade, '0003')
    _insertar_fila(motor_vacio)
    migrar(motor_vacio, command.upgrade, '0004')

    migrar(motor_vacio, command.downgrade, '0003')

    assert _claves(motor_vacio) == [None]
