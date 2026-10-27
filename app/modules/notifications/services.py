import html
import logging
import os
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.modules.notifications.models import SMTPConfig, NotificationTemplate, InAppNotification

logger = logging.getLogger(__name__)


class SmtpSettings:
    """Parámetros de conexión SMTP, vengan del .env o de la base de datos."""

    def __init__(self, server, port, encryption, auth_enabled, username,
                 password, sender_name, sender_email=None, source='db'):
        self.server = server
        self.port = port
        self.encryption = encryption
        self.auth_enabled = auth_enabled
        self.username = username
        self.password = password
        self.sender_name = sender_name
        # Remitente visible. Sin él se usa el usuario de autenticación, que en
        # servidores con dominio propio no siempre es una dirección válida.
        self.sender_email = sender_email or username
        self.source = source

    @property
    def is_usable(self):
        return bool(self.server and self.port)

    def __repr__(self):
        return (f"<SmtpSettings {self.source} {self.server}:{self.port} "
                f"{self.encryption}>")


def _env_flag(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on', 'si', 'sí')


def smtp_settings_from_env():
    """Lee la configuración SMTP del entorno. None si no hay servidor definido."""
    server = (os.getenv('SMTP_SERVER') or '').strip()
    if not server:
        return None

    try:
        port = int(os.getenv('SMTP_PORT', '587'))
    except ValueError:
        port = 587

    encryption = (os.getenv('SMTP_ENCRYPTION') or 'starttls').strip().lower()
    if encryption not in ('starttls', 'ssl', 'none'):
        encryption = 'starttls'

    username = (os.getenv('SMTP_USER') or '').strip() or None
    password = os.getenv('SMTP_PASSWORD') or None

    return SmtpSettings(
        server=server,
        port=port,
        encryption=encryption,
        # Si no se declara, se asume autenticación cuando hay usuario y clave.
        auth_enabled=_env_flag('SMTP_AUTH', bool(username and password)),
        username=username,
        password=password,
        sender_name=(os.getenv('SMTP_SENDER_NAME') or 'Nexus').strip(),
        sender_email=(os.getenv('SMTP_SENDER_EMAIL') or '').strip() or None,
        source='env',
    )


def resolve_smtp_settings():
    """Decide qué configuración SMTP usar.

    Con SMTP_FORCE_ENV activo se usa siempre la del entorno y se ignora la
    guardada en la base de datos: es lo que permite fijar el servidor de correo
    por despliegue y que nadie lo cambie desde la interfaz. En caso contrario
    manda la base de datos, y el entorno solo actúa como respaldo si en la BD
    no hay nada configurado.
    """
    from_env = smtp_settings_from_env()

    if _env_flag('SMTP_FORCE_ENV'):
        if from_env and from_env.is_usable:
            return from_env
        # Se pidió forzar el .env pero está incompleto: mejor fallar visiblemente
        # que enviar por un servidor distinto del esperado.
        return None

    config = SMTPConfig.query.first()
    if config and config.server:
        return SmtpSettings(
            server=config.server,
            port=config.port,
            encryption=config.encryption,
            auth_enabled=config.auth_enabled,
            username=config.username,
            password=config.password,
            sender_name=config.sender_name,
            source='db',
        )

    return from_env if (from_env and from_env.is_usable) else None


def open_smtp(settings):
    """Abre la conexión SMTP según el cifrado configurado."""
    if settings.encryption == 'ssl':
        smtp = smtplib.SMTP_SSL(settings.server, settings.port, timeout=10)
    else:
        smtp = smtplib.SMTP(settings.server, settings.port, timeout=10)
        if settings.encryption == 'starttls':
            smtp.starttls()

    if os.getenv('DEBUG_SMTP', '').strip().lower() == 'true':
        smtp.set_debuglevel(1)

    if settings.auth_enabled and settings.username and settings.password:
        smtp.login(settings.username, settings.password)
    return smtp

def add_in_app_notification(type, title, message, user_id=None):
    """
    Creates a persistent in-app notification.
    type: success, error, warning, info
    user_id: ID of the user (NULL for global)
    """
    from app import db
    try:
        notif = InAppNotification(
            type=type,
            title=title,
            message=message,
            user_id=user_id
        )
        db.session.add(notif)
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error adding notification: {e}")
        db.session.rollback()
        return False


def send_test_email(server, port, encryption, username, password, sender_name, target_email):
    """
    Sends a test email to verify SMTP configuration.
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = f"{sender_name} <{username}>"
        msg['To'] = target_email
        msg['Subject'] = "⚡ Nexus Premium - SMTP Verification"

        body = f"""
        <html>
            <body style="font-family: sans-serif; color: #1a1a1a;">
                <h2 style="color: #6366f1;">⚡ Nexus System Verification</h2>
                <p>Usted está recibiendo este mensaje porque se ha solicitado una prueba de conectividad desde el panel de administración.</p>
                <div style="background: #f8fafc; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0;">
                    <p><b>Status:</b> Conexión Exitosa</p>
                    <p><b>Servidor:</b> {server}:{port}</p>
                    <p><b>Cifrado:</b> {encryption.upper()}</p>
                </div>
            </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))

        if encryption == 'ssl':
            smtp = smtplib.SMTP_SSL(server, port, timeout=10)
        else:
            smtp = smtplib.SMTP(server, port, timeout=10)
            if encryption == 'starttls':
                smtp.starttls()
                
        import os
        if os.getenv('DEBUG_SMTP') == 'true':
            smtp.set_debuglevel(1)

        if username and password:
            smtp.login(username, password)

        smtp.send_message(msg)
        smtp.quit()
        return {"status": "success", "message": "Correo de prueba enviado correctamente"}
    except Exception as e:
        return {"status": "error", "message": "Error al enviar correo de prueba."}

