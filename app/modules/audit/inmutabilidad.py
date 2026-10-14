"""Inmutabilidad del registro de auditoría desde la aplicación (SEC-AUD-03).

- Un `UPDATE` o `DELETE` por el ORM (objeto o masivo) lanza `RegistroInmutable`.
- SQL crudo no se intercepta: lo cubren los permisos de BD de solo
  INSERT/SELECT para el usuario de la app (pendiente de aprobación del dueño).
- Las acciones de FK de la BD (`ON DELETE SET NULL`) no pasan por el ORM.
"""

from sqlalchemy import event
from sqlalchemy.orm import Session


class RegistroInmutable(RuntimeError):
    """Se intentó modificar o borrar un registro de auditoría."""


MENSAJE = 'El registro de auditoría no se modifica ni se borra.'


def _rechazar(*_args, **_kwargs):
    raise RegistroInmutable(MENSAJE)


def _afecta_tabla(estado, tabla):
    if any(m.local_table is tabla for m in estado.all_mappers):
        return True
    return getattr(estado.statement, 'table', None) is tabla


def proteger(modelo):
    """Registra los rechazos de `UPDATE`/`DELETE` para `modelo`."""
    event.listen(modelo, 'before_update', _rechazar)
    event.listen(modelo, 'before_delete', _rechazar)

    tabla = modelo.__table__

    @event.listens_for(Session, 'do_orm_execute')
    def _rechazar_masivo(estado):
        if (estado.is_update or estado.is_delete) and _afecta_tabla(estado, tabla):
            _rechazar()
