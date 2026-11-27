"""
API v1 — autenticación (contrato `docs/contratos/autenticacion.md`).

Las personas entran solo por Authelia con OIDC (código de autorización con
PKCE; `app/modules/auth/oidc.py`, ADR-009). Queda una ruta local de emergencia
(`POST /auth/local`, sin enlace visible) para la cuenta de emergencia.

La emisión y validación de la sesión sigue aquí, en Flask-Login: es lo que
firma la cookie. Las cabeceras `Remote-*` ya no autentican a nadie.

El rol no sale del token ni de sus grupos: una cuenta nueva entra como
`usuario` y el superadmin la eleva en el portal (SEG-10, FNC-042).
"""

import logging
import os

from flask import Blueprint, current_app, jsonify, redirect, request, session
from flask_login import current_user, login_required, login_user, logout_user

from app.modules.access_requests import motivos
from app.modules.api.helpers import endpoint_retirado
from app.modules.audit.services import add_audit_log
from app.modules.auth import oidc
from app.modules.auth.acceso_local import (es_cuenta_de_emergencia,
                                           login_local_por_oidc_apagado,
                                           motivo_rechazo_login_local)
from app.modules.auth.limite_intentos import MENSAJE_BLOQUEO, bloqueado
from app.modules.auth.models import User
from app.modules.auth.oidc_cuentas import cuenta_de_la_identidad
from app.modules.auth.services import MENSAJE_CREDENCIALES
from app.modules.notifications.services import avisar_usuario_creado

logger = logging.getLogger(__name__)

auth_api_bp = Blueprint('api_auth', __name__, url_prefix='/api/v1/auth')

RUTA_INICIO = '/dashboard'
RUTA_ENTRADA = '/login'
USO_OIDC = 'GET /auth/oidc/login'
USO_LOCAL = 'POST /auth/local'


def _acceso_fallido(email, motivo):
    """Audita el motivo y responde el fallo único (401)."""
    add_audit_log('ACCESO FALLIDO', status='error', target=email,
                  detail=motivo[:200])
    return jsonify({'status': 'error', 'message': MENSAJE_CREDENCIALES}), 401


def _abrir_sesion(cuenta):
    """`login_user` sobre una sesión limpia (fijación de sesión, SEC-SES-03).

    `session.clear()` quita también `_permanent`: se vuelve a fijar.
    `remember=False`: no se emiten cookies persistentes de 1 año (SEC-AUTH-15).
    """
    session.clear()
    session.permanent = True
    return login_user(cuenta, remember=False)


# Marca por omisión de `GET /auth/context` (las variables la reemplazan).
NOMBRE_APP_POR_DEFECTO = 'aduana'
TITULO_APP_POR_DEFECTO = 'Aduana'
CORREO_SOPORTE_POR_DEFECTO = 'aduana-app@vivaro.com'


def _volver_a_entrada(codigo):
    """Redirige a la pantalla de acceso con un código sin detalle."""
    return redirect(f'{RUTA_ENTRADA}?error={codigo}')


@auth_api_bp.route('/context')
def context():
    """Qué ofrecer en la pantalla de acceso. El frontend lo consulta antes de pintarla."""
    cfg_oidc = oidc.configuracion()
    authelia_url = (os.getenv('AUTHELIA_URL') or os.getenv('AUTHELIA_SSO_URL') or
                    (cfg_oidc.issuer if cfg_oidc else None) or
                    os.getenv('OIDC_ISSUER_URL') or '').strip() or None
    return jsonify({
        'oidc_enabled': oidc.oidc_habilitado(),
        'authenticated': current_user.is_authenticated,
        # La ruta de emergencia siempre existe, pero no tiene enlace visible (ADR-009 6A).
        'emergency_available': True,
        # Authelia apagado (FNC-158): `/login` muestra usuario y contraseña (solo cuentas locales).
        'local_login': login_local_por_oidc_apagado(),
        'authelia_url': authelia_url,
        # Marca del portal (FNC-168: valores por omisión con nombre).
        'app_name': os.getenv('APP_NAME') or NOMBRE_APP_POR_DEFECTO,
        'app_title': (os.getenv('APP_TITLE') or os.getenv('NEXT_PUBLIC_APP_TITLE')
                      or TITULO_APP_POR_DEFECTO),
        'domain': os.getenv('DOMAIN') or os.getenv('NEXT_PUBLIC_DOMAIN') or '',
        # Si la web pide motivo al solicitar y al rechazar (FNC-216).
        'motivos': motivos.como_dict(),
        'support_email': (os.getenv('SUPPORT_EMAIL')
                          or os.getenv('NEXT_PUBLIC_SUPPORT_EMAIL')
                          or CORREO_SOPORTE_POR_DEFECTO),
    })


