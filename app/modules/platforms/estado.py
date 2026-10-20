"""Estado de una plataforma que aportan otras tareas (puntos de extensión).

- `accesos_vigentes`: accesos otorgados vigentes (FNC-054; definición en
  `docs/contratos/accesos.md`). Con más de 0, `409 plataforma_con_accesos`
  (FNC-046).
- `accesos_que_impiden_mover`: los mismos sin los automáticos de los admins
  (`admin_de_area`), que se resincronizan al cambiar el área (FNC-055).
- `tiene_conector`: configuración activa del conector de un tipo registrado
  (FNC-050, `connectors.consultas.conector_disponible`).

Quien la implemente cambia solo esta función: `to_dict` y las validaciones de
`api.py` ya la usan.
"""


def accesos_vigentes(plataforma):
    """Accesos vigentes de la plataforma (FNC-054)."""
    # Import diferido: `core.models` importa este módulo al cargarse.
    from app.modules.access.consultas import contar_vigentes_de_plataforma
    return contar_vigentes_de_plataforma(getattr(plataforma, 'id', None))


def accesos_que_impiden_mover(plataforma):
    """Vigentes que impiden cambiar el área: todos menos `admin_de_area`."""
    from app.modules.access.consultas import contar_vigentes_no_automaticos
    return contar_vigentes_no_automaticos(getattr(plataforma, 'id', None))


def tiene_conector(plataforma):
    """`True` si la plataforma `conector` tiene una configuración activa de un
    tipo registrado (FNC-050)."""
    from app.modules.connectors.consultas import conector_disponible
    return conector_disponible(plataforma)
