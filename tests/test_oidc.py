"""Inicio de sesión por OIDC con Authelia (FNC-141, ADR-009, contrato `autenticacion`).

Proveedor simulado (`tests/oidc_simulado.py`): firma ID tokens reales y no usa red.
"""

import pytest

from app import db
from app.authz import ROLE_ADMIN, ROLE_AREA_ADMIN, ROLE_USER
from app.modules.audit.models import AuditLog
from app.modules.auth.models import User
from tests.oidc_simulado import (CLIENT_ID, CLIENT_SECRET, CODIGO, CORREO,
                                 ISSUER, NOMBRE, REDIRECT_URI, SUB,
                                 desafio_s256)
from tests.peticiones_auth import A, hay_auditoria, usuario_en_sesion


def _destino(respuesta):
    return respuesta.headers['Location']


def _sin_sesion_y_con_error(cliente, respuesta, codigo):
    assert respuesta.status_code == 302
    assert _destino(respuesta) == f'/login?error={codigo}'
    assert usuario_en_sesion(cliente) is None


def _cuenta_vinculada(crear_usuario, rol=ROLE_USER, origen='sso', sub=None, **kwargs):
    """Cuenta del directorio o de Authelia, sin contraseña local."""
    cuenta = crear_usuario(rol, **kwargs)
    cuenta.auth_source = origen
    cuenta.oidc_sub = sub
    db.session.commit()
    return cuenta


# --------------------------------------------------------------------------- #
# Inicio del flujo
# --------------------------------------------------------------------------- #

def test_login_redirige_a_authelia_con_pkce_state_y_nonce(client, oidc):
    respuesta, parametros = oidc.empezar(client)

    assert respuesta.status_code == 302
    assert _destino(respuesta).startswith(f'{ISSUER}/api/oidc/authorization?')
    assert parametros['response_type'] == 'code'
    assert parametros['client_id'] == CLIENT_ID
    assert parametros['redirect_uri'] == REDIRECT_URI
    assert parametros['scope'] == 'openid profile email groups'
    assert parametros['code_challenge_method'] == 'S256'
    assert parametros['code_challenge']
    assert parametros['state'] and parametros['nonce']
    assert 'code_verifier' not in parametros
    assert 'client_secret' not in _destino(respuesta)


def test_login_sin_configuracion_vuelve_al_acceso(client, monkeypatch):
    respuesta = client.get(f'{A}/oidc/login')

    _sin_sesion_y_con_error(client, respuesta, 'oidc_no_disponible')


def test_login_con_authelia_caido_vuelve_al_acceso(client, oidc):
    oidc.metadatos = lambda: (_ for _ in ()).throw(RuntimeError('sin red'))

    respuesta = client.get(f'{A}/oidc/login')

    _sin_sesion_y_con_error(client, respuesta, 'oidc_no_disponible')
    assert hay_auditoria('ACCESO OIDC FALLIDO', 'error')


def test_el_codigo_se_canjea_con_el_verificador_del_desafio(client, oidc):
    _, parametros = oidc.empezar(client)

    oidc.callback(client, parametros['state'])

    canje = oidc.peticion_del_token()
    assert canje['grant_type'] == 'authorization_code'
    assert canje['code'] == CODIGO
    assert desafio_s256(canje['code_verifier']) == parametros['code_challenge']


# --------------------------------------------------------------------------- #
# Callback correcto y cuenta
# --------------------------------------------------------------------------- #

def test_primer_inicio_crea_cuenta_usuario_con_sub_y_abre_sesion(client, oidc):
    respuesta = oidc.entrar(client)

    assert respuesta.status_code == 302
    assert _destino(respuesta) == '/dashboard'
    cuenta = User.query.filter_by(email=CORREO).one()
    assert (cuenta.role, cuenta.auth_source) == (ROLE_USER, 'sso')
    assert cuenta.oidc_sub == SUB
    assert cuenta.password_hash is None
    assert cuenta.nombre == NOMBRE
    assert usuario_en_sesion(client) == CORREO
    assert hay_auditoria('ACCESO SSO', 'success', target=CORREO)