@auth_api_bp.route('/oidc/login')
def oidc_login():
    """Redirige a Authelia (código de autorización, PKCE S256, `state` y `nonce`)."""
    config = oidc.configuracion()
    if config is None:
        return _volver_a_entrada(oidc.ERROR_NO_DISPONIBLE)
    try:
        return oidc.cliente(config).authorize_redirect(config.redirect_uri)
    except Exception as exc:
        logger.error('OIDC: no se pudo iniciar el flujo (%s).', type(exc).__name__)
        add_audit_log('ACCESO OIDC FALLIDO', status='error',
                      detail=f'No se pudo contactar a Authelia: {type(exc).__name__}')
        return _volver_a_entrada(oidc.ERROR_NO_DISPONIBLE)


def _fallo_oidc(error, objetivo=None):
    # Sin tokens, `code` ni `state`: solo el motivo de `ErrorOidc`.
    add_audit_log('ACCESO OIDC FALLIDO', status='error', target=objetivo,
                  detail=error.motivo[:200])
    return _volver_a_entrada(error.codigo)


@auth_api_bp.route('/oidc/callback')
def oidc_callback():
    """Vuelta de Authelia: valida, vincula la cuenta y abre la sesión del portal."""
    config = oidc.configuracion()
    if config is None:
        return _volver_a_entrada(oidc.ERROR_NO_DISPONIBLE)
    try:
        identidad = oidc.identidad_del_callback(config)
    except oidc.ErrorOidc as error:
        return _fallo_oidc(error)

    try:
        resultado = cuenta_de_la_identidad(identidad)
    except oidc.ErrorOidc as error:
        return _fallo_oidc(error, identidad.correo)
    except Exception as exc:
        from app import db
        db.session.rollback()
        logger.error('OIDC: fallo al registrar la cuenta (%s).', type(exc).__name__)
        return _fallo_oidc(oidc.ErrorOidc(oidc.ERROR_AUTENTICACION,
                                          'OIDC: fallo al registrar la cuenta'),
                           identidad.correo)

    cuenta = resultado.cuenta
    if not _abrir_sesion(cuenta):
        return _fallo_oidc(oidc.ErrorOidc(oidc.ERROR_CUENTA,
                                          'OIDC: login_user rechazó la cuenta'),
                           cuenta.email)
    add_audit_log('ACCESO SSO', status='success', target=cuenta.email,
                  detail='Sesión iniciada vía Authelia (OIDC)')
    if resultado.es_nueva:
        # El enlace del correo sale de la configuración, nunca del `Host`.
        base = (os.getenv('BASE_URL') or oidc.origen_del_portal(config)).rstrip('/')
        avisar_usuario_creado(cuenta.email, cuenta.nombre, base,
                              f'{base}{RUTA_ENTRADA}')
    return redirect(RUTA_INICIO)


@auth_api_bp.route('/local', methods=['POST'])
def local_login():
    """Inicio de sesión de la cuenta de emergencia (o, en desarrollo, la bandera de FNC-077).

    Respuesta única de fallo (SEC-AUTH-09) y límite de intentos (FNC-014).
    """
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip()
    password = data.get('password') or ''

    if not email or not password:
        return jsonify({'status': 'error',
                        'message': 'Indica usuario y contraseña.'}), 400

    user = User.query.filter_by(email=email).first()

    # Fuerza bruta (FNC-014): sin probar credenciales mientras dure el bloqueo.
    # La cuenta de emergencia solo se bloquea por IP (FNC-154): nadie debe poder
    # dejarla fuera a propósito sin quedar bloqueado él mismo.
    if bloqueado(email, omitir_limite_de_cuenta=es_cuenta_de_emergencia(user)):
        add_audit_log('ACCESO BLOQUEADO', status='warning', target=email,
                      detail='Límite de intentos fallidos')
        return jsonify({'status': 'error', 'message': MENSAJE_BLOQUEO}), 429

    if user and user.password_hash and user.check_password(password):
        # Solo la cuenta de emergencia (o, en desarrollo, la bandera):
        # respuesta única, el motivo solo a la auditoría (FNC-077).
        motivo = motivo_rechazo_login_local(user)
        if motivo:
            return _acceso_fallido(email, f'Local: {motivo}')
        # Desactivada: respuesta única, no confirma la contraseña (SEC-AUTH-09).
        if not user.is_active:
            return _acceso_fallido(email, 'Local: cuenta desactivada')
        if not _abrir_sesion(user):
            return _acceso_fallido(email, 'Local: cuenta desactivada')
        add_audit_log('ACCESO LOCAL', status='success', target=email,
                      detail='Autenticación manual')
        return jsonify({'status': 'success', 'role': user.role})

    add_audit_log('ACCESO FALLIDO', status='error', target=email,
                  detail='Credenciales locales incorrectas')
    # Mismo mensaje exista o no la cuenta, para no revelar qué correos hay.
    return jsonify({'status': 'error',
                    'message': MENSAJE_CREDENCIALES}), 401


