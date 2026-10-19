"""Estado de una plataforma que aportan otras tareas (puntos de extensión).

- `accesos_vigentes`: FNC-054 la implementa con los accesos otorgados
  (definición en `docs/contratos/accesos.md`). Mientras no existan, es 0, y
  la regla `409 plataforma_con_accesos` de FNC-046 no se dispara.
- `tiene_conector`: FNC-050 la implementa con la configuración del conector.

Quien la implemente cambia solo esta función: `to_dict` y las validaciones de
`api.py` ya la usan.
"""


def accesos_vigentes(plataforma):
    """Accesos vigentes de la plataforma (FNC-054)."""
    return 0


def tiene_conector(plataforma):
    """`True` si la plataforma tiene un conector configurado (FNC-050)."""
    return False
