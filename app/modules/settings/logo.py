"""Validación del logo del portal (FNC-029, movido de `api/admin.py`).

El logo se guarda como data URI en la base de datos, no como archivo: así el
backend no necesita directorio de subidas ni servir estáticos, y el logo
viaja con el resto de la configuración en los respaldos.
"""

MAX_LOGO_BYTES = 512 * 1024
ALLOWED_LOGO_TYPES = ('image/png', 'image/jpeg', 'image/gif', 'image/webp',
                      'image/svg+xml')


def validar_logo(value):
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
