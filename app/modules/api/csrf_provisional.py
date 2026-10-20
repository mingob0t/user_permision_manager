"""Protección provisional de escrituras de la API v1 mientras no hay CSRF
real (FNC-008, P13). Extraída de `access_requests/api.py` (FNC-056) en FNC-058.

- `Sec-Fetch-Site: cross-site` → `403 csrf_invalido`.
- Cuerpo no JSON → `415 tipo_no_soportado`: un formulario de otro sitio no
  puede enviar `Content-Type: application/json` sin *preflight* CORS.

No sustituye a FNC-008 (token en cabecera y `Origin`, SEC-SES-04): es
requisito antes de desplegar en staging o prod. Uso, debajo de
`@login_required` (y del decorador de rol, si lo hay):

    @login_required
    @escritura_del_portal
    def vista(): ...
"""
from functools import wraps

from flask import request

from app.modules.api.helpers import error_response

CSRF_INVALIDO = ('La petición no viene del portal.', 403, 'csrf_invalido')
TIPO_NO_SOPORTADO = ('El cuerpo debe ser JSON.', 415, 'tipo_no_soportado')
SITIO_AJENO = 'cross-site'


def rechazo_de_escritura():
    """Respuesta de error si la escritura no viene del portal o no es JSON."""
    if request.headers.get('Sec-Fetch-Site', '').lower() == SITIO_AJENO:
        return error_response(*CSRF_INVALIDO)
    if not request.is_json:
        return error_response(*TIPO_NO_SOPORTADO)
    return None


def escritura_del_portal(vista):
    """Decorador: corta con `rechazo_de_escritura()` antes de la vista."""
    @wraps(vista)
    def envoltura(*args, **kwargs):
        rechazo = rechazo_de_escritura()
        if rechazo is not None:
            return rechazo
        return vista(*args, **kwargs)
    return envoltura
