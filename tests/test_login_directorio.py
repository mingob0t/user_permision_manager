"""Login por directorio: `POST /api/v1/auth/login` con `method: directory` (FNC-022, FNC-042).

El login usa el cliente centralizado; `tests/directorio_falso.py` lo conecta a
un `ldap3` `MOCK_SYNC`: no hay red.
"""

import json

import pytest

from app import db
from app.authz import ROLE_ADMIN, ROLE_AREA_ADMIN, ROLE_USER
from app.modules.auth.models import User
from tests.directorio_falso import BASE_DN, DOMINIO_CORREO, instalar_directorio
from tests.matriz_proteccion import CONTRASENA_FICTICIA
from tests.peticiones_auth import (MENSAJE_CREDENCIALES, hay_auditoria,
                                   iniciar_sesion_api, usuario_en_sesion)

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
    assert hay_auditoria('ACCESO DIRECTORIO', 'success', target=UID)


def test_segundo_login_reutiliza_el_usuario_sombra(app, directorio):
    directorio.agregar(UID, CONTRASENA_FICTICIA)

    assert _entrar(app.test_client()).status_code == 200
    assert _entrar(app.test_client()).status_code == 200

    assert User.query.filter_by(email=CORREO).count() == 1


def test_busqueda_usa_el_atributo_uid_por_defecto(client, directorio):
    directorio.agregar(UID, CONTRASENA_FICTICIA)

    assert _entrar(client).status_code == 200

    assert directorio.filtros == [f'(uid={UID})']


def test_busqueda_usa_ldap_user_attr(app, client, monkeypatch):
    directorio = instalar_directorio(monkeypatch,
                                     variables={'LDAP_USER_ATTR': 'cn'})
    directorio.agregar(UID, CONTRASENA_FICTICIA)

    assert _entrar(client).status_code == 200

    assert directorio.filtros == [f'(cn={UID})']


def test_config_heredada_de_la_bd_no_activa_el_directorio(client, monkeypatch):
    # Sin `LDAP_URL` el directorio está inactivo aunque `auth_config` tenga
    # host (el login ya no abre conexiones propias con CERT_NONE).
    from app.modules.auth.models import AuthConfig
    db.session.add(AuthConfig(ldap_host='ldap.pruebas.invalid',
                              ldap_base_dn=BASE_DN))
    db.session.commit()

    respuesta = _entrar(client)

    assert respuesta.status_code == 401
    assert respuesta.get_json()['message'] == MENSAJE_CREDENCIALES


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
    assert hay_auditoria('ACCESO FALLIDO', 'error', target=UID)


def test_usuario_inexistente_da_401_y_no_crea_cuenta(client, directorio):
    respuesta = _entrar(client, usuario='no-existe')

    assert respuesta.status_code == 401
    assert usuario_en_sesion(client) is None
    assert User.query.count() == 0


def test_sin_directorio_configurado_da_401(client):
    respuesta = _entrar(client)

    assert respuesta.status_code == 401
    assert usuario_en_sesion(client) is None


def test_login_fallido_no_borra_cuentas_locales(client, directorio,
                                                crear_usuario):
    local = crear_usuario(ROLE_ADMIN, contrasena=CONTRASENA_FICTICIA)

    _entrar(client, usuario=local.email, contrasena=CONTRASENA_ERRONEA)

    assert db.session.get(User, local.id) is not None


def test_mensaje_uniforme_en_los_fallos(app, directorio):
    directorio.agregar(UID, CONTRASENA_FICTICIA)

    mala = _entrar(app.test_client(), contrasena=CONTRASENA_ERRONEA)
    inexistente = _entrar(app.test_client(), usuario='no-existe')

    assert mala.status_code == inexistente.status_code == 401
    assert mala.get_json() == inexistente.get_json()
    assert mala.get_json() == {'status': 'error',
                               'message': MENSAJE_CREDENCIALES}


