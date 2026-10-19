"""Lista blanca y validación de campos de `POST/PUT /platforms` (FNC-046).

Contrato `docs/contratos/plataformas-integracion.md`, sección "Entrada". Cada
validador devuelve el valor limpio o un mensaje de error para `fields`.
"""
from urllib.parse import urlsplit

from app.modules.directory.configuracion import es_ip_literal
from app.modules.platforms.tipos import CAMPOS_DN, LARGO_DN, TIPOS_INTEGRACION
from app.utils.naming import sanitize_display_name

CAMPOS_PERMITIDOS = frozenset({
    'name', 'description', 'area_id', 'direct_link', 'logo_url', 'icon',
    'bg_color', 'text_color', 'status', 'integration_type',
    *CAMPOS_DN.values(),
})
OBLIGATORIOS_ALTA = ('name', 'description', 'area_id', 'integration_type')

NOMBRE_MIN, NOMBRE_MAX = 2, 100
DESCRIPCION_MIN, DESCRIPCION_MAX = 1, 1000
URL_MAX = 255
# Solo https (SEC-SES-10, SEG-24); http no se justificó (decisión de FNC-046).
ESQUEMAS_URL = ('https',)
CAMPOS_URL = ('direct_link', 'logo_url')
# Campos visuales "igual que hoy": texto libre hasta el largo de su columna.
LARGO_CAMPOS_TEXTO = {'icon': 50, 'bg_color': 20, 'text_color': 20,
                      'status': 20}
ESPACIO_O_CONTROL = 0x20
CARACTER_DEL = 0x7f

MENSAJE_OBLIGATORIO = 'Es obligatorio.'
MENSAJE_URL = 'Usa una dirección https://.'
MENSAJE_DN_BASE = 'El grupo debe estar en la OU de plataformas.'


def campos_fuera_de_lista(datos):
    """Campos fuera de la lista blanca (distinto de `users/roles.py`, que es
    una lista negra)."""
    return sorted(set(datos) - CAMPOS_PERMITIDOS)


def _texto(valor, minimo, maximo):
    if not isinstance(valor, str):
        return None, 'Debe ser texto.'
    valor = valor.strip()
    if not minimo <= len(valor) <= maximo:
        return None, f'Debe tener entre {minimo} y {maximo} caracteres.'
    return valor, None


def validar_nombre(valor):
    if not isinstance(valor, str):
        return None, 'Debe ser texto.'
    return _texto(sanitize_display_name(valor, fallback=''), NOMBRE_MIN,
                  NOMBRE_MAX)


def validar_url(valor):
    """`None`/`''` → sin enlace; si no, `https://host...` sin espacios."""
    if valor is None or valor == '':
        return None, None
    if not isinstance(valor, str):
        return None, MENSAJE_URL
    valor = valor.strip()
    if not valor:
        return None, None
    if len(valor) > URL_MAX:
        return None, f'Debe tener como máximo {URL_MAX} caracteres.'
    if any(ord(c) <= ESPACIO_O_CONTROL or ord(c) == CARACTER_DEL
           for c in valor) or '\\' in valor:
        return None, MENSAJE_URL
    partes = urlsplit(valor)
    try:
        partes.port  # un puerto inválido lanza ValueError
    except ValueError:
        return None, MENSAJE_URL
    if (partes.scheme.lower() not in ESQUEMAS_URL or not partes.hostname
            or partes.username is not None or partes.password is not None
            or es_ip_literal(partes.hostname)):
        return None, MENSAJE_URL
    return valor, None


def url_segura(valor):
    """La URL guardada si cumple `validar_url`; si no, `None` (las guardadas
    antes de FNC-046 pueden traer `javascript:` o `http:`)."""
    limpio, error = validar_url(valor)
    return None if error else limpio


def validar_area_id(valor):
    if isinstance(valor, bool) or not isinstance(valor, int):
        return None, 'Debe ser un identificador de área.'
    return valor, None


def validar_tipo(valor):
    if valor not in TIPOS_INTEGRACION:
        return None, 'Usa ldap o conector.'
    return valor, None


def validar_dn(valor):
    """Forma del DN (texto, largo); la base se valida en `grupos.dn_en_base`."""
    if valor is None:
        return None, None
    if not isinstance(valor, str) or not valor.strip():
        return None, MENSAJE_DN_BASE
    valor = valor.strip()
    if len(valor) > LARGO_DN:
        return None, f'Debe tener como máximo {LARGO_DN} caracteres.'
    return valor, None


def _validar_texto_visual(campo):
    def validar(valor):
        if valor is None:
            return None, None
        return _texto(valor, 0, LARGO_CAMPOS_TEXTO[campo])
    return validar


VALIDADORES = {
    'name': validar_nombre,
    'description': lambda v: _texto(v, DESCRIPCION_MIN, DESCRIPCION_MAX),
    'area_id': validar_area_id,
    'integration_type': validar_tipo,
    **{campo: validar_url for campo in CAMPOS_URL},
    **{campo: validar_dn for campo in CAMPOS_DN.values()},
    **{campo: _validar_texto_visual(campo) for campo in LARGO_CAMPOS_TEXTO},
}


def validar_campos(datos, alta=False):
    """(valores limpios de los campos presentes, errores por campo)."""
    limpios, errores = {}, {}
    if alta:
        for campo in OBLIGATORIOS_ALTA:
            if datos.get(campo) in (None, ''):
                errores[campo] = MENSAJE_OBLIGATORIO
    for campo, valor in datos.items():
        if campo in errores:
            continue
        limpio, error = VALIDADORES[campo](valor)
        if error:
            errores[campo] = error
        else:
            limpios[campo] = limpio
    return limpios, errores
