"""Forma `Job` del contrato `conectores-y-ejecuciones.md` (FNC-062).

- Lista sin `attempts`; detalle con `attempts` en orden de número.
- `attempts[].error` se vuelve a pasar por `saneo.sanear_error` al salir
  (SEC-CON-10, defensa en profundidad): sin secretos, controles ni más de
  `LARGO_ERROR` caracteres aunque la fila tuviera texto crudo.
- Nunca se envían `idempotency_key`, `locked_by` (host y pid del worker) ni
  `locked_at`.
- Usuario, plataforma y área se resuelven en una consulta por tipo y página;
  si se borraron, van en `null`.
"""
from app.modules.access.serializacion import _fecha_utc
from app.modules.auth.models import User
from app.modules.core.models import Area, Platform
from app.modules.provisioning.saneo import sanear_error


def _por_id(modelo, ids, forma):
    ids = {i for i in ids if i}
    if not ids:
        return {}
    return {o.id: forma(o) for o in modelo.query.filter(modelo.id.in_(ids))}


def _referencias(trabajos):
    return (
        _por_id(User, (t.user_id for t in trabajos),
                lambda u: {'id': u.id, 'name': u.nombre or u.email}),
        _por_id(Platform, (t.platform_id for t in trabajos),
                lambda p: {'id': p.id, 'name': p.name}),
        _por_id(Area, (t.area_id for t in trabajos),
                lambda a: {'id': a.id, 'name': a.name}),
    )


def intento_publico(intento):
    return {'n': intento.number,
            'started_at': _fecha_utc(intento.started_at),
            'finished_at': _fecha_utc(intento.finished_at),
            'result': intento.result,
            'error': sanear_error(intento.error)}


def _trabajo(trabajo, usuarios, plataformas, areas):
    return {
        'id': trabajo.id,
        'status': trabajo.status,
        'operation': trabajo.operation,
        'provider': trabajo.provider,
        'access_id': trabajo.access_id,
        'user': usuarios.get(trabajo.user_id),
        'platform': plataformas.get(trabajo.platform_id),
        'area': areas.get(trabajo.area_id),
        'attempts_count': trabajo.attempts_count,
        'max_attempts': trabajo.max_attempts,
        'next_attempt_at': _fecha_utc(trabajo.next_attempt_at),
        'created_at': _fecha_utc(trabajo.created_at),
        'finished_at': _fecha_utc(trabajo.finished_at),
    }


def trabajos_publicos(trabajos):
    referencias = _referencias(trabajos)
    return [_trabajo(t, *referencias) for t in trabajos]


def trabajo_con_intentos(trabajo):
    datos, = trabajos_publicos([trabajo])
    datos['attempts'] = [intento_publico(i) for i in trabajo.attempts]
    return datos