def test_fallo_de_directorio_responde_igual_que_el_login_local(app,
                                                               directorio):
    directorio.agregar(UID, CONTRASENA_FICTICIA)

    del_directorio = _entrar(app.test_client(), contrasena=CONTRASENA_ERRONEA)
    local = iniciar_sesion_api(app.test_client(), UID, CONTRASENA_ERRONEA,
                               metodo='local')

    assert del_directorio.status_code == local.status_code == 401
    assert del_directorio.get_json() == local.get_json()


def test_motivo_del_fallo_queda_solo_en_la_auditoria(client, directorio):
    from app.modules.audit.models import AuditLog

    _entrar(client, usuario='no-existe')

    registro = AuditLog.query.filter_by(action='ACCESO FALLIDO',
                                        target='no-existe').one()
    assert 'no encontrado' in registro.detail


def test_login_fallido_no_modifica_la_cuenta_local(client, directorio,
                                                   crear_usuario):
    # El identificador escrito no enlaza cuentas locales (SEC-AUTH-08).
    local = crear_usuario(ROLE_ADMIN, email=UID,
                          contrasena=CONTRASENA_FICTICIA)
    directorio.agregar(UID, CONTRASENA_FICTICIA)

    _entrar(client, contrasena=CONTRASENA_ERRONEA)

    cuenta = db.session.get(User, local.id)
    assert (cuenta.email, cuenta.role, cuenta.auth_source) == \
        (UID, ROLE_ADMIN, 'local')


def test_identificador_igual_a_una_cuenta_local_no_la_toma(client, directorio,
                                                           crear_usuario):
    # Regresión: el login de directorio buscaba la cuenta local también por
    # lo escrito; una persona del directorio con uid igual al usuario local
    # (p. ej. el superadmin) se quedaba con esa cuenta y su rol.
    local = crear_usuario(ROLE_ADMIN, email=UID,
                          contrasena=CONTRASENA_FICTICIA)
    directorio.agregar(UID, CONTRASENA_FICTICIA)

    respuesta = _entrar(client)

    assert respuesta.get_json() == {'status': 'success', 'role': ROLE_USER}
    assert usuario_en_sesion(client) == CORREO
    cuenta = db.session.get(User, local.id)
    assert (cuenta.email, cuenta.role, cuenta.auth_source) == \
        (UID, ROLE_ADMIN, 'local')


def test_persona_sin_correo_no_toma_la_cuenta_local_de_su_uid(
        client, directorio, crear_usuario):
    # Regresión: sin `mail`, el código anterior enlazaba la cuenta local cuyo
    # correo era lo escrito (p. ej. el superadmin local `admin`).
    local = crear_usuario(ROLE_ADMIN, email=UID,
                          contrasena=CONTRASENA_FICTICIA)
    directorio.agregar(UID, CONTRASENA_FICTICIA, correo='')

    respuesta = _entrar(client)

    assert respuesta.status_code == 401
    assert respuesta.get_json()['message'] == MENSAJE_CREDENCIALES
    assert usuario_en_sesion(client) is None
    cuenta = db.session.get(User, local.id)
    assert (cuenta.email, cuenta.role, cuenta.auth_source) == \
        (UID, ROLE_ADMIN, 'local')
    assert User.query.count() == 1


def test_contrasena_vacia_no_llega_al_directorio(app, directorio):
    from app.modules.auth.services import authenticate_user_ldap
    directorio.agregar(UID, CONTRASENA_FICTICIA)

    resultado = authenticate_user_ldap(UID, '')

    assert resultado['status'] == 'error'
    assert resultado['message'] == MENSAJE_CREDENCIALES
    assert directorio.filtros == []


