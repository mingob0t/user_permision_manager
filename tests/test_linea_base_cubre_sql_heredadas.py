"""FNC-028: la línea base 0001 ya contiene el efecto de `utils/migrations/001-004`."""
from alembic import command
from sqlalchemy import inspect

from tests.test_migraciones import migrar, motor_vacio  # noqa: F401 (fixture)

COLUMNAS_PREFERENCIAS = {
    'pref_notifications', 'pref_refresh_interval',
    'pref_tour_enabled', 'pref_email_notifications',
}
COLUMNAS_DRIVE_RETIRADAS = {
    'storage_path', 'can_download', 'can_upload',
    'can_delete', 'is_encrypted', 'password',
}
TABLAS_RETIRADAS = {'storage_stats', 'drive_activity', 'access_requests'}


def test_0001_incluye_las_preferencias_del_001(motor_vacio):  # noqa: F811
    migrar(motor_vacio, command.upgrade, '0001')
    columnas = {c['name'] for c in inspect(motor_vacio).get_columns('users')}
    assert COLUMNAS_PREFERENCIAS <= columnas


def test_0001_no_trae_lo_que_retiraron_el_002_y_el_004(motor_vacio):  # noqa: F811
    migrar(motor_vacio, command.upgrade, '0001')
    inspector = inspect(motor_vacio)
    assert not TABLAS_RETIRADAS & set(inspector.get_table_names())
    columnas = {c['name'] for c in inspector.get_columns('platforms')}
    assert not COLUMNAS_DRIVE_RETIRADAS & columnas
