"""Migración 0010 (FNC-065): `user_platforms` pasa a accesos `heredado`.

- Cada fila válida se convierte en un acceso `heredado`, nivel `usuario`,
  estado `activo`, sin actor ni solicitud ni trabajo encolado.
- Se omiten (y se cuentan): acceso vigente previo (P5), cuenta inactiva,
  plataforma inactiva, cuenta que no es del área de la plataforma (P1) y
  superadmin (acceso por defecto, P6).
- Idempotente; el downgrade quita lo que creó y no tocó nadie más.
"""
import importlib.util
import pathlib

from alembic import command
from sqlalchemy import inspect, text

from tests.test_migraciones import RAIZ, migrar, motor_vacio  # noqa: F401

ARCHIVO = next(pathlib.Path(RAIZ / 'migrations' / 'versions').glob('0010_*.py'),
               None)
AHORA = '2026-10-21 10:00:00'


def _cargar():
    especificacion = importlib.util.spec_from_file_location('mig0010', ARCHIVO)
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    return modulo


def _ejecutar(motor, sql, **params):
    with motor.begin() as conexion:
        conexion.execute(text(sql), params)


def _escena(motor):
    """Datos en el esquema 0009; devuelve los ids por nombre."""
    _ejecutar(motor, "INSERT INTO areas (id, name, status) VALUES "
                     "(1, 'Finanzas', 'Activo'), (2, 'Ventas', 'Activo')")
    _ejecutar(motor, "INSERT INTO platforms (id, name, description, area_id, "
                     "status, integration_type, groups_status) VALUES "
                     "(1, 'Contabilidad', 'x', 1, 'Activo', 'ldap', 'sin_verificar'), "
                     "(2, 'Nómina', 'x', 1, 'Activo', 'ldap', 'sin_verificar'), "
                     "(3, 'Vieja', 'x', 1, 'Inactivo', 'ldap', 'sin_verificar'), "
                     "(4, 'CRM', 'x', 2, 'Activo', 'ldap', 'sin_verificar')")
    _ejecutar(motor, "INSERT INTO users (id, email, role, is_active) VALUES "
                     "(1, 'ana@pruebas.local', 'usuario', 1), "
                     "(2, 'baja@pruebas.local', 'usuario', 0), "
                     "(3, 'luis@pruebas.local', 'usuario', 1), "
                     "(4, 'root@pruebas.local', 'administrador', 1), "
                     "(5, 'eva@pruebas.local', 'admin_area', 1)")
    _ejecutar(motor, "INSERT INTO user_areas (user_id, area_id) VALUES "
                     "(1, 1), (2, 1), (3, 2), (4, 1), (5, 1)")
    # Filas de user_platforms: 1 válida (ana-1), ana-2 con acceso previo,
    # ana-3 plataforma inactiva, baja-1 cuenta inactiva, luis-1 sin el área,
    # root-1 superadmin, eva-1 válida, ana-4 (otra área, ana no es de Ventas).
    _ejecutar(motor, "INSERT INTO user_platforms (user_id, platform_id) VALUES "
                     "(1, 1), (1, 2), (1, 3), (2, 1), (3, 1), (4, 1), (5, 1), "
                     "(1, 4)")
    _ejecutar(motor, "INSERT INTO platform_access_grants (user_id, platform_id, "
                     "level, origin, request_id, granted_at, status, updated_at, "
                     "slot_vigente, slot_ocupante) VALUES "
                     "(1, 2, 'usuario', 'solicitud', 7, :ahora, 'activo', :ahora, "
                     "1, 1)", ahora=AHORA)


def _accesos(motor):
    with motor.connect() as conexion:
        filas = conexion.execute(text(
            "SELECT user_id, platform_id, level, origin, status, request_id, "
            "granted_by, last_job_id, slot_vigente, slot_ocupante "
            "FROM platform_access_grants ORDER BY user_id, platform_id"))
        return [tuple(f) for f in filas]


def _preparar(motor):
    migrar(motor, command.upgrade, '0009')
    _escena(motor)


def test_la_migracion_existe_sobre_la_0009():
    assert ARCHIVO is not None, 'Falta migrations/versions/0010_*.py'
    modulo = _cargar()
    assert (modulo.revision, modulo.down_revision) == ('0010', '0009')


def test_upgrade_convierte_las_filas_validas_en_accesos_heredados(
        motor_vacio):  # noqa: F811
    _preparar(motor_vacio)

    migrar(motor_vacio, command.upgrade, '0010')

    assert _accesos(motor_vacio) == [
        (1, 1, 'usuario', 'heredado', 'activo', None, None, None, 1, 1),
        (1, 2, 'usuario', 'solicitud', 'activo', 7, None, None, 1, 1),
        (5, 1, 'usuario', 'heredado', 'activo', None, None, None, 1, 1),
    ]


