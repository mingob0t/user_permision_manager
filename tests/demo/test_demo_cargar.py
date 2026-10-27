"""`flask demo cargar` (FNC-131): datos demo para validar en local.

Solo con `APP_ENV=development`; las contraseñas no están en el código.
"""

import ast
from pathlib import Path

import pytest

from app import db
from app.authz import ROLE_AREA_ADMIN, ROLE_USER
from app.modules.access.models import PlatformAccessGrant
from app.modules.access_requests.models import PlatformAccessRequest
from app.modules.access_requests.tipos import ESTADO_PENDIENTE
from app.modules.auth.models import User
from app.modules.core.models import Area, Platform
from app.modules.demo import datos
from tests.peticiones_auth import (activar_login_local_de_todas,
                                   iniciar_sesion_api, usuario_en_sesion)

CONTRASENA_DE_PRUEBA = 'clave-demo-de-prueba-1'
CARPETA_DEMO = Path(__file__).resolve().parents[2] / 'app' / 'modules' / 'demo'


def cargar(app, argumentos=(), entrada=None):
    return app.test_cli_runner().invoke(args=['demo', 'cargar', *argumentos],
                                        input=entrada)


def contar():
    return (Area.query.count(), Platform.query.count(), User.query.count(),
            PlatformAccessRequest.query.count(),
            PlatformAccessGrant.query.count())


@pytest.fixture
def desarrollo(monkeypatch):
    activar_login_local_de_todas(monkeypatch)


@pytest.mark.parametrize('entorno', [None, '', 'production', 'staging',
                                     'Producción'])
def test_aborta_fuera_de_development_sin_escribir(app, monkeypatch, entorno):
    activar_login_local_de_todas(monkeypatch, entorno=entorno)
    antes = contar()

    resultado = cargar(app, ['--password-desde-stdin'],
                       entrada=CONTRASENA_DE_PRUEBA + '\n')

    assert resultado.exit_code != 0
    assert 'APP_ENV=development' in resultado.output
    assert contar() == antes
    assert CONTRASENA_DE_PRUEBA not in resultado.output


def test_crea_los_datos_esperados(app, desarrollo):
    resultado = cargar(app, ['--password-desde-stdin'],
                       entrada=CONTRASENA_DE_PRUEBA + '\n')

    assert resultado.exit_code == 0, resultado.output
    assert Area.query.count() == len(datos.AREAS)
    assert Platform.query.count() == len(datos.PLATAFORMAS)
    assert 2 <= len(datos.PLATAFORMAS) <= 3
    for plataforma in Platform.query.all():
        assert plataforma.integration_type == 'ldap'
        assert plataforma.ldap_group_user_dn and plataforma.ldap_group_admin_dn
    cuentas = {u.email: u for u in User.query.filter(
        User.email.in_([c.correo for c in datos.CUENTAS]))}
    assert len(cuentas) == len(datos.CUENTAS)
    assert sum(c.role == ROLE_AREA_ADMIN for c in cuentas.values()) == 1
    assert sum(c.role == ROLE_USER for c in cuentas.values()) == 2
    for cuenta in cuentas.values():
        assert cuenta.auth_source == 'local'
        assert cuenta.is_active and cuenta.password_hash
    admin = next(c for c in cuentas.values() if c.role == ROLE_AREA_ADMIN)
    assert [a.name for a in admin.managed_areas] == [datos.AREAS[0].nombre]
    # El admin de área recibe el acceso automático (P6) a las dos plataformas.
    assert PlatformAccessGrant.query.filter_by(user_id=admin.id).count() == 2
    solicitud = PlatformAccessRequest.query.one()
    assert solicitud.status == ESTADO_PENDIENTE
    # La tabla final dice con qué entrar.
    for cuenta in datos.CUENTAS:
        assert cuenta.correo in resultado.output
    assert ROLE_AREA_ADMIN in resultado.output
    assert datos.AREAS[0].nombre in resultado.output
    assert CONTRASENA_DE_PRUEBA not in resultado.output


