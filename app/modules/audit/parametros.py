"""Parámetros de consulta de la auditoría (FNC-060).

Contrato `docs/contratos/auditoria.md` y convenciones de
`docs/contratos/README.md` (paginación y filtros). Un valor inválido levanta
`ParametroInvalido`; la ruta responde `400 parametro_invalido`.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

from app.modules.audit.events import Evento

# `result` del contrato = columna `status`.
RESULTADOS = frozenset({'success', 'error', 'warning', 'info'})
ACCIONES = frozenset(e.value for e in Evento)

PAGINA_POR_DEFECTO = 1
POR_PAGINA_POR_DEFECTO = 25
POR_PAGINA_MAX = 100
LARGO_MAX_BUSQUEDA = 100
RANGO_MAX_DIAS = 366

# `GET /audit` sin `page` (cliente actual, `?limit=`): por defecto y tope.
LIMITE_POR_DEFECTO = 100
AUDIT_PAGE_SIZE_MAX = 500

# Enteros de consulta (ids, página): más dígitos desbordarían el entero de la BD.
MAX_DIGITOS_ENTERO = 9

# Un `to` con hora es inclusivo: se compara contra el instante siguiente.
INSTANTE_MINIMO = timedelta(microseconds=1)


class ParametroInvalido(ValueError):
    """Parámetro de consulta fuera del contrato; `campo` es su nombre."""

    def __init__(self, campo):
        super().__init__(campo)
        self.campo = campo


@dataclass(frozen=True)
class Filtros:
    action: Optional[str] = None
    result: Optional[str] = None
    area_id: Optional[int] = None
    platform_id: Optional[int] = None
    user_id: Optional[int] = None
    desde: Optional[datetime] = None
    hasta: Optional[datetime] = None  # exclusivo
    q: Optional[str] = None


@dataclass(frozen=True)
class Paginacion:
    page: int
    per_page: int

    @property
    def offset(self):
        return (self.page - 1) * self.per_page


def _entero_positivo(args, campo):
    valor = args.get(campo)
    if valor is None or valor == '':
        return None
    if (not (valor.isascii() and valor.isdigit())
            or len(valor) > MAX_DIGITOS_ENTERO or int(valor) < 1):
        raise ParametroInvalido(campo)
    return int(valor)


def _enumerado(args, campo, permitidos):
    valor = args.get(campo)
    if valor is None or valor == '':
        return None
    if valor not in permitidos:
        raise ParametroInvalido(campo)
    return valor


def _fecha(args, campo):
    """(instante, es_solo_fecha) de un ISO 8601, en la hora local guardada.

    Los registros se guardan en hora local del proceso (`TZ_APP`); una fecha
    con zona se convierte a esa hora antes de comparar.
    """
    valor = args.get(campo)
    if valor is None or valor == '':
        return None, False
    try:
        if len(valor) == len('AAAA-MM-DD'):
            dia = date.fromisoformat(valor)
            return datetime(dia.year, dia.month, dia.day), True
        instante = datetime.fromisoformat(valor)
    except ValueError:
        raise ParametroInvalido(campo) from None
    if instante.tzinfo is not None:
        instante = instante.astimezone().replace(tzinfo=None)
    return instante, False


def leer_filtros(args):
    """Filtros comunes de los tres endpoints."""
    desde, _ = _fecha(args, 'from')
    hasta, solo_fecha = _fecha(args, 'to')
    if desde and hasta:
        if desde > hasta:
            raise ParametroInvalido('from')
        if hasta - desde > timedelta(days=RANGO_MAX_DIAS):
            raise ParametroInvalido('to')
    if hasta:
        hasta += timedelta(days=1) if solo_fecha else INSTANTE_MINIMO

    q = (args.get('q') or '').strip() or None
    if q and len(q) > LARGO_MAX_BUSQUEDA:
        raise ParametroInvalido('q')

    return Filtros(
        action=_enumerado(args, 'action', ACCIONES),
        result=_enumerado(args, 'result', RESULTADOS),
        area_id=_entero_positivo(args, 'area_id'),
        platform_id=_entero_positivo(args, 'platform_id'),
        user_id=_entero_positivo(args, 'user_id'),
        desde=desde, hasta=hasta, q=q)


def leer_paginacion(args):
    """`page` ≥ 1 (1 por defecto) y `per_page` 1–100 (25 por defecto)."""
    page = _entero_positivo(args, 'page') or PAGINA_POR_DEFECTO
    per_page = _entero_positivo(args, 'per_page') or POR_PAGINA_POR_DEFECTO
    if per_page > POR_PAGINA_MAX:
        raise ParametroInvalido('per_page')
    return Paginacion(page=page, per_page=per_page)


def leer_limite(args):
    """`limit` del cliente actual: como antes, un valor no numérico usa el
    por defecto; se acota a 1–`AUDIT_PAGE_SIZE_MAX`."""
    limite = args.get('limit', LIMITE_POR_DEFECTO, type=int)
    return max(1, min(limite, AUDIT_PAGE_SIZE_MAX))