def test_upgrade_no_encola_trabajos_ni_toca_user_platforms(
        motor_vacio):  # noqa: F811
    _preparar(motor_vacio)

    migrar(motor_vacio, command.upgrade, '0010')

    with motor_vacio.connect() as conexion:
        trabajos = conexion.execute(
            text('SELECT COUNT(*) FROM provisioning_jobs')).scalar()
        filas = conexion.execute(
            text('SELECT COUNT(*) FROM user_platforms')).scalar()
    assert trabajos == 0
    assert filas == 8  # la tabla queda intacta (obsoleta, no se borra)
    assert 'user_platforms' in inspect(motor_vacio).get_table_names()


def test_upgrade_cuenta_y_registra_las_omisiones(motor_vacio):  # noqa: F811
    _preparar(motor_vacio)

    migrar(motor_vacio, command.upgrade, '0010')

    with motor_vacio.connect() as conexion:
        registro = conexion.execute(text(
            "SELECT \"user\", action, module, status, detail FROM audit_logs "
            "WHERE action = 'migracion_accesos_heredados'")).mappings().all()
    assert len(registro) == 1
    fila = registro[0]
    assert (fila['user'], fila['module'], fila['status']) == \
        ('sistema', 'Accesos', 'info')
    detalle = fila['detail']
    assert 'filas=8' in detalle and 'migradas=2' in detalle
    assert 'acceso_vigente=1' in detalle
    assert 'cuenta_inactiva=1' in detalle
    assert 'plataforma_inactiva=1' in detalle
    assert 'fuera_del_area=2' in detalle      # luis-1 y ana-4
    assert 'superadmin=1' in detalle


def test_la_funcion_es_idempotente(motor_vacio):  # noqa: F811
    _preparar(motor_vacio)
    migrar(motor_vacio, command.upgrade, '0010')
    antes = _accesos(motor_vacio)

    with motor_vacio.begin() as conexion:
        resultado = _cargar().migrar_asignaciones(conexion)

    assert resultado['migradas'] == 0
    assert _accesos(motor_vacio) == antes


def test_no_resucita_un_acceso_heredado_ya_revocado(motor_vacio):  # noqa: F811
    _preparar(motor_vacio)
    migrar(motor_vacio, command.upgrade, '0010')
    _ejecutar(motor_vacio, "UPDATE platform_access_grants SET status = "
                           "'revocado', slot_vigente = NULL, slot_ocupante = NULL "
                           "WHERE user_id = 1 AND platform_id = 1")

    with motor_vacio.begin() as conexion:
        resultado = _cargar().migrar_asignaciones(conexion)

    assert resultado['migradas'] == 0
    assert [a[4] for a in _accesos(motor_vacio)
            if a[:2] == (1, 1)] == ['revocado']


def test_downgrade_quita_los_heredados_sin_trabajo_y_deja_lo_demas(
        motor_vacio):  # noqa: F811
    _preparar(motor_vacio)
    migrar(motor_vacio, command.upgrade, '0010')

    migrar(motor_vacio, command.downgrade, '0009')

    assert _accesos(motor_vacio) == [
        (1, 2, 'usuario', 'solicitud', 'activo', 7, None, None, 1, 1)]
    with motor_vacio.connect() as conexion:
        assert conexion.execute(
            text('SELECT COUNT(*) FROM user_platforms')).scalar() == 8


def test_downgrade_conserva_el_heredado_que_ya_tuvo_trabajo(
        motor_vacio):  # noqa: F811
    _preparar(motor_vacio)
    migrar(motor_vacio, command.upgrade, '0010')
    _ejecutar(motor_vacio, "UPDATE platform_access_grants SET last_job_id = 9 "
                           "WHERE user_id = 1 AND platform_id = 1")

    migrar(motor_vacio, command.downgrade, '0009')

    assert (1, 1) in [a[:2] for a in _accesos(motor_vacio)]


def test_subir_bajar_y_volver_a_subir(motor_vacio):  # noqa: F811
    _preparar(motor_vacio)
    migrar(motor_vacio, command.upgrade, '0010')
    primero = _accesos(motor_vacio)
    migrar(motor_vacio, command.downgrade, '0009')

    migrar(motor_vacio, command.upgrade, '0010')

    assert _accesos(motor_vacio) == primero
