"""API v1 de respaldo y restauración de la configuración (FNC-029, movido de
`api/admin.py`). Exclusivo del superadmin.
"""

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app import db
from app.authz import admin_required
from app.modules.api.helpers import error_response
from app.modules.audit.services import add_audit_log
from app.modules.auth.models import AuthConfig
from app.modules.notifications.models import NotificationTemplate, SMTPConfig
from app.modules.settings.models import SystemConfig

respaldo_api_bp = Blueprint('api_backup', __name__, url_prefix='/api/v1')


@respaldo_api_bp.route('/backup')
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


@respaldo_api_bp.route('/backup', methods=['POST'])
@login_required
@admin_required
def import_backup():
    """Restaura la configuración desde un paquete ZIP exportado."""
    import json
    import zipfile

    if 'file' not in request.files:
        return error_response('No se recibió el archivo.')

    upload = request.files['file']
    if not zipfile.is_zipfile(upload):
        return error_response('El archivo no es un paquete ZIP válido.')

    upload.seek(0)
    try:
        with zipfile.ZipFile(upload) as archive:
            if 'nexus_config.json' not in archive.namelist():
                return error_response(
                    'El paquete no contiene nexus_config.json.')
            with archive.open('nexus_config.json') as handle:
                data = json.load(handle)
    except (zipfile.BadZipFile, json.JSONDecodeError) as exc:
        return error_response(f'No se pudo leer el paquete: {exc}')

    payload = data.get('payload') or {}
    restored = []

    system_data = payload.get('system_config')
    if system_data:
        config = SystemConfig.query.first() or SystemConfig.por_defecto()
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