# `{clave}` de una plantilla: letras, dígitos y guion bajo.
PATRON_VARIABLE = re.compile(r'\{(\w+)\}')
# Saltos de línea que, en una cabecera, abrirían otra (SEC-MAIL-01).
PATRON_SALTO_DE_LINEA = re.compile(r'[\r\n]+')


def render_template_text(text, context=None, escape_html=False):
    """Sustituye `{clave}` por su valor en una sola pasada (SEC-MAIL-01, 02).

    - Una clave sin valor queda tal cual.
    - Con `escape_html` los valores pasan por `html.escape`: el texto del
      usuario (justificación, motivo, nombre) no puede meter HTML ni enlaces.
    - El valor insertado no se vuelve a sustituir: `{url}` dentro de una
      justificación queda literal.
    """
    valores = context or {}

    def _valor(coincidencia):
        clave = coincidencia.group(1)
        if clave not in valores:
            return coincidencia.group(0)
        texto = str(valores[clave])
        return html.escape(texto) if escape_html else texto

    return PATRON_VARIABLE.sub(_valor, text)


def render_subject(subject, context=None):
    """Asunto sin saltos de línea: ni los valores ni la plantilla agregan cabeceras."""
    return PATRON_SALTO_DE_LINEA.sub(' ', render_template_text(subject, context))


def notifications_enabled():
    """Interruptor global `ENABLE_NOTIFICATIONS`: solo `true` activa el envío."""
    return os.getenv('ENABLE_NOTIFICATIONS', 'true').lower() == 'true'


def send_notification_by_slug(slug, target_email, context=None):
    """
    Sends a pre-defined notification template using the global SMTP configuration.
    """
    from app import db
    import os
    from dotenv import load_dotenv
    
    # Reload env to catch changes without restart
    load_dotenv(override=True)
    
    # Global Switch Check
    if not notifications_enabled():
        print(f"🔕 Notificaciones desactivadas globalmente (.env). Omitiendo slug: {slug}")
        return {"status": "success", "message": "Notifications disabled globally"}

    try:
        config = resolve_smtp_settings()
        template = NotificationTemplate.query.filter_by(slug=slug).first()
        if config is None:
            return {"status": "error",
                    "message": "No hay configuración SMTP utilizable."}
        if not template:
            return {"status": "error", "message": f"Plantilla '{slug}' no encontrada"}

        body = render_template_text(template.body, context,
                                    escape_html=bool(template.is_html))
        subject = render_subject(template.subject, context)

        msg = MIMEMultipart()
        msg['From'] = f"{config.sender_name} <{config.sender_email}>"
        msg['To'] = target_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html' if template.is_html else 'plain'))

        smtp = open_smtp(config)
        smtp.send_message(msg)
        smtp.quit()
        return {"status": "success",
                "message": f"Notificación '{slug}' enviada",
                "source": config.source}

    except Exception as e:
        return {"status": "error", "message": "Error interno enviando notificación."}


SLUG_USUARIO_CREADO = 'usuario_creado'
VAR_NOTIFY_USER_CREATED = 'NOTIFY_USER_CREATED'


def avisar_usuario_creado(correo, nombre, base_url, url=None):
    """Correo de bienvenida a una cuenta recién creada (D-04, FNC-030).

    Solo si `NOTIFY_USER_CREATED` es `true` (por omisión). Un fallo al
    notificar nunca impide el acceso: se registra en el log y se sigue.
    `url` es el enlace de la plantilla (por omisión, `base_url`).
    """
    if os.getenv(VAR_NOTIFY_USER_CREATED, 'true').lower() != 'true':
        return
    try:
        send_notification_by_slug(SLUG_USUARIO_CREADO, correo, context={
            'nombre': nombre, 'usuario': correo,
            'base_url': base_url, 'url': url or base_url,
        })
    except Exception:
        logger.exception('Fallo al enviar el aviso de usuario creado')