def test_identificador_ambiguo_da_la_respuesta_unica(client, directorio):
    directorio.agregar(UID, CONTRASENA_FICTICIA)
    # Segunda persona con el mismo uid en otra rama de la OU de personas.
    directorio._agregar(f'cn=duplicado,ou=personas,{BASE_DN}',
                        objectClass='inetOrgPerson', uid=UID, cn='duplicado',
                        sn='duplicado', userPassword=CONTRASENA_FICTICIA)

    respuesta = _entrar(client)

    assert respuesta.status_code == 401
    assert respuesta.get_json()['message'] == MENSAJE_CREDENCIALES


def test_filtro_ldap_escapa_comodines(client, directorio):
    directorio.agregar(UID, CONTRASENA_FICTICIA)

    _entrar(client, usuario='j*', contrasena=CONTRASENA_ERRONEA)

    assert directorio.filtros == [r'(uid=j\2a)']


def test_error_del_directorio_no_se_filtra_al_cliente(client, directorio):
    directorio.error = RuntimeError(DETALLE_INTERNO)

    respuesta = _entrar(client)

    assert respuesta.status_code == 401
    assert DETALLE_INTERNO not in respuesta.get_data(as_text=True)


# --------------------------------------------------------------------------- #
# Mapeo de grupos a rol
# --------------------------------------------------------------------------- #

def test_mapeo_de_grupo_exacto_ya_no_asigna_el_rol(app, client, monkeypatch):
    # FNC-042 (RF-04): el rol lo asigna solo el superadmin en el portal; antes
    # un mapeo exacto daba `admin_area` (prueba invertida).
    mapeos = json.dumps([{'group': DN_GRUPO_ADMIN_AREA,
                          'role': ROLE_AREA_ADMIN}])
    directorio = instalar_directorio(monkeypatch, ldap_role_mappings=mapeos)
    directorio.agregar(UID, CONTRASENA_FICTICIA, grupos=[DN_GRUPO_ADMIN_AREA])

    respuesta = _entrar(client)

    assert respuesta.get_json() == {'status': 'success', 'role': ROLE_USER}
    assert User.query.filter_by(email=CORREO).one().role == ROLE_USER


def test_sin_grupos_mapeados_queda_como_usuario(app, client, monkeypatch):
    mapeos = json.dumps([{'group': DN_GRUPO_ADMIN_AREA,
                          'role': ROLE_AREA_ADMIN}])
    directorio = instalar_directorio(monkeypatch, ldap_role_mappings=mapeos)
    directorio.agregar(UID, CONTRASENA_FICTICIA,
                       grupos=[f'cn=ventas,ou=grupos,{BASE_DN}'])

    respuesta = _entrar(client)

    assert respuesta.get_json()['role'] == ROLE_USER


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


def test_directorio_no_asigna_administrador(app, client, monkeypatch):
    directorio = instalar_directorio(monkeypatch,
                                     ldap_group_admin=DN_GRUPO_ADMINS)
    directorio.agregar(UID, CONTRASENA_FICTICIA, grupos=[DN_GRUPO_ADMINS])

    respuesta = _entrar(client)

    assert respuesta.get_json()['role'] != ROLE_ADMIN


def test_conserva_admin_area_asignado_localmente(client, directorio,
                                                 crear_usuario):
    crear_usuario(ROLE_AREA_ADMIN, email=CORREO)
    directorio.agregar(UID, CONTRASENA_FICTICIA)

    _entrar(client)

    assert User.query.filter_by(email=CORREO).one().role == ROLE_AREA_ADMIN


def test_directorio_no_degrada_el_rol_del_portal(client, directorio,
                                                 crear_usuario):
    # Regresión: cada login recalculaba el rol desde los grupos y bajaba a
    # `usuario` al administrador asignado en el portal.
    crear_usuario(ROLE_ADMIN, email=CORREO)
    directorio.agregar(UID, CONTRASENA_FICTICIA)

    respuesta = _entrar(client)

    assert respuesta.get_json()['role'] == ROLE_ADMIN
    assert User.query.filter_by(email=CORREO).one().role == ROLE_ADMIN