def test_cuenta_nueva_avisa_por_correo_una_vez(client, oidc, monkeypatch):
    from app.modules.api import auth
    avisos = []
    monkeypatch.setattr(auth, 'avisar_usuario_creado',
                        lambda *args: avisos.append(args))

    oidc.entrar(client)
    client.post(f'{A}/logout')
    oidc.entrar(client)

    assert len(avisos) == 1


def test_la_sesion_previa_no_sobrevive_al_inicio(client, oidc):
    with client.session_transaction() as sesion:
        sesion['dato_previo'] = 'valor'

    oidc.entrar(client)

    with client.session_transaction() as sesion:
        assert 'dato_previo' not in sesion
        assert sesion.permanent is True


def test_primer_inicio_vincula_por_correo_y_conserva_rol_y_origen(
        client, oidc, crear_usuario):
    oidc.userinfo['groups'] = ['app-aduana-admins']
    cuenta = _cuenta_vinculada(crear_usuario, ROLE_AREA_ADMIN, origen='ldap',
                               email=CORREO)

    oidc.entrar(client)

    db.session.refresh(cuenta)
    assert cuenta.oidc_sub == SUB
    assert (cuenta.role, cuenta.auth_source) == (ROLE_AREA_ADMIN, 'ldap')
    assert User.query.count() == 1
    assert usuario_en_sesion(client) == CORREO


def test_correo_con_mayusculas_se_vincula_sin_duplicar(client, oidc,
                                                       crear_usuario):
    _cuenta_vinculada(crear_usuario, email=CORREO)
    oidc.userinfo['email'] = f'  {CORREO.upper()} '

    oidc.entrar(client)

    assert User.query.count() == 1


def test_despues_entra_solo_por_sub_aunque_cambie_el_correo(client, oidc,
                                                            crear_usuario):
    cuenta = _cuenta_vinculada(crear_usuario, email=CORREO, sub=SUB)
    oidc.userinfo['email'] = 'otro.correo@pruebas.invalid'

    respuesta = oidc.entrar(client)

    assert _destino(respuesta) == '/dashboard'
    assert User.query.count() == 1
    assert usuario_en_sesion(client) == cuenta.email


def test_actualiza_el_nombre_de_la_cuenta(client, oidc, crear_usuario):
    cuenta = _cuenta_vinculada(crear_usuario, email=CORREO, sub=SUB)
    oidc.userinfo['name'] = 'Nombre Nuevo'

    oidc.entrar(client)

    db.session.refresh(cuenta)
    assert cuenta.nombre == 'Nombre Nuevo'


def test_sin_name_usa_el_correo(client, oidc):
    del oidc.userinfo['name']

    oidc.entrar(client)

    assert User.query.filter_by(email=CORREO).one().nombre == CORREO


# --------------------------------------------------------------------------- #
# Autorización estricta por grupos mapeados (FNC-143, FNC-144)
# --------------------------------------------------------------------------- #

def test_sin_grupos_autorizados_se_rechaza_acceso(client, oidc):
    oidc.userinfo['groups'] = []

    respuesta = oidc.entrar(client)

    _sin_sesion_y_con_error(client, respuesta, 'acceso_denegado')
    assert User.query.filter_by(email=CORREO).first() is None
    assert hay_auditoria('ACCESO OIDC FALLIDO', 'error')


@pytest.mark.parametrize('claims', [
    {'groups': ['admins', 'administradores'], 'role': ROLE_ADMIN},
    {'groups': ['marketing', 'contabilidad']},
    {'roles': [ROLE_ADMIN], 'is_admin': True, 'groups': []},
])
def test_grupos_y_roles_no_autorizados_se_rechazan_con_acceso_denegado(
        client, oidc, claims):
    oidc.userinfo.update(claims)
    oidc.id_token_cambios.update(claims)

    respuesta = oidc.entrar(client)

    _sin_sesion_y_con_error(client, respuesta, 'acceso_denegado')
    assert User.query.filter_by(email=CORREO).first() is None


