"""Login por directorio: `POST /api/v1/auth/login` con `method: directory` (FNC-022).

`ldap3` se simula con `tests/directorio_falso.py`: no hay red.
"""

import json

import pytest

from app import db
from app.authz import ROLE_ADMIN, ROLE_AREA_ADMIN, ROLE_USER
from app.modules.auth.models import User
from tests.directorio_falso import BASE_DN, DOMINIO_CORREO, instalar_directorio
from tests.matriz_proteccion import CONTRASENA_FICTICIA
from tests.peticiones_auth import (hay_auditoria, iniciar_sesion_api,
                                   usuario_en_sesion)

UID = 'jperez'
CORREO = f'{UID}@{DOMINIO_CORREO}'
CONTRASENA_ERRONEA = 'clave-erronea-de-prueba'
DETALLE_INTERNO = 'detalle-interno-del-servidor-ldap'

DN_GRUPO_ADMIN_AREA = f'cn=admins-area-ti,ou=grupos,{BASE_DN}'
DN_GRUPO_ADMINS = f'cn=administradores,ou=grupos,{BASE_DN}'
DN_GRUPO_PARECIDO = f'cn=sysadmins-lectura,ou=grupos,{BASE_DN}'


@pytest.fixture
def directorio(app, monkeypatch):
    return instalar_directorio(monkeypatch)


def _entrar(cliente, usuario=UID, contrasena=CONTRASENA_FICTICIA):
    return iniciar_sesion_api(cliente, usuario, contrasena, metodo='directory')


# --------------------------------------------------------------------------- #
# Éxito y usuario sombra
# --------------------------------------------------------------------------- #

def test_login_de_directorio_crea_usuario_sombra(client, directorio):
    directorio.agregar(UID, CONTRASENA_FICTICIA, nombre='Juan Pérez')

    respuesta = _entrar(client)

    assert respuesta.status_code == 200
    assert respuesta.get_json() == {'status': 'success', 'role': ROLE_USER}
    usuario = User.query.filter_by(email=CORREO).one()
    assert usuario.role == ROLE_USER
    assert usuario.auth_source == 'ldap'
    assert usuario.password_hash is None
    assert usuario.nombre == 'Juan Pérez'
    assert usuario.last_login_at is not None
    assert usuario_en_sesion(client) == CORREO
    assert hay_auditoria(f'ACCESO DIRECTORIO: {UID}', 'success')


def test_segundo_login_reutiliza_el_usuario_sombra(app, directorio):
    directorio.agregar(UID, CONTRASENA_FICTICIA)

    assert _entrar(app.test_client()).status_code == 200
    assert _entrar(app.test_client()).status_code == 200

    assert User.query.filter_by(email=CORREO).count() == 1


def test_busqueda_usa_el_atributo_configurado(client, directorio):
    directorio.agregar(UID, CONTRASENA_FICTICIA)

    _entrar(client)

    assert directorio.filtros == [f'(sAMAccountName={UID})']


# --------------------------------------------------------------------------- #
# Fallos
# --------------------------------------------------------------------------- #

def test_contrasena_erronea_da_401_sin_sesion(client, directorio):
    directorio.agregar(UID, CONTRASENA_FICTICIA)

    respuesta = _entrar(client, contrasena=CONTRASENA_ERRONEA)

    assert respuesta.status_code == 401
    assert respuesta.get_json()['status'] == 'error'
    assert usuario_en_sesion(client) is None
    assert User.query.count() == 0
    assert hay_auditoria(f'ACCESO FALLIDO: {UID}', 'error')


def test_usuario_inexistente_da_401_y_no_crea_cuenta(client, directorio):
    respuesta = _entrar(client, usuario='no-existe')

    assert respuesta.status_code == 401
    assert usuario_en_sesion(client) is None
    assert User.query.count() == 0


def test_sin_directorio_configurado_da_401(client):
    respuesta = _entrar(client)

    assert respuesta.status_code == 401
    assert usuario_en_sesion(client) is None


@pytest.mark.xfail(strict=True, reason='SEG-01 / FNC-002: un login fallido '
                   'por directorio borra la cuenta local con ese correo')
def test_login_fallido_no_borra_cuentas_locales(client, directorio,
                                                crear_usuario):
    local = crear_usuario(ROLE_ADMIN, contrasena=CONTRASENA_FICTICIA)

    _entrar(client, usuario=local.email, contrasena=CONTRASENA_ERRONEA)

    assert db.session.get(User, local.id) is not None


@pytest.mark.xfail(strict=True, reason='SEG-12 / FNC-002: mensajes distintos '
                   'para usuario inexistente y contraseña mala (enumeración)')
