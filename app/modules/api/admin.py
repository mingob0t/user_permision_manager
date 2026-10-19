"""
API v1 — configuración del sistema.

Todo aquí es exclusivo del superadmin: identidad del portal, SMTP, plantillas
de correo y respaldo. Un admin de área administra su tenant, no el sistema.
El directorio (`/auth-config`, `/directory/search`) vive en
`app/modules/directory/api.py` (FNC-043).
"""

import json
import os

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app import db
from app.authz import admin_required
from app.modules.audit.services import add_audit_log
from app.modules.auth.models import AuthConfig
from app.modules.notifications.models import (InAppNotification,
                                              NotificationTemplate, SMTPConfig)
from app.modules.settings.models import SystemConfig

admin_bp = Blueprint('api_admin', __name__, url_prefix='/api/v1')


def _payload():
    return request.get_json(silent=True) or {}


def _error(message, status=400):
    return jsonify({'status': 'error', 'message': message}), status


def _smtp_forced():
    """True si SMTP_FORCE_ENV fija la configuración desde el entorno."""
    from app.modules.notifications.services import _env_flag
    return _env_flag('SMTP_FORCE_ENV')


# --------------------------------------------------------------------------- #
# Identidad del portal
# --------------------------------------------------------------------------- #

# El logo se guarda como data URI en la base de datos, no como archivo: así el
# backend no necesita directorio de subidas ni servir estáticos, y el logo
# viaja con el resto de la configuración en los respaldos.
MAX_LOGO_BYTES = 512 * 1024
ALLOWED_LOGO_TYPES = ('image/png', 'image/jpeg', 'image/gif', 'image/webp',
                      'image/svg+xml')


def _validate_logo(value):
    """Comprueba un data URI de imagen. Devuelve (valor, error)."""
    if not value:
        return None, None
    if not value.startswith('data:'):
        return None, 'El logo debe enviarse como data URI.'

    try:
        header, encoded = value.split(',', 1)
        mime = header[5:].split(';')[0]
    except ValueError:
        return None, 'Data URI mal formado.'

    if mime not in ALLOWED_LOGO_TYPES:
        return None, f'Tipo de imagen no permitido: {mime}'

    # base64 crece ~4/3 respecto al original.
    if len(encoded) * 3 // 4 > MAX_LOGO_BYTES:
        return None, f'La imagen supera {MAX_LOGO_BYTES // 1024} KB.'

    import base64
    try:
        base64.b64decode(encoded, validate=True)
    except Exception:
        return None, 'El contenido no es base64 válido.'

    return value, None

@admin_bp.route('/settings')
@login_required
def get_settings():
    """La identidad del portal la lee cualquiera: la interfaz la necesita."""
    config = SystemConfig.query.first()
    if config is None:
        return jsonify(SystemConfig().to_dict())
    return jsonify(config.to_dict())


@admin_bp.route('/settings', methods=['PUT'])
@login_required
@admin_required
def save_settings():
    config = SystemConfig.query.first()
    if config is None:
        config = SystemConfig()
        db.session.add(config)

    data = _payload()
    for field in ('portal_name', 'bg_color', 'text_color'):
        if field in data:
            setattr(config, field, data[field])

    if 'portal_identity_type' in data:
        kind = data['portal_identity_type']
        if kind not in ('icon', 'image'):
            return _error('El tipo de identidad debe ser "icon" o "image".')
        config.portal_identity_type = kind

    if 'portal_icon' in data:
        raw = data['portal_icon']
        if config.portal_identity_type == 'image':
            value, problem = _validate_logo(raw)
            if problem:
                return _error(problem)
            config.portal_icon = value
        else:
            # Para el modo icono se guarda el SVG tal cual.
            config.portal_icon = raw

    db.session.commit()
    add_audit_log('ACTUALIZAR CONFIGURACIÓN', module='Ajustes',
                  status='success')
    return jsonify({'status': 'success', 'settings': config.to_dict()})


# --------------------------------------------------------------------------- #
# SMTP
# --------------------------------------------------------------------------- #