def test_claim_role_en_token_no_eleva_privilegios_de_usuario(client, oidc):
    # El usuario pertenece a app-aduana-users pero el token trae role: 'administrador'
    oidc.userinfo.update({'groups': ['app-aduana-users'], 'role': ROLE_ADMIN})
    oidc.id_token_cambios.update({'role': ROLE_ADMIN})

    oidc.entrar(client)

    assert User.query.filter_by(email=CORREO).one().role == ROLE_USER


def test_cuenta_existente_sin_grupos_autorizados_no_puede_entrar(
        client, oidc, crear_usuario):
    cuenta = _cuenta_vinculada(crear_usuario, ROLE_USER, email=CORREO, sub=SUB)
    oidc.userinfo.update({'groups': ['grupo_revocado']})

    respuesta = oidc.entrar(client)

    _sin_sesion_y_con_error(client, respuesta, 'acceso_denegado')
    db.session.refresh(cuenta)
    assert usuario_en_sesion(client) is None


# --------------------------------------------------------------------------- #
# Mapeo de grupos OIDC de Authelia a roles (FNC-143)
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('grupo,rol_esperado', [
    ('infraestructuraVoIP', ROLE_ADMIN),
    ('app-aduana-admins', ROLE_AREA_ADMIN),
    ('app-aduana-users', ROLE_USER),
    ('INFRAESTRUCTURAVOIP', ROLE_ADMIN),
    ('App-Aduana-Admins', ROLE_AREA_ADMIN),
])
def test_mapeo_de_grupos_asigna_rol_en_cuenta_nueva(client, oidc, grupo, rol_esperado):
    oidc.userinfo['groups'] = [grupo]

    oidc.entrar(client)

    cuenta = User.query.filter_by(email=CORREO).one()
    assert cuenta.role == rol_esperado


def test_prioridad_superadmin_sobre_admin_de_area(client, oidc):
    oidc.userinfo['groups'] = ['app-aduana-admins', 'infraestructuraVoIP']

    oidc.entrar(client)

    cuenta = User.query.filter_by(email=CORREO).one()
    assert cuenta.role == ROLE_ADMIN


def test_cuenta_existente_sincroniza_rol_si_cambia_en_authelia(
        client, oidc, crear_usuario):
    cuenta = _cuenta_vinculada(crear_usuario, ROLE_USER, email=CORREO, sub=SUB)

    # 1. Se le asigna grupo de admin de área en Authelia
    oidc.userinfo['groups'] = ['app-aduana-admins']
    oidc.entrar(client)
    db.session.refresh(cuenta)
    assert cuenta.role == ROLE_AREA_ADMIN

    # 2. Se le promueve a superadmin en Authelia
    oidc.userinfo['groups'] = ['infraestructuraVoIP']
    oidc.entrar(client)
    db.session.refresh(cuenta)
    assert cuenta.role == ROLE_ADMIN

    # 3. Se le degrada a usuario en Authelia
    oidc.userinfo['groups'] = ['app-aduana-users']
    oidc.entrar(client)
    db.session.refresh(cuenta)
    assert cuenta.role == ROLE_USER


def test_degradacion_de_admin_de_area_limpia_areas_administradas(
        client, oidc, crear_usuario):
    from app.modules.core.models import Area
    area = Area(name='Área Pruebas', status='active')
    db.session.add(area)
    db.session.commit()

    cuenta = _cuenta_vinculada(crear_usuario, ROLE_AREA_ADMIN, email=CORREO, sub=SUB)
    cuenta.managed_areas = [area]
    db.session.commit()

    # Usuario inicia sesión con grupo app-aduana-users (ya no es admin_area)
    oidc.userinfo['groups'] = ['app-aduana-users']
    oidc.entrar(client)

    db.session.refresh(cuenta)
    assert cuenta.role == ROLE_USER
    assert cuenta.managed_areas == []


