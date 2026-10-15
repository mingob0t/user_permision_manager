"""Respuestas comunes de la API v1 (contrato `docs/contratos/README.md`).

Primer paso del duplicado D-03 (FNC-044): las respuestas de error con `code`
salen de aquí; `admin.py` converge después.
"""

from flask import jsonify


def error_response(message, status=400, code=None, fields=None):
    """Error estándar: `{"status": "error", "message", "code"?, "fields"?}`.

    `message` va en español y sin datos internos; `code` es el código del
    contrato y `fields` el detalle por campo de un `422 validacion`.
    """
    cuerpo = {'status': 'error', 'message': message}
    if code:
        cuerpo['code'] = code
    if fields:
        cuerpo['fields'] = fields
    return jsonify(cuerpo), status