@admin_bp.route('/smtp')
@login_required
@admin_required
def get_smtp():
    """Configuración SMTP efectiva, indicando de dónde sale.

    Con SMTP_FORCE_ENV activo manda el entorno y lo guardado en la base de
    datos se ignora, así que la interfaz muestra los valores en vigor y
    desactiva la edición.
    """
    from app.modules.notifications.services import (resolve_smtp_settings,
                                                    smtp_settings_from_env)

    effective = resolve_smtp_settings()
    forced = _smtp_forced()

    if effective is not None:
        payload = {
            'server': effective.server,
            'port': effective.port,
            'encryption': effective.encryption,
            'auth_enabled': effective.auth_enabled,
            'username': effective.username,
            'sender_name': effective.sender_name,
            'sender_email': effective.sender_email,
            # La contraseña nunca se devuelve.
            'source': effective.source,
        }
    else:
        stored = SMTPConfig.query.first()
        payload = stored.to_dict() if stored else SMTPConfig().to_dict()
        payload['source'] = 'none'

    payload['forced_by_env'] = forced
    # Solo se puede editar desde la interfaz si no está forzado por el entorno.
    payload['editable'] = not forced
    if forced and smtp_settings_from_env() is None:
        payload['warning'] = ('SMTP_FORCE_ENV está activo pero falta '
                              'SMTP_SERVER en el entorno.')
    return jsonify(payload)


@admin_bp.route('/smtp', methods=['PUT'])
@login_required
@admin_required
def save_smtp():
    # Con el entorno forzado, guardar en la base de datos no tendría efecto:
    # es mejor rechazarlo que dejar creer que el cambio se aplicó.
    if _smtp_forced():
        return _error('La configuración SMTP está fijada por el entorno '
                      '(SMTP_FORCE_ENV). Edítala en el .env del servidor.', 409)

    config = SMTPConfig.query.first()
    if config is None:
        config = SMTPConfig()
        db.session.add(config)

    data = _payload()
    for field in ('server', 'encryption', 'username', 'sender_name'):
        if field in data:
            setattr(config, field, data[field])
    if 'port' in data:
        try:
            config.port = int(data['port'])
        except (TypeError, ValueError):
            return _error('Puerto no válido.')
    if 'auth_enabled' in data:
        config.auth_enabled = bool(data['auth_enabled'])
    # Una contraseña vacía no borra la guardada.
    if data.get('password'):
        config.password = data['password']

    db.session.commit()
    add_audit_log('ACTUALIZAR SMTP', module='Notificaciones', status='success')
    return jsonify({'status': 'success', 'smtp': config.to_dict()})


@admin_bp.route('/smtp/test', methods=['POST'])
@login_required
@admin_required
def test_smtp():
    """Envía un correo de prueba al destinatario indicado."""
    recipient = (_payload().get('email') or current_user.email or '').strip()
    if not recipient or '@' not in recipient:
        return _error('Indica un correo de destino válido.')

    from app.modules.notifications.services import (resolve_smtp_settings,
                                                    send_test_email)

    config = resolve_smtp_settings()
    if config is None:
        return _error('No hay configuración SMTP utilizable.')

    try:
        # Se prueba lo que está en vigor; el payload puede sobrescribir campos
        # para validar antes de guardar, salvo si el entorno manda.
        data = {} if config.source == 'env' else _payload()
        result = send_test_email(
            server=data.get('server') or config.server,
            port=int(data.get('port') or config.port),
            encryption=data.get('encryption') or config.encryption,
            username=data.get('username') or config.username,
            password=data.get('password') or config.password,
            sender_name=data.get('sender_name') or config.sender_name,
            target_email=recipient,
        )
        if isinstance(result, dict) and result.get('status') == 'error':
            add_audit_log('PRUEBA SMTP', module='Notificaciones',
                          status='error', detail=str(result.get('message'))[:200])
            return jsonify(result), 502
    except Exception as exc:
        add_audit_log('PRUEBA SMTP', module='Notificaciones', status='error',
                      detail=str(exc))
        return _error(f'No se pudo enviar: {exc}', 502)

    add_audit_log('PRUEBA SMTP', module='Notificaciones', status='success',
                  detail=f'Destinatario: {recipient}')
    return jsonify({'status': 'success'})


