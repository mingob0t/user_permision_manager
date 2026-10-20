"""Estado de una plataforma que aportan otras tareas (puntos de extensión).

- `accesos_vigentes`: accesos otorgados vigentes (FNC-054; definición en
  `docs/contratos/accesos.md`). Con más de 0, `409 plataforma_con_accesos`
  (FNC-046).
- `tiene_conector`: FNC-050 la implementa con la configuración del conector.

Quien la implemente cambia solo esta función: `to_dict` y las validaciones de
`api.py` ya la usan.
"""


def accesos_vigentes(plataforma):
    """Accesos vigentes de la plataforma (FNC-054)."""
    # Import diferido: `core.models` importa este módulo al cargarse.
    from app.modules.access.consultas import contar_vigentes_de_plataforma
    return contar_vigentes_de_plataforma(getattr(plataforma, 'id', None))


def tiene_conector(plataforma):
    """`True` si la plataforma tiene un conector configurado (FNC-050)."""
    return False
