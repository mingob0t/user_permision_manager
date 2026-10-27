"""Entrada de `POST /areas` y `PUT /areas/<id>` (FNC-045).

Fuente: `docs/contratos/areas-y-roles.md` (lista blanca y reglas por campo).
"""

import re

from app import db
from app.modules.core.models import Area
from app.utils.naming import sanitize_display_name

CAMPOS_PERMITIDOS = frozenset({'name', 'description', 'icon', 'color',
                               'status'})

NOMBRE_MIN = 2
NOMBRE_MAX = 100
DESCRIPCION_MAX = 500
ICONO_MAX = 50
# Nombre de ícono: letras, dígitos, guion y guion bajo (decisión del
# orquestador, FNC-045): evita marcado o rutas en un campo que se pinta.
PATRON_ICONO = re.compile(r'[A-Za-z0-9_-]+')
PATRON_COLOR = re.compile(r'#[0-9A-Fa-f]{6}')
ESTADOS = ('Activo', 'Inactivo')

# Valores por omisión del alta (los mismos que usaba `crud.py`).
ICONO_POR_OMISION = 'box'
COLOR_POR_OMISION = '#6366f1'
ESTADO_POR_OMISION = 'Activo'


def validar(datos, es_alta):
    """(valores, errores): valores limpios y errores por campo (`422`).

    En el alta `name` es obligatorio; en la edición solo se validan los campos
    enviados.
    """
    valores, errores = {}, {}
    if es_alta and 'name' not in datos:
        errores['name'] = 'Es obligatorio.'
    for campo, regla in _REGLAS.items():
        if campo in datos:
            valor, problema = regla(datos[campo])
            if problema:
                errores[campo] = problema
            else:
                valores[campo] = valor
    return valores, errores


def nombre_duplicado(nombre, excepto_id=None):
    """True si otra área ya usa `nombre` (sin distinguir mayúsculas).

    Se compara en Python con `casefold`: `lower()` de SQLite no convierte
    letras acentuadas ("Á"), y el número de áreas es pequeño.
    """
    buscado = nombre.casefold()
    return any(
        area_id != excepto_id and existente.casefold() == buscado
        for area_id, existente in db.session.query(Area.id, Area.name))


def _texto(valor):
    return valor.strip() if isinstance(valor, str) else None


def _nombre(valor):
    texto = _texto(valor)
    if texto is None:
        return None, 'Debe ser texto.'
    if len(texto) > NOMBRE_MAX:
        return None, f'Máximo {NOMBRE_MAX} caracteres.'
    limpio = sanitize_display_name(texto, fallback='')
    if len(limpio) < NOMBRE_MIN:
        return None, f'Mínimo {NOMBRE_MIN} caracteres.'
    return limpio, None


def _descripcion(valor):
    if valor is None:
        return None, None
    texto = _texto(valor)
    if texto is None:
        return None, 'Debe ser texto.'
    if len(texto) > DESCRIPCION_MAX:
        return None, f'Máximo {DESCRIPCION_MAX} caracteres.'
    return texto or None, None


def _icono(valor):
    texto = _texto(valor)
    if not texto or len(texto) > ICONO_MAX or not PATRON_ICONO.fullmatch(texto):
        return None, f'Nombre de ícono de hasta {ICONO_MAX} caracteres.'
    return texto, None


def _color(valor):
    texto = _texto(valor)
    if texto is None or not PATRON_COLOR.fullmatch(texto):
        return None, 'Color hexadecimal de 7 caracteres (#rrggbb).'
    return texto, None


def _estado(valor):
    if valor not in ESTADOS:
        return None, f"Debe ser {' o '.join(ESTADOS)}."
    return valor, None


_REGLAS = {
    'name': _nombre,
    'description': _descripcion,
    'icon': _icono,
    'color': _color,
    'status': _estado,
}
