"""Errores de las solicitudes con su código y HTTP de contrato.

Reusan `ErrorDeAcceso` (FNC-054): el endpoint responde
`error_response(*e.respuesta)`. `nivel_vigente` y `validacion` vienen de
`access.errores`; aquí solo los propios de `solicitudes.md`.
"""
from app.modules.access.errores import ErrorDeAcceso


def solicitud_duplicada():
    return ErrorDeAcceso('Ya tienes una solicitud pendiente para esta '
                         'plataforma.', 409, 'solicitud_duplicada')


def ya_administra_area():
    return ErrorDeAcceso('Ya administras esta área; tienes acceso '
                         'automático.', 409, 'ya_administra_area')


def plataforma_no_disponible():
    return ErrorDeAcceso('La plataforma está inactiva o sin integración '
                         'configurada.', 409, 'plataforma_no_disponible')


def sin_permiso():
    """El superadmin no solicita: tiene acceso por defecto (P6)."""
    return ErrorDeAcceso('No tienes permiso para esta acción.', 403,
                         'sin_permiso')
