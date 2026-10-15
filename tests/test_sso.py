"""SSO por cabeceras `Remote-*` de Authelia: `/api/v1/auth/sso` y `/context` (FNC-022).

El cliente de pruebas llega desde loopback, que está en `TRUSTED_PROXIES` por
defecto. Para simular otro origen se cambia `TRUSTED_PROXIES` y el
`REMOTE_ADDR` del cliente por nombres ficticios (sin direcciones IP).
"""

import pytest

from app import db
from app.authz import ROLE_ADMIN, ROLE_AREA_ADMIN, ROLE_USER
from app.modules.auth.models import User
from tests.matriz_proteccion import CORREO_SSO_FICTICIO
from tests.matriz_proteccion import CONTRASENA_FICTICIA
from tests.peticiones_auth import (A, MENSAJE_CREDENCIALES, hay_auditoria,
                                   usuario_en_sesion)

PROXY_FICTICIO = 'proxy.pruebas.invalid'
ORIGEN_AJENO = 'cliente.pruebas.invalid'


@pytest.fixture
def sso_activo(monkeypatch):
    monkeypatch.setenv('AUTHELIA_ENABLED', 'true')


def _cabeceras(email=CORREO_SSO_FICTICIO, nombre=None, grupos=None):
    cabeceras = {}
    if email:
        cabeceras['Remote-Email'] = email
    if nombre:
        cabeceras['Remote-Name'] = nombre
    if grupos is not None:
        cabeceras['Remote-Groups'] = grupos
    return cabeceras


def _cuenta_vinculada(crear_usuario, rol, origen='sso', **kwargs):
    """Cuenta ya vinculada al SSO o al directorio (sin contraseña local)."""
    cuenta = crear_usuario(rol, **kwargs)
    cuenta.auth_source = origen
    db.session.commit()
    return cuenta


def _sso(cliente, origen=None, **cabeceras):
    extra = {'environ_base': {'REMOTE_ADDR': origen}} if origen else {}
    return cliente.post(f'{A}/sso', headers=_cabeceras(**cabeceras), **extra)


# --------------------------------------------------------------------------- #
# Origen de las cabeceras
# --------------------------------------------------------------------------- #

def test_sso_deshabilitado_da_400(client):
    respuesta = _sso(client)

    assert respuesta.status_code == 400
    assert usuario_en_sesion(client) is None
    assert User.query.count() == 0


def test_desde_proxy_de_confianza_crea_usuario_y_abre_sesion(client,
                                                             sso_activo):
    respuesta = _sso(client, nombre='Persona SSO', grupos='usuarios')

    assert respuesta.status_code == 200
    assert respuesta.get_json() == {'status': 'success', 'role': ROLE_USER}
    usuario = User.query.filter_by(email=CORREO_SSO_FICTICIO).one()
    assert usuario.auth_source == 'sso'
    assert usuario.password_hash is None
    assert usuario.nombre == 'Persona SSO'
    assert usuario_en_sesion(client) == CORREO_SSO_FICTICIO
    assert hay_auditoria('ACCESO SSO', 'success', target=CORREO_SSO_FICTICIO)


def test_proxy_declarado_en_trusted_proxies_se_acepta(client, sso_activo,
                                                     monkeypatch):
    monkeypatch.setenv('TRUSTED_PROXIES', PROXY_FICTICIO)

    respuesta = _sso(client, origen=PROXY_FICTICIO)

    assert respuesta.status_code == 200
    assert usuario_en_sesion(client) == CORREO_SSO_FICTICIO


def test_desde_origen_no_confiable_se_rechaza(client, sso_activo, monkeypatch):
    monkeypatch.setenv('TRUSTED_PROXIES', PROXY_FICTICIO)

    respuesta = _sso(client, origen=ORIGEN_AJENO, grupos='administrador')

    assert respuesta.status_code == 403
    assert usuario_en_sesion(client) is None
    assert User.query.count() == 0
    assert hay_auditoria('SSO RECHAZADO', 'warning')