def test_mapeo_con_variables_de_entorno_personalizadas(client, oidc, monkeypatch):
    monkeypatch.setenv('OIDC_GROUP_SUPERADMIN', 'infra_custom')
    monkeypatch.setenv('OIDC_GROUP_AREA_ADMIN', 'admins_custom')
    monkeypatch.setenv('OIDC_GROUP_USER', 'users_custom')

    oidc.userinfo['groups'] = ['infra_custom']
    oidc.entrar(client)

    cuenta = User.query.filter_by(email=CORREO).one()
    assert cuenta.role == ROLE_ADMIN


# --------------------------------------------------------------------------- #
# Rechazos por el estado de la cuenta
# --------------------------------------------------------------------------- #

def test_cuenta_local_con_el_mismo_correo_se_rechaza_y_no_se_toca(
        client, oidc, crear_usuario):
    cuenta = crear_usuario(ROLE_ADMIN, email=CORREO, contrasena='clave-ficticia-1')

    respuesta = oidc.entrar(client)

    _sin_sesion_y_con_error(client, respuesta, 'cuenta_no_disponible')
    db.session.refresh(cuenta)
    assert cuenta.oidc_sub is None
    assert cuenta.auth_source == 'local'
    assert hay_auditoria('ACCESO BLOQUEADO', 'warning', target=CORREO)
    assert hay_auditoria('ACCESO OIDC FALLIDO', 'error', target=CORREO)


def test_cuenta_con_contrasena_local_aunque_sea_sso_se_rechaza(
        client, oidc, crear_usuario):
    cuenta = _cuenta_vinculada(crear_usuario, email=CORREO,
                               contrasena='clave-ficticia-1')

    respuesta = oidc.entrar(client)

    _sin_sesion_y_con_error(client, respuesta, 'cuenta_no_disponible')
    db.session.refresh(cuenta)
    assert cuenta.oidc_sub is None


@pytest.mark.parametrize('sub', [None, SUB])
def test_cuenta_desactivada_no_entra(client, oidc, crear_usuario, sub):
    _cuenta_vinculada(crear_usuario, email=CORREO, sub=sub, activo=False)

    respuesta = oidc.entrar(client)

    _sin_sesion_y_con_error(client, respuesta, 'cuenta_no_disponible')


def test_correo_ya_vinculado_a_otra_identidad_se_rechaza(client, oidc,
                                                         crear_usuario):
    cuenta = _cuenta_vinculada(crear_usuario, email=CORREO,
                               sub='sub-de-otra-persona')

    respuesta = oidc.entrar(client)

    _sin_sesion_y_con_error(client, respuesta, 'cuenta_no_disponible')
    db.session.refresh(cuenta)
    assert cuenta.oidc_sub == 'sub-de-otra-persona'


# --------------------------------------------------------------------------- #
# Callback inválido: sin sesión y error genérico auditado
# --------------------------------------------------------------------------- #

def _fallo_auditado():
    return AuditLog.query.filter_by(action='ACCESO OIDC FALLIDO',
                                    status='error').count() == 1


def test_callback_sin_state(client, oidc):
    oidc.empezar(client)

    respuesta = client.get(f'{A}/oidc/callback', query_string={'code': CODIGO})

    _sin_sesion_y_con_error(client, respuesta, 'autenticacion_fallida')
    assert _fallo_auditado()


def test_callback_con_state_distinto(client, oidc):
    oidc.empezar(client)

    respuesta = oidc.callback(client, 'state-que-no-se-emitio')

    _sin_sesion_y_con_error(client, respuesta, 'autenticacion_fallida')
    assert _fallo_auditado()


def test_callback_sin_haber_iniciado_el_flujo(client, oidc):
    respuesta = oidc.callback(client, 'state-ajeno')

    _sin_sesion_y_con_error(client, respuesta, 'autenticacion_fallida')
    assert oidc.peticion_del_token() is None


def test_el_state_solo_sirve_una_vez(client, oidc):
    _, parametros = oidc.empezar(client)
    assert oidc.callback(client, parametros['state']).status_code == 302
    client.post(f'{A}/logout')

    respuesta = oidc.callback(client, parametros['state'])

    _sin_sesion_y_con_error(client, respuesta, 'autenticacion_fallida')