@auth_api_bp.route('/sso', methods=['POST'])
def sso_retirado():
    """Retirado (ADR-009): las cabeceras `Remote-*` ya no autentican."""
    return endpoint_retirado(USO_OIDC)


@auth_api_bp.route('/login', methods=['POST'])
def login_retirado():
    """Retirado (ADR-009): sin login por directorio; la emergencia usa `/auth/local`."""
    return endpoint_retirado(USO_LOCAL)


@auth_api_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Cierra la sesión y devuelve la URL de cierre de Authelia, si hay una."""
    email = current_user.email
    session.clear()
    logout_user()
    add_audit_log('CIERRE DE SESIÓN', status='success', target=email,
                  detail='Sesión finalizada por el usuario')

    config = oidc.configuracion()
    redirect_to = oidc.url_de_cierre(config) if config else None
    resp = jsonify({'status': 'success', 'redirect': redirect_to})

    # Borrado explícito y garantizado de remember_token y nexus_session
    rem_name = current_app.config.get('REMEMBER_COOKIE_NAME', 'remember_token')
    sess_name = current_app.config.get('SESSION_COOKIE_NAME', 'nexus_session')
    rem_domain = current_app.config.get('REMEMBER_COOKIE_DOMAIN')
    sess_domain = current_app.config.get('SESSION_COOKIE_DOMAIN')
    rem_path = current_app.config.get('REMEMBER_COOKIE_PATH', '/')
    sess_path = current_app.config.get('SESSION_COOKIE_PATH', '/')

    resp.delete_cookie(rem_name, domain=rem_domain, path=rem_path)
    resp.delete_cookie(sess_name, domain=sess_domain, path=sess_path)
    if rem_domain:
        resp.delete_cookie(rem_name, path=rem_path)
    if sess_domain:
        resp.delete_cookie(sess_name, path=sess_path)

    return resp


# ------------------------------------------------------------------ #
# Autoservicio de Contraseña e Identidad Authelia
# ------------------------------------------------------------------ #

@auth_api_bp.route('/autoservicio/configuracion', methods=['GET'])
def autoservicio_configuracion():
    """Retorna la configuración de identidad, MFA y políticas para Authelia."""
    from app.modules.auth.autoservicio import obtener_configuracion_autoservicio
    return jsonify(obtener_configuracion_autoservicio()), 200


@auth_api_bp.route('/autoservicio/politica', methods=['GET'])
def autoservicio_politica():
    """Retorna la política de contraseñas para validación en tiempo real."""
    from app.modules.users.politica_contrasena import cargar_politica
    return jsonify(cargar_politica().publica()), 200


@auth_api_bp.route('/autoservicio/mfa/solicitar', methods=['POST'])
def autoservicio_mfa_solicitar():
    """Envía un código de 6 dígitos al correo del usuario para verificación MFA."""
    from app.modules.auth.autoservicio import solicitar_codigo_mfa, ErrorAutoservicio
    data = request.get_json(silent=True) or {}
    identificador = (data.get('identificador') or '').strip()
    try:
        res = solicitar_codigo_mfa(identificador)
        return jsonify(res), 200
    except ErrorAutoservicio as err:
        return jsonify({'status': 'error', 'message': err.mensaje}), err.codigo_http
    except Exception as exc:
        logger.error("Error en autoservicio/mfa/solicitar: %s", type(exc).__name__)
        return jsonify({'status': 'error', 'message': 'Ocurrió un error al procesar el código MFA.'}), 500


@auth_api_bp.route('/autoservicio/mfa/verificar', methods=['POST'])
def autoservicio_mfa_verificar():
    """Valida el código de segundo factor (MFA) en el paso 2 del asistente."""
    from app.modules.auth.autoservicio import verificar_codigo_mfa_paso2, ErrorAutoservicio
    data = request.get_json(silent=True) or {}
    identificador = (data.get('identificador') or data.get('identifier') or '').strip()
    mfa_code = (data.get('mfa_code') or '').strip()
    challenge_token = data.get('challenge_token') or ''
    try:
        res = verificar_codigo_mfa_paso2(identificador, mfa_code, challenge_token=challenge_token)
        return jsonify(res), 200
    except ErrorAutoservicio as err:
        return jsonify({'status': 'error', 'message': err.mensaje}), err.codigo_http
    except Exception as exc:
        logger.error("Error en autoservicio/mfa/verificar: %s", type(exc).__name__)
        return jsonify({'status': 'error', 'message': 'Ocurrió un error al verificar el código MFA.'}), 500


@auth_api_bp.route('/autoservicio/cambiar', methods=['POST'])
def autoservicio_cambiar():
    """Cambia la contraseña validando la contraseña actual y MFA si aplica."""
    from app.modules.auth.autoservicio import cambiar_contrasena, ErrorAutoservicio
    data = request.get_json(silent=True) or {}
    identificador = (data.get('identificador') or '').strip()
    contrasena_actual = data.get('current_password') or ''
    nueva_contrasena = data.get('new_password') or ''
    mfa_code = data.get('mfa_code') or ''
    challenge_token = data.get('challenge_token') or ''
    try:
        res = cambiar_contrasena(identificador, contrasena_actual, nueva_contrasena,
                                 mfa_code=mfa_code, challenge_token=challenge_token)
        return jsonify(res), 200
    except ErrorAutoservicio as err:
        return jsonify({'status': 'error', 'message': err.mensaje}), err.codigo_http
    except Exception as exc:
        logger.error("Error en autoservicio/cambiar: %s", type(exc).__name__)
        return jsonify({'status': 'error', 'message': 'Ocurrió un error interno procesando la solicitud.'}), 500


@auth_api_bp.route('/autoservicio/solicitar-recuperacion', methods=['POST'])
def autoservicio_solicitar_recuperacion():
    """Envía el enlace de recuperación al correo corporativo si existe."""
    from app.modules.auth.autoservicio import solicitar_recuperacion, ErrorAutoservicio
    data = request.get_json(silent=True) or {}
    correo = (data.get('email') or '').strip()
    # El enlace sale solo de `BASE_URL`, nunca del `Host` de la petición
    # (FNC-168: evita envenenar el enlace de recuperación; como FNC-141).
    try:
        res = solicitar_recuperacion(correo)
        return jsonify(res), 200
    except ErrorAutoservicio as err:
        return jsonify({'status': 'error', 'message': err.mensaje}), err.codigo_http
    except Exception as exc:
        logger.error("Error en autoservicio/solicitar-recuperacion: %s", type(exc).__name__)
        return jsonify({'status': 'error', 'message': 'Ocurrió un error interno procesando la solicitud.'}), 500


@auth_api_bp.route('/autoservicio/restablecer', methods=['POST'])
def autoservicio_restablecer():
    """Aplica la nueva contraseña utilizando el token firmado y MFA si aplica."""
    from app.modules.auth.autoservicio import restablecer_con_token, ErrorAutoservicio
    data = request.get_json(silent=True) or {}
    correo = (data.get('email') or '').strip()
    token = (data.get('token') or '').strip()
    nueva_contrasena = data.get('new_password') or ''
    mfa_code = data.get('mfa_code') or ''
    challenge_token = data.get('challenge_token') or ''
    try:
        res = restablecer_con_token(correo, token, nueva_contrasena,
                                     mfa_code=mfa_code, challenge_token=challenge_token)
        return jsonify(res), 200
    except ErrorAutoservicio as err:
        return jsonify({'status': 'error', 'message': err.mensaje}), err.codigo_http
    except Exception as exc:
        logger.error("Error en autoservicio/restablecer: %s", type(exc).__name__)
        return jsonify({'status': 'error', 'message': 'Ocurrió un error interno procesando la solicitud.'}), 500


@auth_api_bp.route('/autoservicio/restablecer-mfa', methods=['POST'])
def autoservicio_restablecer_mfa():
    """Aplica la nueva contraseña validando directamente el código MFA (sin requerir clave previa)."""
    from app.modules.auth.autoservicio import restablecer_directo_mfa, ErrorAutoservicio
    data = request.get_json(silent=True) or {}
    identificador = (data.get('identifier') or data.get('identificador') or '').strip()
    nueva_contrasena = data.get('new_password') or ''
    mfa_code = data.get('mfa_code') or ''
    challenge_token = data.get('challenge_token') or ''
    try:
        res = restablecer_directo_mfa(identificador, nueva_contrasena,
                                      mfa_code=mfa_code, challenge_token=challenge_token)
        return jsonify(res), 200
    except ErrorAutoservicio as err:
        return jsonify({'status': 'error', 'message': err.mensaje}), err.codigo_http
    except Exception as exc:
        logger.error("Error en autoservicio/restablecer-mfa: %s", type(exc).__name__)
        return jsonify({'status': 'error', 'message': 'Ocurrió un error interno procesando la solicitud.'}), 500