def test_loopback_deja_de_ser_confiable_si_no_esta_declarado(client,
                                                            sso_activo,
                                                            monkeypatch):
    monkeypatch.setenv('TRUSTED_PROXIES', PROXY_FICTICIO)

    respuesta = _sso(client)

    assert respuesta.status_code == 403
    assert User.query.count() == 0


def test_sin_cabecera_de_identidad_da_401(client, sso_activo):
    respuesta = _sso(client, email=None, nombre='Sin correo', grupos='usuarios')

    assert respuesta.status_code == 401
    assert usuario_en_sesion(client) is None
    assert User.query.count() == 0


@pytest.mark.xfail(strict=True, reason='SEG-04 / FNC-006: basta la IP del '
                   'proxy; falta el secreto compartido (FNC-004 y FNC-005 son '
                   'de nginx y Next.js, no se prueban desde Flask)')
def test_sin_secreto_compartido_del_proxy_se_rechaza(client, sso_activo):
    respuesta = _sso(client, grupos='administrador')

    assert respuesta.status_code == 401
    assert User.query.count() == 0


# --------------------------------------------------------------------------- #
# Rol a partir de Remote-Groups
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('grupos', ['', 'usuarios, ventas',
                                    'administradores-lectura'])
def test_grupos_sin_coincidencia_exacta_dan_rol_usuario(client, sso_activo,
                                                        grupos):
    respuesta = _sso(client, grupos=grupos)

    assert respuesta.get_json()['role'] == ROLE_USER


def test_conserva_admin_area_asignado_localmente(client, sso_activo,
                                                 crear_usuario):
    _cuenta_vinculada(crear_usuario, ROLE_AREA_ADMIN,
                      email=CORREO_SSO_FICTICIO)

    respuesta = _sso(client, grupos='administrador')

    assert respuesta.get_json()['role'] == ROLE_AREA_ADMIN
    usuario = User.query.filter_by(email=CORREO_SSO_FICTICIO).one()
    assert usuario.role == ROLE_AREA_ADMIN


def test_actualiza_el_nombre_de_un_usuario_existente(client, sso_activo,
                                                     crear_usuario):
    _cuenta_vinculada(crear_usuario, ROLE_USER, origen='ldap',
                      email=CORREO_SSO_FICTICIO)

    _sso(client, nombre='Nombre desde Authelia')

    usuario = User.query.filter_by(email=CORREO_SSO_FICTICIO).one()
    assert usuario.nombre == 'Nombre desde Authelia'
    assert User.query.count() == 1


def test_remote_groups_no_asigna_administrador(client, sso_activo):
    respuesta = _sso(client, grupos='administrador')

    assert respuesta.get_json()['role'] != ROLE_ADMIN


def test_remote_groups_no_cambia_el_rol_del_portal(client, sso_activo,
                                                    crear_usuario):
    # Regresión (FNC-042): el SSO recalculaba el rol en cada acceso y bajaba
    # a `usuario` al administrador sin el grupo de Authelia.
    _cuenta_vinculada(crear_usuario, ROLE_ADMIN, email=CORREO_SSO_FICTICIO)

    respuesta = _sso(client, grupos='usuarios')

    assert respuesta.get_json()['role'] == ROLE_ADMIN
    usuario = User.query.filter_by(email=CORREO_SSO_FICTICIO).one()
    assert usuario.role == ROLE_ADMIN


def test_grupo_de_admin_de_authelia_no_eleva_una_cuenta(client, sso_activo,
                                                         monkeypatch,
                                                         crear_usuario):
    monkeypatch.setenv('AUTHELIA_GROUP_ADMIN', 'admins-portal')
    _cuenta_vinculada(crear_usuario, ROLE_USER, email=CORREO_SSO_FICTICIO)

    respuesta = _sso(client, grupos='admins-portal')

    assert respuesta.get_json()['role'] == ROLE_USER