# --------------------------------------------------------------------------- #
# Plantillas de correo
# --------------------------------------------------------------------------- #

@admin_bp.route('/templates')
@login_required
@admin_required
def list_templates():
    templates = NotificationTemplate.query.order_by(
        NotificationTemplate.name).all()
    return jsonify([t.to_dict() for t in templates])


@admin_bp.route('/templates/<slug>', methods=['PUT'])
@login_required
@admin_required
def save_template(slug):
    template = NotificationTemplate.query.filter_by(slug=slug).first()
    data = _payload()

    if template is None:
        if not data.get('name') or not data.get('subject'):
            return _error('Nombre y asunto son obligatorios.')
        template = NotificationTemplate(slug=slug, name=data['name'],
                                        subject=data['subject'],
                                        body=data.get('body') or '')
        db.session.add(template)
    else:
        for field in ('name', 'subject', 'body'):
            if field in data:
                setattr(template, field, data[field])
    if 'is_html' in data:
        template.is_html = bool(data['is_html'])

    db.session.commit()
    add_audit_log(f'GUARDAR PLANTILLA: {slug}', module='Notificaciones',
                  target=slug, status='success')
    return jsonify({'status': 'success', 'template': template.to_dict()})


# --------------------------------------------------------------------------- #
# Notificaciones in-app
# --------------------------------------------------------------------------- #

@admin_bp.route('/notifications')
@login_required
def list_notifications():
    """Notificaciones del usuario, más las globales."""
    if not current_user.pref_notifications:
        return jsonify([])

    items = (InAppNotification.query
             .filter(db.or_(InAppNotification.user_id == current_user.id,
                            InAppNotification.user_id.is_(None)))
             .order_by(InAppNotification.created_at.desc())
             .limit(50).all())
    return jsonify([n.to_dict() for n in items])


@admin_bp.route('/notifications/read', methods=['POST'])
@login_required
def mark_notifications_read():
    """Marca como leídas: todas las propias, o las indicadas."""
    ids = _payload().get('ids')
    query = InAppNotification.query.filter(
        db.or_(InAppNotification.user_id == current_user.id,
               InAppNotification.user_id.is_(None)))
    if ids:
        query = query.filter(InAppNotification.id.in_(ids))
    query.update({'is_read': True}, synchronize_session=False)
    db.session.commit()
    return jsonify({'status': 'success'})


@admin_bp.route('/notifications', methods=['DELETE'])
@login_required
def delete_notifications():
    """Elimina las notificaciones propias; las globales no se tocan."""
    InAppNotification.query.filter_by(user_id=current_user.id).delete(
        synchronize_session=False)
    db.session.commit()
    return jsonify({'status': 'success'})


# --------------------------------------------------------------------------- #
# Respaldo y restauración
# --------------------------------------------------------------------------- #

@admin_bp.route('/backup')
@login_required
@admin_required
def export_backup():
    """Descarga la configuración del sistema como paquete ZIP.

    Incluye la identidad del portal, LDAP, SMTP, las plantillas y las cuentas
    locales. El logo viaja dentro de system_config, ya que se guarda como data
    URI y no como archivo.
    """
    import io
    import json
    import zipfile
    from datetime import datetime

    from flask import send_file

    from app.modules.auth.models import User

    system = SystemConfig.query.first()
    auth = AuthConfig.query.first()
    smtp = SMTPConfig.query.first()

    payload = {
        'version': '2.0',
        'timestamp': datetime.now().isoformat(),
        'exported_by': current_user.email,
        'payload': {
            'system_config': system.to_dict() if system else {},
            'auth_config': auth.to_dict() if auth else {},
            'smtp_config': smtp.to_dict() if smtp else {},
            # Solo cuentas locales: las de LDAP y SSO las provee el directorio.
            'users': [{
                'email': u.email,
                'nombre': u.nombre,
                'password_hash': u.password_hash,
                'role': u.role,
                'auth_source': u.auth_source,
                'is_active': u.is_active,
            } for u in User.query.filter_by(auth_source='local').all()],
            'templates': [t.to_dict() for t in NotificationTemplate.query.all()],
        },
    }

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('nexus_config.json', json.dumps(payload, indent=2))
    buffer.seek(0)

    add_audit_log('EXPORTAR CONFIGURACIÓN', module='Ajustes', status='success',
                  detail='Respaldo descargado en ZIP')

    stamp = datetime.now().strftime('%Y-%m-%d')
    return send_file(buffer, mimetype='application/zip', as_attachment=True,
                     download_name=f'nexus_backup_{stamp}.zip')


