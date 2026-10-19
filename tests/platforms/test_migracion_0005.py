"""Migración 0005 (FNC-046): tipo de integración y grupos en `platforms`."""
from alembic import command
from sqlalchemy import inspect, text

from tests.test_migraciones import migrar, motor_vacio  # noqa: F401 (fixture)

COLUMNAS_NUEVAS = {'integration_type', 'ldap_group_user_dn',
                   'ldap_group_admin_dn', 'groups_status'}


def _plataforma_heredada(motor):
    with motor.begin() as conexion:
        conexion.execute(text("INSERT INTO areas (name) VALUES ('Finanzas')"))
        conexion.execute(text(
            "INSERT INTO platforms (name, description, area_id) "
            "VALUES ('Heredada', 'De NEXUS', 1)"))


def _columnas(motor):
    return {c['name'] for c in inspect(motor).get_columns('platforms')}


def test_upgrade_deja_las_existentes_ldap_sin_grupos(motor_vacio):  # noqa: F811
    migrar(motor_vacio, command.upgrade, '0004')
    _plataforma_heredada(motor_vacio)

    migrar(motor_vacio, command.upgrade, '0005')

    with motor_vacio.connect() as conexion:
        fila = conexion.execute(text(
            'SELECT integration_type, ldap_group_user_dn, ldap_group_admin_dn, '
            'groups_status FROM platforms')).one()
    assert tuple(fila) == ('ldap', None, None, 'sin_verificar')


def test_downgrade_quita_las_columnas_y_conserva_la_fila(motor_vacio):  # noqa: F811
    migrar(motor_vacio, command.upgrade, '0004')
    _plataforma_heredada(motor_vacio)
    migrar(motor_vacio, command.upgrade, '0005')

    migrar(motor_vacio, command.downgrade, '0004')

    assert not COLUMNAS_NUEVAS & _columnas(motor_vacio)
    with motor_vacio.connect() as conexion:
        assert conexion.execute(text('SELECT name FROM platforms')).scalars() \
            .all() == ['Heredada']