def test_nonce_distinto(client, oidc):
    _, parametros = oidc.empezar(client)
    oidc.nonce = 'nonce-de-otro-flujo'

    respuesta = oidc.callback(client, parametros['state'])

    _sin_sesion_y_con_error(client, respuesta, 'autenticacion_fallida')
    assert _fallo_auditado()


def test_id_token_sin_nonce(client, oidc):
    _, parametros = oidc.empezar(client)
    oidc.id_token_cambios['nonce'] = None

    respuesta = oidc.callback(client, parametros['state'])

    _sin_sesion_y_con_error(client, respuesta, 'autenticacion_fallida')


def test_token_vencido(client, oidc):
    _, parametros = oidc.empezar(client)
    oidc.id_token_cambios.update({'exp': 1_000, 'iat': 900})

    respuesta = oidc.callback(client, parametros['state'])

    _sin_sesion_y_con_error(client, respuesta, 'autenticacion_fallida')
    assert _fallo_auditado()


def test_audiencia_ajena(client, oidc):
    _, parametros = oidc.empezar(client)
    oidc.id_token_cambios['aud'] = 'otro-cliente'

    respuesta = oidc.callback(client, parametros['state'])

    _sin_sesion_y_con_error(client, respuesta, 'autenticacion_fallida')
    assert _fallo_auditado()


def test_emisor_ajeno(client, oidc):
    _, parametros = oidc.empezar(client)
    oidc.id_token_cambios['iss'] = 'https://falso.pruebas.invalid'

    respuesta = oidc.callback(client, parametros['state'])

    _sin_sesion_y_con_error(client, respuesta, 'autenticacion_fallida')
    assert _fallo_auditado()


def test_firma_invalida(client, oidc):
    _, parametros = oidc.empezar(client)
    oidc.firmar_con_llave_ajena = True

    respuesta = oidc.callback(client, parametros['state'])

    _sin_sesion_y_con_error(client, respuesta, 'autenticacion_fallida')
    assert _fallo_auditado()
    assert User.query.count() == 0


def test_respuesta_sin_id_token(client, oidc):
    _, parametros = oidc.empezar(client)
    oidc.token_sin_id_token = True

    respuesta = oidc.callback(client, parametros['state'])

    _sin_sesion_y_con_error(client, respuesta, 'autenticacion_fallida')
    assert User.query.count() == 0


def test_error_del_endpoint_de_token(client, oidc):
    _, parametros = oidc.empezar(client)
    oidc.error_del_token = 'invalid_grant'

    respuesta = oidc.callback(client, parametros['state'])

    _sin_sesion_y_con_error(client, respuesta, 'autenticacion_fallida')


def test_authelia_niega_el_acceso(client, oidc):
    _, parametros = oidc.empezar(client)

    respuesta = client.get(f'{A}/oidc/callback', query_string={
        'error': 'access_denied', 'state': parametros['state'],
        'error_description': 'detalle que no debe llegar al cliente'})

    _sin_sesion_y_con_error(client, respuesta, 'acceso_denegado')
    assert 'detalle' not in _destino(respuesta)
    assert oidc.peticion_del_token() is None


def test_sub_de_userinfo_distinto_al_del_id_token(client, oidc):
    _, parametros = oidc.empezar(client)
    oidc.id_token_cambios['sub'] = 'sub-del-id-token'

    respuesta = oidc.callback(client, parametros['state'])

    _sin_sesion_y_con_error(client, respuesta, 'autenticacion_fallida')
    assert User.query.count() == 0


def test_sin_correo(client, oidc):
    del oidc.userinfo['email']

    respuesta = oidc.entrar(client)

    _sin_sesion_y_con_error(client, respuesta, 'identidad_incompleta')
    assert User.query.count() == 0


