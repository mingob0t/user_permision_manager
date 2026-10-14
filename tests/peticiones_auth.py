"""Peticiones y comprobaciones comunes de las pruebas de autenticación (FNC-022)."""

from app.modules.audit.models import AuditLog

A = '/api/v1/auth'
RUTA_ME = '/api/v1/me'

MENSAJE_CREDENCIALES = 'Credenciales incorrectas.'


def iniciar_sesion_api(cliente, email, contrasena, metodo='local'):
    """`POST /api/v1/auth/login` real (no arma la sesión a mano)."""
    return cliente.post(f'{A}/login', json={'email': email,
                                            'password': contrasena,
                                            'method': metodo})


def usuario_en_sesion(cliente):
    """Correo del usuario con sesión en `cliente`, o None si no hay sesión."""
    respuesta = cliente.get(RUTA_ME)
    if respuesta.status_code == 401:
        return None
    assert respuesta.status_code == 200, respuesta.get_json()
    return respuesta.get_json()['email']


def hay_auditoria(prefijo_accion, status=None):
    """True si existe un registro de auditoría cuya acción empieza así."""
    consulta = AuditLog.query.filter(AuditLog.action.like(f'{prefijo_accion}%'))
    if status:
        consulta = consulta.filter_by(status=status)
    return consulta.first() is not None
