import ssl
import os
import logging
from ldap3 import Server, Connection, ALL, Tls
from ldap3.utils.log import set_library_log_detail_level, EXTENDED
from datetime import datetime
from app.authz import ROLE_USER
from app.modules.directory.configuracion import (ErrorConfiguracionDirectorio,
                                                 directorio_activo)
from app.modules.directory.ldap_client import ClienteDirectorio, ErrorDirectorio
from app.modules.notifications.services import send_notification_by_slug

logger = logging.getLogger(__name__)

if os.getenv('DEBUG_LDAP') == 'true':
    set_library_log_detail_level(EXTENDED)
    ldap3_logger = logging.getLogger('ldap3')
    ldap3_logger.setLevel(logging.DEBUG)
    if not ldap3_logger.handlers:
        os.makedirs(os.path.join(os.getcwd(), 'logs'), exist_ok=True)
        fh = logging.FileHandler(os.path.join(os.getcwd(), 'logs', 'ldap_debug.log'))
        fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        ldap3_logger.addHandler(fh)
        ldap3_logger.addHandler(logging.StreamHandler())

# Respuesta única de login fallido (directorio y cuenta local): no distingue
# usuario inexistente, contraseña incorrecta ni fallo del directorio (SEG-12).
MENSAJE_CREDENCIALES = 'Credenciales incorrectas.'

# Origen de las cuentas creadas por el login de directorio.
ORIGEN_DIRECTORIO = 'ldap'


def _fallo(motivo):
    """Resultado de un login fallido; `motivo` es solo para la auditoría."""
    return {"status": "error", "message": MENSAJE_CREDENCIALES, "motivo": motivo}


def authenticate_user_ldap(identificador, password):
    """
    Autentica contra OpenLDAP con el cliente centralizado y sincroniza el perfil.

    - Busca por `LDAP_USER_ATTR` (filtro escapado) y valida la contraseña con
      un bind de la persona sobre TLS validado (FNC-040).
    - La cuenta local se busca solo por el `mail` del directorio, nunca por
      lo escrito; sin `mail` no hay acceso.
    - Todo fallo devuelve `MENSAJE_CREDENCIALES`; el detalle va en `motivo`.
    - Un intento nunca borra cuentas locales (SEG-01, SEC-AUTH-08).
    - El directorio no asigna rol: una cuenta nueva entra como `usuario` y una
      existente conserva el rol del portal (RF-04, SEG-10, SEC-AUTH-07).
    """
    if not directorio_activo():
        return _fallo('directorio no configurado')
    if not identificador or not password:
        return _fallo('usuario o contraseña vacíos')
    try:
        cliente = ClienteDirectorio()
        persona = cliente.buscar_usuario(identificador)
        if persona is None:
            return _fallo('usuario no encontrado en el directorio')
        if not cliente.verificar_contrasena(persona, password):
            return _fallo('contraseña incorrecta')
        if not persona.atributos.get('mail'):
            # La cuenta local se identifica por correo; sin `mail` no se
            # enlaza por el uid, que podría coincidir con una cuenta local.
            return _fallo('la persona no tiene correo en el directorio')
    except (ErrorDirectorio, ErrorConfiguracionDirectorio) as exc:
        return _fallo(f'directorio: {exc}')
    except Exception:
        logger.exception('Login de directorio: error inesperado')
        return _fallo('error inesperado del directorio')
    return _sincronizar_cuenta(persona)


def _sincronizar_cuenta(persona):
    """Crea o actualiza la cuenta local de una persona autenticada."""
    from app.modules.auth.models import User
    from app.modules.audit.services import add_audit_log
    from app import db

    correo = persona.atributos['mail']
    nombre = (persona.atributos.get('displayName')
              or persona.atributos.get('cn') or correo)
    try:
        cuenta = User.query.filter_by(email=correo).first()
        es_nueva = cuenta is None
        if es_nueva:
            cuenta = User(email=correo, nombre=nombre, role=ROLE_USER,
                          auth_source=ORIGEN_DIRECTORIO, is_active=True)
            cuenta.password_hash = None
            db.session.add(cuenta)
        else:
            # El rol no se toca: lo asigna el superadmin en el portal.
            cuenta.nombre = nombre
            cuenta.auth_source = ORIGEN_DIRECTORIO
        cuenta.last_login_at = datetime.now()
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception('Login de directorio: fallo al registrar la cuenta')
        return _fallo('error al registrar la cuenta local')

    if es_nueva:
        add_audit_log("usuario creado", status="success", target=correo,
                      target_user_id=cuenta.id,
                      detail="Alta por login de directorio con rol usuario")
        _avisar_alta(correo, nombre)
    return {"status": "success", "user": cuenta}


def _avisar_alta(correo, nombre):
    """Correo de bienvenida; un fallo al notificar no impide el acceso."""
    if os.getenv('NOTIFY_USER_CREATED', 'true').lower() != 'true':
        return
    base_url = os.getenv('BASE_URL', '').rstrip('/')
    try:
        send_notification_by_slug('usuario_creado', correo, context={
            'nombre': nombre,
            'usuario': correo,
            'base_url': base_url,
            'url': f"{base_url}/auth/login"
        })
    except Exception:
        logger.exception('Login de directorio: fallo al enviar la bienvenida')


def purge_inactive_users(days=30):
    """
    RUTINA DE HIGIENE: Elimina usuarios que no han iniciado sesión en X días.
    """
    from app.modules.auth.models import User
    from app.modules.audit.services import add_audit_log
    from app import db
    from datetime import datetime, timedelta

    cutoff = datetime.now() - timedelta(days=days)
    
    try:
        # No purgar administradores nunca por seguridad
        inactive_users = User.query.filter(
            User.last_login_at < cutoff,
            User.role != 'administrador'
        ).all()
        
        count = len(inactive_users)
        purged_names = [user.email for user in inactive_users]
        
        for user in inactive_users:
            email = user.email
            db.session.delete(user)
            add_audit_log("usuario purgado", status="warning", detail=f"Inactividad > {days} días: Usuario {email} eliminado automáticamente")
            
        db.session.commit()
        return {"status": "success", "purged_count": count, "purged_names": purged_names}
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": "Error al conectar con LDAP."}

def validate_ldap_connection(host, port, use_ssl=False, bind_dn=None, bind_pass=None):
    """
    Realiza una prueba de conexión y bind contra un servidor LDAP.
    """
    try:
        tls_config = None
        if use_ssl:
            tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1_2)

        server = Server(
            host, 
            port=int(port), 
            use_ssl=use_ssl, 
            tls=tls_config, 
            get_info=ALL,
            connect_timeout=5
        )

        with Connection(server, user=bind_dn, password=bind_pass, auto_bind=True, auto_referrals=False) as conn:
            return {
                "status": "success",
                "message": "Conexión establecida correctamente",
                "info": str(server.info) if server.info else "Anonimo"
            }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Fallo de conexión: {str(e)}"
        }