@admin_bp.route('/backup', methods=['POST'])
@login_required
@admin_required
def import_backup():
    """Restaura la configuración desde un paquete ZIP exportado."""
    import json
    import zipfile

    if 'file' not in request.files:
        return _error('No se recibió el archivo.')

    upload = request.files['file']
    if not zipfile.is_zipfile(upload):
        return _error('El archivo no es un paquete ZIP válido.')

    upload.seek(0)
    try:
        with zipfile.ZipFile(upload) as archive:
            if 'nexus_config.json' not in archive.namelist():
                return _error('El paquete no contiene nexus_config.json.')
            with archive.open('nexus_config.json') as handle:
                data = json.load(handle)
    except (zipfile.BadZipFile, json.JSONDecodeError) as exc:
        return _error(f'No se pudo leer el paquete: {exc}')

    payload = data.get('payload') or {}
    restored = []

    system_data = payload.get('system_config')
    if system_data:
        config = SystemConfig.query.first() or SystemConfig()
        for field in ('portal_name', 'portal_identity_type', 'portal_icon',
                      'bg_color', 'text_color'):
            if field in system_data:
                setattr(config, field, system_data[field])
        db.session.add(config)
        restored.append('portal')

    auth_data = payload.get('auth_config')
    if auth_data:
        config = AuthConfig.query.first() or AuthConfig()
        for field in ('ldap_host', 'ldap_port', 'ldap_ssl', 'ldap_base_dn',
                      'ldap_user', 'ldap_user_attr', 'ldap_group_admin',
                      'ldap_group_user', 'ldap_role_mappings'):
            if field in auth_data:
                setattr(config, field, auth_data[field])
        db.session.add(config)
        restored.append('directorio')

    smtp_data = payload.get('smtp_config')
    if smtp_data:
        config = SMTPConfig.query.first() or SMTPConfig()
        for field in ('server', 'port', 'encryption', 'auth_enabled',
                      'username', 'sender_name'):
            if field in smtp_data:
                setattr(config, field, smtp_data[field])
        db.session.add(config)
        restored.append('correo')

    for item in payload.get('templates') or []:
        slug = item.get('slug')
        if not slug:
            continue
        template = NotificationTemplate.query.filter_by(slug=slug).first()
        if template is None:
            template = NotificationTemplate(slug=slug, name=item.get('name', slug),
                                            subject=item.get('subject', ''),
                                            body=item.get('body', ''))
            db.session.add(template)
        else:
            template.name = item.get('name', template.name)
            template.subject = item.get('subject', template.subject)
            template.body = item.get('body', template.body)
        template.is_html = bool(item.get('is_html', template.is_html))

    from app.modules.auth.models import User
    users_added = 0
    for item in payload.get('users') or []:
        email = (item.get('email') or '').strip().lower()
        if not email or User.query.filter(db.func.lower(User.email) == email).first():
            continue
        # Se conserva el hash: el respaldo no contiene contraseñas en claro.
        db.session.add(User(
            email=email,
            nombre=item.get('nombre'),
            password_hash=item.get('password_hash'),
            role=item.get('role') or 'usuario',
            auth_source=item.get('auth_source') or 'local',
            is_active=bool(item.get('is_active', True)),
        ))
        users_added += 1

    db.session.commit()
    if users_added:
        restored.append(f'{users_added} usuario(s)')

    add_audit_log('IMPORTAR CONFIGURACIÓN', module='Ajustes', status='success',
                  detail=f"Restaurado: {', '.join(restored) or 'nada'}")
    return jsonify({'status': 'success', 'restored': restored})