def test_correo_no_verificado(client, oidc):
    oidc.userinfo['email_verified'] = False

    respuesta = oidc.entrar(client)

    _sin_sesion_y_con_error(client, respuesta, 'identidad_incompleta')
    assert User.query.count() == 0


def test_sin_email_verified_se_acepta(client, oidc):
    del oidc.userinfo['email_verified']

    assert _destino(oidc.entrar(client)) == '/dashboard'


def test_callback_sin_configuracion(client, monkeypatch):
    respuesta = client.get(f'{A}/oidc/callback',
                           query_string={'code': 'x', 'state': 'y'})

    _sin_sesion_y_con_error(client, respuesta, 'oidc_no_disponible')


# --------------------------------------------------------------------------- #
# Nada sensible en la auditoría ni en las respuestas
# --------------------------------------------------------------------------- #

def test_secreto_codigo_y_state_no_quedan_en_la_auditoria(client, oidc):
    _, parametros = oidc.empezar(client)
    oidc.firmar_con_llave_ajena = True
    oidc.callback(client, parametros['state'])
    oidc.firmar_con_llave_ajena = False
    oidc.entrar(client)

    texto = ' '.join(f'{r.action} {r.detail} {r.target} {r.before_state} {r.after_state}'
                     for r in AuditLog.query.all())
    for sensible in (CLIENT_SECRET, CODIGO, parametros['state'], 'acceso-ficticio'):
        assert sensible not in texto


def test_el_secreto_no_viaja_en_la_redireccion_ni_en_el_context(client, oidc):
    respuesta, _ = oidc.empezar(client)

    assert CLIENT_SECRET not in _destino(respuesta)
    assert CLIENT_SECRET not in client.get(f'{A}/context').get_data(as_text=True)


# --------------------------------------------------------------------------- #
# Contexto
# --------------------------------------------------------------------------- #

# Claves de marca agregadas al contexto (contrato autenticacion: marca).
CLAVES_DE_MARCA = {'authelia_url', 'app_name', 'app_title', 'domain',
                   'support_email', 'motivos'}


def _contexto_sin_marca(datos):
    assert CLAVES_DE_MARCA <= set(datos)
    return {k: v for k, v in datos.items() if k not in CLAVES_DE_MARCA}


def test_context_con_oidc(client, oidc):
    assert _contexto_sin_marca(client.get(f'{A}/context').get_json()) == {
        'oidc_enabled': True, 'authenticated': False,
        'emergency_available': True, 'local_login': False}


def test_context_sin_oidc(client):
    assert _contexto_sin_marca(client.get(f'{A}/context').get_json()) == {
        'oidc_enabled': False, 'authenticated': False,
        'emergency_available': True, 'local_login': False}


def test_context_con_sesion(client, oidc):
    oidc.entrar(client)

    assert client.get(f'{A}/context').get_json()['authenticated'] is True


# --------------------------------------------------------------------------- #
# Cierre de sesión
# --------------------------------------------------------------------------- #

URL_CIERRE = 'https://auth.pruebas.invalid/logout'
RETORNO = 'https%3A%2F%2Fportal.pruebas.invalid%2Flogin'


def test_logout_devuelve_la_url_de_cierre_de_la_configuracion(client, oidc,
                                                              monkeypatch):
    monkeypatch.setenv('OIDC_LOGOUT_URL', URL_CIERRE)
    oidc.entrar(client)

    respuesta = client.post(f'{A}/logout')

    assert respuesta.get_json() == {
        'status': 'success', 'redirect': f'{URL_CIERRE}?rd={RETORNO}'}
    assert usuario_en_sesion(client) is None


def test_logout_ignora_el_host_de_la_peticion(client, oidc, monkeypatch):
    monkeypatch.setenv('OIDC_LOGOUT_URL', URL_CIERRE)
    oidc.entrar(client)

    respuesta = client.post(f'{A}/logout', headers={
        'Host': 'atacante.pruebas.invalid',
        'X-Forwarded-Host': 'atacante.pruebas.invalid'})

    assert 'atacante' not in respuesta.get_json()['redirect']