# --------------------------------------------------------------------------- #
# Cuentas existentes: conflicto con cuentas locales y cuentas desactivadas
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('rol', [ROLE_ADMIN, ROLE_AREA_ADMIN, ROLE_USER])
def test_correo_de_una_cuenta_local_se_bloquea(client, sso_activo,
                                               crear_usuario, rol):
    # Regresión (auditor-seguridad, Alto): `Remote-Email` igual al correo de
    # una cuenta local abría sesión con ella (decisión del dueño 2026-10-15:
    # bloquear y avisar).
    local = crear_usuario(rol, email=CORREO_SSO_FICTICIO,
                          contrasena=CONTRASENA_FICTICIA)
    antes = (local.nombre, local.password_hash)

    respuesta = _sso(client, nombre='Otro Nombre')

    assert respuesta.status_code == 401
    assert respuesta.get_json() == {'status': 'error',
                                    'message': MENSAJE_CREDENCIALES}
    assert usuario_en_sesion(client) is None
    cuenta = db.session.get(User, local.id)
    assert (cuenta.role, cuenta.auth_source) == (rol, 'local')
    assert (cuenta.nombre, cuenta.password_hash) == antes
    assert hay_auditoria('ACCESO BLOQUEADO', 'warning',
                         target=CORREO_SSO_FICTICIO)


def test_correo_con_mayusculas_y_espacios_se_bloquea_sin_duplicar(
        client, sso_activo, crear_usuario):
    # Regresión (re-auditoría, Baja): el correo se comparaba sin normalizar.
    local = crear_usuario(ROLE_ADMIN, email=CORREO_SSO_FICTICIO,
                          contrasena=CONTRASENA_FICTICIA)

    respuesta = _sso(client, email=f'  {CORREO_SSO_FICTICIO.upper()} ')

    assert respuesta.status_code == 401
    assert usuario_en_sesion(client) is None
    assert User.query.count() == 1
    assert db.session.get(User, local.id).auth_source == 'local'


def test_no_cambia_el_origen_de_una_cuenta_ldap(client, sso_activo,
                                                crear_usuario):
    cuenta = _cuenta_vinculada(crear_usuario, ROLE_USER, origen='ldap',
                               email=CORREO_SSO_FICTICIO)

    assert _sso(client).status_code == 200

    assert db.session.get(User, cuenta.id).auth_source == 'ldap'


def test_cuenta_sso_desactivada_no_entra(client, sso_activo, crear_usuario):
    cuenta = _cuenta_vinculada(crear_usuario, ROLE_USER,
                               email=CORREO_SSO_FICTICIO, activo=False)
    nombre = cuenta.nombre

    respuesta = _sso(client, nombre='Otro Nombre')

    assert respuesta.status_code == 401
    assert usuario_en_sesion(client) is None
    assert db.session.get(User, cuenta.id).nombre == nombre


# --------------------------------------------------------------------------- #
# /context
# --------------------------------------------------------------------------- #

def test_context_con_sso_deshabilitado(client):
    datos = client.get(f'{A}/context', headers=_cabeceras()).get_json()

    assert datos['sso_enabled'] is False
    assert datos['sso_user'] is None
    assert datos['authenticated'] is False


def test_context_muestra_la_identidad_si_viene_del_proxy(client, sso_activo):
    datos = client.get(f'{A}/context', headers=_cabeceras()).get_json()

    assert datos['sso_enabled'] is True
    assert datos['sso_user'] == CORREO_SSO_FICTICIO


def test_context_ignora_cabeceras_de_origen_no_confiable(client, sso_activo,
                                                        monkeypatch):
    monkeypatch.setenv('TRUSTED_PROXIES', PROXY_FICTICIO)

    datos = client.get(f'{A}/context', headers=_cabeceras(),
                       environ_base={'REMOTE_ADDR': ORIGEN_AJENO}).get_json()

    assert datos['sso_user'] is None
