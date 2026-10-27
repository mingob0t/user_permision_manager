"""API v1 de notificaciones (FNC-029, movido de `api/admin.py`).

SMTP y plantillas de correo son exclusivos del superadmin; las notificaciones
in-app son de cada usuario.
"""

from flask import Blueprint, jsonify
from flask_login import current_user, login_required

from app import db
from app.authz import admin_required
from app.modules.api.helpers import error_response, leer_cuerpo
from app.modules.audit.services import add_audit_log
from app.modules.notifications.models import (InAppNotification,
                                              NotificationRead,
                                              NotificationTemplate, SMTPConfig)

notifications_api_bp = Blueprint('api_notifications', __name__,
                                 url_prefix='/api/v1')


def _smtp_forced():
    """True si SMTP_FORCE_ENV fija la configuración desde el entorno."""
    from app.modules.notifications.services import _env_flag
    return _env_flag('SMTP_FORCE_ENV')


# --------------------------------------------------------------------------- #
# SMTP
# --------------------------------------------------------------------------- #

@notifications_api_bp.route('/smtp')
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


@notifications_api_bp.route('/smtp', methods=['PUT'])
@login_required
@admin_required
def save_smtp():
    # Con el entorno forzado, guardar en la base de datos no tendría efecto:
    # es mejor rechazarlo que dejar creer que el cambio se aplicó.
    if _smtp_forced():
        return error_response(
            'La configuración SMTP está fijada por el entorno (SMTP_FORCE_ENV). '
            'Edítala en el .env del servidor.', 409)

    config = SMTPConfig.query.first()
    if config is None:
        config = SMTPConfig()
        db.session.add(config)

    data, error = leer_cuerpo(None)
    if error is not None:
        return error
    for field in ('server', 'encryption', 'username', 'sender_name'):
        if field in data:
            setattr(config, field, data[field])
    if 'port' in data:
        try:
            config.port = int(data['port'])
        except (TypeError, ValueError):
            return error_response('Puerto no válido.')
    if 'auth_enabled' in data:
        config.auth_enabled = bool(data['auth_enabled'])
    # Una contraseña vacía no borra la guardada.
    if data.get('password'):
        config.password = data['password']

    db.session.commit()
    add_audit_log('ACTUALIZAR SMTP', module='Notificaciones', status='success')
    return jsonify({'status': 'success', 'smtp': config.to_dict()})


@notifications_api_bp.route('/smtp/test', methods=['POST'])
@login_required
@admin_required
def test_smtp():
    """Envía un correo de prueba al destinatario indicado."""
    cuerpo, error = leer_cuerpo(None)
    if error is not None:
        return error
    recipient = (cuerpo.get('email') or current_user.email or '').strip()
    if not recipient or '@' not in recipient:
        return error_response('Indica un correo de destino válido.')

    from app.modules.notifications.services import (resolve_smtp_settings,
                                                    send_test_email)

    config = resolve_smtp_settings()
    if config is None:
        return error_response('No hay configuración SMTP utilizable.')

    try:
        # Se prueba lo que está en vigor; el payload puede sobrescribir campos
        # para validar antes de guardar, salvo si el entorno manda.
        data = {} if config.source == 'env' else cuerpo
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
        return error_response(f'No se pudo enviar: {exc}', 502)

    add_audit_log('PRUEBA SMTP', module='Notificaciones', status='success',
                  detail=f'Destinatario: {recipient}')
    return jsonify({'status': 'success'})


# --------------------------------------------------------------------------- #
# Plantillas de correo
# --------------------------------------------------------------------------- #

@notifications_api_bp.route('/templates')
@login_required
@admin_required
def list_templates():
    templates = NotificationTemplate.query.order_by(
        NotificationTemplate.name).all()
    return jsonify([t.to_dict() for t in templates])


@notifications_api_bp.route('/templates/<slug>', methods=['PUT'])
@login_required
@admin_required
def save_template(slug):
    data, error = leer_cuerpo(None)
    if error is not None:
        return error
    template = NotificationTemplate.query.filter_by(slug=slug).first()

    if template is None:
        if not data.get('name') or not data.get('subject'):
            return error_response('Nombre y asunto son obligatorios.')
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

@notifications_api_bp.route('/notifications')
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
    # Una global cuenta como leída solo si este usuario la leyó.
    leidas = {fila.notification_id for fila in
              NotificationRead.query.filter_by(user_id=current_user.id).all()}
    return jsonify([
        n.to_dict(leida=(n.id in leidas) if n.user_id is None else None)
        for n in items])


@notifications_api_bp.route('/notifications/read', methods=['POST'])
@login_required
def mark_notifications_read():
    """Marca como leídas, solo para quien consulta: todas o las indicadas.

    Las propias cambian `is_read`; las globales se registran en
    `notification_reads` y no afectan a los demás usuarios.
    """
    cuerpo, error = leer_cuerpo(None)
    if error is not None:
        return error
    ids = cuerpo.get('ids')

    propias = InAppNotification.query.filter_by(user_id=current_user.id)
    globales = InAppNotification.query.filter(
        InAppNotification.user_id.is_(None))
    if ids:
        propias = propias.filter(InAppNotification.id.in_(ids))
        globales = globales.filter(InAppNotification.id.in_(ids))
    propias.update({'is_read': True}, synchronize_session=False)

    ya_leidas = {fila.notification_id for fila in
                 NotificationRead.query.filter_by(user_id=current_user.id)}
    for aviso in globales.all():
        if aviso.id not in ya_leidas:
            db.session.add(NotificationRead(notification_id=aviso.id,
                                            user_id=current_user.id))
    db.session.commit()
    return jsonify({'status': 'success'})


@notifications_api_bp.route('/notifications', methods=['DELETE'])
@login_required
def delete_notifications():
    """Elimina las notificaciones propias; las globales no se tocan."""
    InAppNotification.query.filter_by(user_id=current_user.id).delete(
        synchronize_session=False)
    db.session.commit()
    return jsonify({'status': 'success'})
