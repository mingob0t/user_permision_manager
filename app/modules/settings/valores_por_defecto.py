"""Valores por defecto de la identidad del portal (FNC-121).

Los usa el modelo `SystemConfig` (al insertar) y la API cuando todavía no hay
registro, para que la respuesta nunca traiga `null` en estos campos.
"""

PORTAL_NAME_POR_DEFECTO = 'Nexus Core AI'
PORTAL_IDENTITY_TYPE_POR_DEFECTO = 'icon'  # 'icon' o 'image'
BG_COLOR_POR_DEFECTO = '#0f172a'
TEXT_COLOR_POR_DEFECTO = '#ffffff'
