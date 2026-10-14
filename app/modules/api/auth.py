"""
API v1 — autenticación.

Endpoints JSON que consume el frontend. La emisión y validación de la sesión
sigue aquí, en Flask-Login: es lo que firma la cookie.

Sobre el SSO: Authelia se aplica mediante cabeceras que inyecta Nginx
(`Remote-Email`, `Remote-Name`, `Remote-Groups`). Confiar en ellas solo es
seguro si nadie más puede ponerlas, así que este módulo únicamente las acepta
cuando la petición llega de un proxy declarado en TRUSTED_PROXIES. Sin esa
comprobación, cualquiera que alcance el puerto podría enviar
`Remote-Email: admin` y suplantar a quien quisiera.
"""

import os

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required, login_user, logout_user

from app import db
from app.modules.audit.services import add_audit_log
from app.modules.auth.models import User

auth_api_bp = Blueprint('api_auth', __name__, url_prefix='/api/v1/auth')


def _trusted_proxy():
    """True si la petición viene de un proxy autorizado a inyectar Remote-*.

    Por defecto solo loopback, que es donde escucha Nginx en este despliegue.
    """
    allowed = {p.strip() for p in os.getenv(
        'TRUSTED_PROXIES', '127.0.0.1,::1').split(',') if p.strip()}
    return request.remote_addr in allowed


def _sso_enabled():
    return os.getenv('AUTHELIA_ENABLED', 'false').lower() == 'true'


def _role_from_groups(groups_header):
    """Deduce el rol a partir de los grupos que envía Authelia."""
    admin_groups = [g.strip().lower() for g in os.getenv(
        'AUTHELIA_GROUP_ADMIN', 'administrador').split(',')]
    if not groups_header:
        return 'usuario'
    groups = [g.strip().lower() for g in groups_header.split(',')]
    return 'administrador' if any(g in groups for g in admin_groups) else 'usuario'


@auth_api_bp.route('/context')
def context():
    """Qué métodos de acceso ofrecer, y si el SSO ya identifica al visitante.

    El frontend lo consulta antes de pintar el formulario.
    """
    sso_user = None
    if _sso_enabled() and _trusted_proxy():
        header = os.getenv('AUTHELIA_HEADER_USER', 'Remote-Email')
        sso_user = request.headers.get(header)

    return jsonify({
        'sso_enabled': _sso_enabled(),
        'sso_user': sso_user,
        'authenticated': current_user.is_authenticated,
        'ldap_available': True,
    })


@auth_api_bp.route('/sso', methods=['POST'])
def sso_login():
    """Inicia sesión a partir de las cabeceras de Authelia."""
    if not _sso_enabled():
        return jsonify({'status': 'error', 'message': 'SSO no habilitado.'}), 400

    # Una cabecera Remote-* solo vale si la puso el proxy, no el cliente.
    if not _trusted_proxy():
        add_audit_log('SSO RECHAZADO', status='warning',
                      detail=f'Cabeceras Remote-* desde origen no confiable: '
                             f'{request.remote_addr}')
        return jsonify({'status': 'error',
                        'message': 'Origen no autorizado para SSO.'}), 403

    email = request.headers.get(os.getenv('AUTHELIA_HEADER_USER', 'Remote-Email'))
    if not email:
        return jsonify({'status': 'error', 'message': 'Sin identidad SSO.'}), 401

    name = request.headers.get(
        os.getenv('AUTHELIA_HEADER_NAME', 'Remote-Name'), email)
    groups = request.headers.get(
        os.getenv('AUTHELIA_HEADER_GROUPS', 'Remote-Groups'), '')
    role = _role_from_groups(groups)

    user = User.query.filter_by(email=email).first()
    created = user is None
    if created:
        user = User(email=email, nombre=name, role=role, auth_source='sso')
        db.session.add(user)
    else:
        user.nombre = name
        # El rol lo manda el directorio, salvo que sea un admin de área local:
        # ese nivel se gestiona en Nexus y el SSO no lo conoce.
        if user.role != 'admin_area':
            user.role = role
    db.session.commit()

    login_user(user, remember=True)
    add_audit_log('ACCESO SSO', status='success', target=email,
                  detail='Sesión iniciada vía Authelia')

    if created and os.getenv('NOTIFY_USER_CREATED', 'true').lower() == 'true':
        try:
            from app.modules.notifications.services import send_notification_by_slug
            base = os.getenv('BASE_URL', request.host_url.rstrip('/'))
            send_notification_by_slug('usuario_creado', email, context={
                'nombre': name, 'usuario': email,
                'base_url': base, 'url': base,
            })
        except Exception:
            # Un fallo al notificar no debe impedir el acceso.
            pass

    return jsonify({'status': 'success', 'role': user.role})


@auth_api_bp.route('/login', methods=['POST'])
def login():
    """Inicio de sesión con credenciales: directorio o cuenta local."""
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip()
    password = data.get('password') or ''
    method = data.get('method') or 'directory'

    if not email or not password:
        return jsonify({'status': 'error',
                        'message': 'Indica usuario y contraseña.'}), 400

    if method == 'directory':
        from app.modules.auth.services import authenticate_user_ldap
        result = authenticate_user_ldap(email, password)
        if result.get('status') == 'success':
            user = result['user']
            login_user(user, remember=True)
            add_audit_log('ACCESO DIRECTORIO', status='success', target=email,
                          detail='Autenticación corporativa')
            return jsonify({'status': 'success', 'role': user.role})
        add_audit_log('ACCESO FALLIDO', status='error', target=email,
                      detail=str(result.get('message'))[:200])
        return jsonify({'status': 'error',
                        'message': result.get('message') or 'Credenciales incorrectas.'}), 401

    user = User.query.filter_by(email=email).first()
    if user and user.password_hash and user.check_password(password):
        if not user.is_active:
            return jsonify({'status': 'error',
                            'message': 'La cuenta está desactivada.'}), 403
        login_user(user, remember=True)
        add_audit_log('ACCESO LOCAL', status='success', target=email,
                      detail='Autenticación manual')
        return jsonify({'status': 'success', 'role': user.role})

    add_audit_log('ACCESO FALLIDO', status='error', target=email,
                  detail='Credenciales locales incorrectas')
    # Mismo mensaje exista o no la cuenta, para no revelar qué correos hay.
    return jsonify({'status': 'error',
                    'message': 'Credenciales incorrectas.'}), 401


@auth_api_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Cierra la sesión y, con SSO, devuelve la URL de cierre de Authelia."""
    email = current_user.email
    logout_user()
    add_audit_log('CIERRE DE SESIÓN', status='success', target=email,
                  detail='Sesión finalizada por el usuario')

    redirect_to = None
    if _sso_enabled():
        slo = os.getenv('AUTHELIA_SLO_URL')
        if slo:
            # Authelia cierra su propia sesión y devuelve al login.
            base = os.getenv('BASE_URL', request.host_url.rstrip('/'))
            redirect_to = f'{slo}?rd={base}/login'

    return jsonify({'status': 'success', 'redirect': redirect_to})