def test_es_idempotente(app, desarrollo):
    cargar(app, ['--password-desde-stdin'], entrada=CONTRASENA_DE_PRUEBA + '\n')
    primero = contar()
    hashes = {u.email: u.password_hash for u in User.query.all()}

    resultado = cargar(app)

    assert resultado.exit_code == 0, resultado.output
    assert contar() == primero
    assert {u.email: u.password_hash for u in User.query.all()} == hashes
    assert 'ya existía' in resultado.output


def test_las_cuentas_inician_sesion_por_login_local(app, desarrollo):
    cargar(app, ['--password-desde-stdin'], entrada=CONTRASENA_DE_PRUEBA + '\n')

    for cuenta in datos.CUENTAS:
        cliente = app.test_client()
        respuesta = iniciar_sesion_api(cliente, cuenta.correo,
                                       CONTRASENA_DE_PRUEBA)
        assert respuesta.status_code == 200, cuenta.correo
        assert usuario_en_sesion(cliente) == cuenta.correo


def test_pide_la_contrasena_con_confirmacion_en_una_terminal(
        app, desarrollo, monkeypatch):
    monkeypatch.setattr('app.modules.demo.cli.hay_terminal', lambda: True)

    resultado = cargar(app, entrada=(f'{CONTRASENA_DE_PRUEBA}\n'
                                     f'{CONTRASENA_DE_PRUEBA}\n'))

    assert resultado.exit_code == 0, resultado.output
    cuenta = User.query.filter_by(email=datos.CUENTAS[0].correo).one()
    assert cuenta.check_password(CONTRASENA_DE_PRUEBA)
    assert CONTRASENA_DE_PRUEBA not in resultado.output


def test_sin_terminal_ni_opcion_genera_contrasenas_y_las_imprime_una_vez(
        app, desarrollo):
    resultado = cargar(app)

    assert resultado.exit_code == 0, resultado.output
    claves = []
    for cuenta in datos.CUENTAS:
        usuario = User.query.filter_by(email=cuenta.correo).one()
        encontrada = [t for t in resultado.output.split()
                      if usuario.check_password(t)]
        assert len(encontrada) == 1, cuenta.correo
        claves.append(encontrada[0])
    assert len(set(claves)) == len(claves)
    assert all(len(c) >= datos.LARGO_MINIMO_CONTRASENA for c in claves)
    segunda = cargar(app)
    assert not any(c in segunda.output for c in claves)


def test_contrasena_corta_por_stdin_se_rechaza_sin_escribir(app, desarrollo):
    antes = contar()

    resultado = cargar(app, ['--password-desde-stdin'], entrada='corta\n')

    assert resultado.exit_code != 0
    assert contar() == antes


def test_el_codigo_demo_no_trae_contrasenas():
    """Ninguna contraseña fija: ni asignada a un nombre ni pasada a `set_password`."""
    archivos = sorted(CARPETA_DEMO.glob('*.py'))
    assert archivos
    for archivo in archivos:
        for nodo in ast.walk(ast.parse(archivo.read_text(encoding='utf-8'))):
            if isinstance(nodo, ast.Call) and getattr(
                    nodo.func, 'attr', '') in ('set_password',
                                              'generate_password_hash'):
                assert not any(isinstance(a, ast.Constant) for a in nodo.args), (
                    f'{archivo.name}:{nodo.lineno}')
            if isinstance(nodo, (ast.Assign, ast.AnnAssign)):
                destinos = nodo.targets if isinstance(nodo, ast.Assign) \
                    else [nodo.target]
                nombres = [getattr(d, 'id', '') or getattr(d, 'attr', '')
                           for d in destinos]
                if (isinstance(nodo.value, ast.Constant)
                        and isinstance(nodo.value.value, str)
                        and nodo.value.value
                        and any(('pass' in n.lower() or 'contrasena' in n.lower()
                                 or 'clave' in n.lower()) for n in nombres)):
                    pytest.fail(f'{archivo.name}:{nodo.lineno} asigna texto fijo '
                                f'a {nombres}')