def test_mensaje_uniforme_en_los_fallos(app, directorio):
    directorio.agregar(UID, CONTRASENA_FICTICIA)

    mala = _entrar(app.test_client(), contrasena=CONTRASENA_ERRONEA)
    inexistente = _entrar(app.test_client(), usuario='no-existe')

    assert mala.status_code == inexistente.status_code == 401
    assert mala.get_json() == inexistente.get_json()


@pytest.mark.xfail(strict=True, reason='SEG-12 / FNC-002: el filtro LDAP se '
                   'arma sin escapar lo que escribe el usuario')
def test_filtro_ldap_escapa_comodines(client, directorio):
    directorio.agregar(UID, CONTRASENA_FICTICIA)

    _entrar(client, usuario='j*', contrasena=CONTRASENA_ERRONEA)

    assert directorio.filtros == [r'(sAMAccountName=j\2a)']


@pytest.mark.xfail(strict=True, reason='SEG-12 / FNC-002: el error de LDAP '
                   'llega textual al cliente')
def test_error_del_directorio_no_se_filtra_al_cliente(client, directorio):
    directorio.error = RuntimeError(DETALLE_INTERNO)

    respuesta = _entrar(client)

    assert respuesta.status_code == 401
    assert DETALLE_INTERNO not in respuesta.get_data(as_text=True)


# --------------------------------------------------------------------------- #
# Mapeo de grupos a rol
# --------------------------------------------------------------------------- #

def test_mapeo_de_grupo_exacto_asigna_el_rol(app, client, monkeypatch):
    mapeos = json.dumps([{'group': DN_GRUPO_ADMIN_AREA,
                          'role': ROLE_AREA_ADMIN}])
    directorio = instalar_directorio(monkeypatch, ldap_role_mappings=mapeos)
    directorio.agregar(UID, CONTRASENA_FICTICIA, grupos=[DN_GRUPO_ADMIN_AREA])

    respuesta = _entrar(client)

    assert respuesta.get_json() == {'status': 'success',
                                    'role': ROLE_AREA_ADMIN}
    assert User.query.filter_by(email=CORREO).one().role == ROLE_AREA_ADMIN


def test_sin_grupos_mapeados_queda_como_usuario(app, client, monkeypatch):
    mapeos = json.dumps([{'group': DN_GRUPO_ADMIN_AREA,
                          'role': ROLE_AREA_ADMIN}])
    directorio = instalar_directorio(monkeypatch, ldap_role_mappings=mapeos)
    directorio.agregar(UID, CONTRASENA_FICTICIA,
                       grupos=[f'cn=ventas,ou=grupos,{BASE_DN}'])

    respuesta = _entrar(client)

    assert respuesta.get_json()['role'] == ROLE_USER


@pytest.mark.xfail(strict=True, reason='SEG-10 / FNC-013: el grupo se compara '
                   'por subcadena del DN, no por DN exacto')
@pytest.mark.parametrize('config', [
    {'ldap_group_admin': 'admin'},
    {'ldap_role_mappings': json.dumps([{'group': 'admin',
                                        'role': ROLE_AREA_ADMIN}])},
], ids=['grupo_admin_heredado', 'mapeo_json'])
def test_grupo_parecido_no_cambia_el_rol(app, client, monkeypatch, config):
    directorio = instalar_directorio(monkeypatch, **config)
    directorio.agregar(UID, CONTRASENA_FICTICIA, grupos=[DN_GRUPO_PARECIDO])

    respuesta = _entrar(client)

    assert respuesta.get_json()['role'] == ROLE_USER


@pytest.mark.xfail(strict=True, reason='SEG-10 / FNC-013: el directorio '
                   'asigna administrador (debe haber un solo superadmin)')
def test_directorio_no_asigna_administrador(app, client, monkeypatch):
    directorio = instalar_directorio(monkeypatch,
                                     ldap_group_admin=DN_GRUPO_ADMINS)
    directorio.agregar(UID, CONTRASENA_FICTICIA, grupos=[DN_GRUPO_ADMINS])

    respuesta = _entrar(client)

    assert respuesta.get_json()['role'] != ROLE_ADMIN


@pytest.mark.xfail(strict=True, reason='SEG-10 / FNC-013: el login por '
                   'directorio pisa el rol admin_area asignado en Nexus')
def test_conserva_admin_area_asignado_localmente(client, directorio,
                                                 crear_usuario):
    crear_usuario(ROLE_AREA_ADMIN, email=CORREO)
    directorio.agregar(UID, CONTRASENA_FICTICIA)

    _entrar(client)

    assert User.query.filter_by(email=CORREO).one().role == ROLE_AREA_ADMIN
