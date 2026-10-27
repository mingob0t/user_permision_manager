"""Respuestas comunes de la API v1 (contrato `docs/contratos/README.md`).

Duplicado D-03 (FNC-044, FNC-030): las respuestas de error con `code`, la
lectura del cuerpo JSON y la lista blanca de campos (FNC-082) salen de aquí;
`crud.py` y `admin.py` ya no tienen `_payload` ni `_error` propios.
"""

from flask import jsonify, request

# (mensaje, HTTP, code) de los errores de los contratos. Uso:
# `error_response(*NO_ENCONTRADO)`.
NO_ENCONTRADO = ('Recurso no encontrado.', 404, 'no_encontrado')
CAMPO_NO_PERMITIDO = ('Hay campos que no se pueden enviar.', 400,
                      'campo_no_permitido')
CUERPO_INVALIDO = ('Los datos enviados no son válidos.', 400,
                   'cuerpo_invalido')
ROL_RESERVADO = ('Ese rol no se puede asignar.', 403, 'rol_reservado')
OPERACION_PROPIA = ('No puedes cambiar tu propio rol.', 403,
                    'operacion_propia')
ROL_NO_ADMIN = ('El usuario no es administrador de área.', 409,
                'rol_no_admin')
AREA_DUPLICADA = ('Ya existe un área con ese nombre.', 409, 'area_duplicada')
AREA_CON_PLATAFORMAS = ('El área tiene plataformas; muévelas o elimínalas '
                        'antes.', 409, 'area_con_plataformas')
AREA_CON_ACCESOS = ('El área tiene accesos vigentes.', 409,
                    'area_con_accesos')
AREA_CON_OTROS_ADMINS = ('El área tiene otros administradores; solo el '
                         'superadmin puede darla de baja.', 409,
                         'area_con_otros_admins')
# Endpoint que reemplaza a la asignación directa de plataformas (FNC-065).
REEMPLAZO_ASIGNACION = 'POST /access-requests'
MENSAJE_VALIDACION = 'Revisa los campos marcados.'


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


def endpoint_retirado(use):
    """`410` de un endpoint retirado, con el que lo reemplaza (FNC-065).

    Mismo formato que el `410` de los blueprints heredados (`message`, `use`)
    más `code`, como el resto de los errores de `/api/v1`.
    """
    cuerpo = {'status': 'error', 'message': 'Endpoint retirado.',
              'code': 'endpoint_retirado', 'use': use}
    return jsonify(cuerpo), 410


def validation_error(fields):
    """`422 validacion` con el detalle por campo."""
    return error_response(MENSAJE_VALIDACION, 422, 'validacion', fields)


def json_object():
    """Cuerpo JSON como objeto: `{}` si no hay cuerpo, `None` si no es objeto.

    Un arreglo, texto o número en el cuerpo no es un objeto: quien llama
    responde `400 cuerpo_invalido` en lugar de fallar con 500.
    """
    datos = request.get_json(silent=True)
    if datos is None:
        return {}
    return datos if isinstance(datos, dict) else None


def json_payload():
    """Cuerpo JSON tal cual o `{}` si no hay (lectura laxa de `crud` y `admin`).

    No valida que sea un objeto: los endpoints nuevos usan `json_object()` o
    `leer_cuerpo()`, que responden `400 cuerpo_invalido`.
    """
    return request.get_json(silent=True) or {}


def campos_no_permitidos(datos, permitidos=()):
    """Lista blanca (SEC-AUTHZ-09): campos de `datos` fuera de `permitidos`.

    Devuelve la lista ordenada de los rechazados; vacía si todo es válido.
    Con `permitidos` vacío cualquier campo se rechaza (cuerpo `{}`).
    """
    return sorted(set(datos) - set(permitidos))


def campos_prohibidos(datos, prohibidos):
    """Lista negra: campos de `datos` que están en `prohibidos`, ordenados."""
    return sorted(set(prohibidos) & set(datos))


def leer_cuerpo(permitidos=()):
    """Cuerpo JSON validado: `(datos, None)` o `(None, respuesta de error)`.

    `400 cuerpo_invalido` si no es un objeto y `400 campo_no_permitido` si
    trae campos fuera de `permitidos` (por omisión, ninguno).
    """
    datos = json_object()
    if datos is None:
        return None, error_response(*CUERPO_INVALIDO)
    if campos_no_permitidos(datos, permitidos):
        return None, error_response(*CAMPO_NO_PERMITIDO)
    return datos, None


def is_id_list(valor):
    """True si `valor` es una lista de enteros (sin booleanos)."""
    return isinstance(valor, list) and all(
        isinstance(i, int) and not isinstance(i, bool) for i in valor)