def test_logout_usa_end_session_endpoint_si_no_hay_url_configurada(
        client, oidc):
    oidc.fin_de_sesion = 'https://auth.pruebas.invalid/oidc/logout'
    oidc.entrar(client)

    redireccion = client.post(f'{A}/logout').get_json()['redirect']

    assert redireccion.startswith('https://auth.pruebas.invalid/oidc/logout?')
    assert f'post_logout_redirect_uri={RETORNO}' in redireccion


def test_logout_sin_ninguna_url_no_redirige(client, oidc):
    oidc.entrar(client)

    assert client.post(f'{A}/logout').get_json() == {
        'status': 'success', 'redirect': None}


def test_logout_de_la_cuenta_de_emergencia_sin_oidc(cliente_admin):
    respuesta = cliente_admin.post(f'{A}/logout')

    assert respuesta.get_json() == {'status': 'success', 'redirect': None}


# --------------------------------------------------------------------------- #
# Retiro de las cabeceras Remote-* y del login por directorio (regresión SEG-04)
# --------------------------------------------------------------------------- #

CABECERAS_REMOTAS = {'Remote-Email': CORREO, 'Remote-Name': NOMBRE,
                     'Remote-User': 'persona', 'Remote-Groups': 'admins'}


def test_remote_email_ya_no_autentica_una_ruta_protegida(client, oidc,
                                                         crear_usuario):
    _cuenta_vinculada(crear_usuario, ROLE_ADMIN, email=CORREO)

    respuesta = client.get('/api/v1/me', headers=CABECERAS_REMOTAS)

    assert respuesta.status_code == 401


def test_remote_email_no_aparece_en_el_context(client, oidc):
    cuerpo = client.get(f'{A}/context', headers=CABECERAS_REMOTAS).get_json()

    assert cuerpo['authenticated'] is False
    assert 'sso_user' not in cuerpo and 'sso_enabled' not in cuerpo
    assert CORREO not in str(cuerpo)


def test_sso_retirado_da_410_y_no_crea_cuenta(client, oidc):
    respuesta = client.post(f'{A}/sso', headers=CABECERAS_REMOTAS)

    assert respuesta.status_code == 410
    assert respuesta.get_json()['code'] == 'endpoint_retirado'
    assert respuesta.get_json()['use'] == 'GET /auth/oidc/login'
    assert User.query.count() == 0
    assert usuario_en_sesion(client) is None


@pytest.mark.parametrize('metodo', ['directory', 'local', None])
def test_login_retirado_da_410(client, crear_usuario, metodo):
    cuerpo = {'email': 'a@pruebas.invalid', 'password': 'x'}
    if metodo:
        cuerpo['method'] = metodo

    respuesta = client.post(f'{A}/login', json=cuerpo)

    assert respuesta.status_code == 410
    assert respuesta.get_json()['use'] == 'POST /auth/local'


def test_el_modulo_ya_no_lee_authelia_enabled(client, oidc, monkeypatch):
    monkeypatch.setenv('AUTHELIA_ENABLED', 'true')

    assert client.post(f'{A}/sso', headers=CABECERAS_REMOTAS).status_code == 410
    assert usuario_en_sesion(client) is None


def test_un_error_libre_del_callback_se_audita_como_otro(client, oidc):
    """Revisión de seguridad: `?error=` lo elige quien llama; a la auditoría
    solo llegan códigos OAuth conocidos (el resto, como «otro»)."""
    from app.modules.audit.models import AuditLog
    _, parametros = oidc.empezar(client)

    respuesta = client.get(f'{A}/oidc/callback', query_string={
        'error': 'texto inventado por un atacante', 'state': parametros['state']})

    _sin_sesion_y_con_error(client, respuesta, 'autenticacion_fallida')
    fallos = AuditLog.query.filter_by(action='ACCESO OIDC FALLIDO').all()
    assert fallos and all('texto inventado' not in (a.detail or '') for a in fallos)
    assert any('OIDC: otro' in (a.detail or '') for a in fallos)
