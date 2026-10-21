"""Encolado transaccional y aviso al worker por RQ (FNC-049, ADR-003).

- `encolar()` agrega el trabajo a la sesión **sin commit**: queda en la misma
  transacción que el cambio de negocio del llamador (patrón *outbox*). Si el
  llamador revierte, no hay trabajo.
- Tras el `commit` se despierta al worker con un mensaje RQ que lleva solo el
  id del trabajo. Si Redis no está o falla, el trabajo espera al barrido del
  worker (`PROVISIONING_POLL_INTERVAL_SECONDS`); nunca se revierte el commit.
- Idempotencia: una `clave_idempotencia` ya usada devuelve el trabajo
  existente y no crea otro. Dos transacciones simultáneas con la misma clave:
  la segunda falla por la restricción única y el llamador la revierte.
"""
import logging

import redis
from rq import Queue
from rq.serializers import JSONSerializer
from sqlalchemy import event

from app import db
from app.modules.audit.events import Evento
from app.modules.audit.services import add_audit_log
from app.modules.platforms.tipos import CAMPOS_DN
from app.modules.provisioning.configuracion import (
    ErrorConfiguracionAprovisionamiento, cargar_configuracion,
    configuracion_redis)
from app.modules.provisioning.models import ProvisioningJob
from app.modules.provisioning.reloj import ahora
from app.modules.provisioning.tipos import (ESTADO_CANCELADO,
                                            ESTADO_PENDIENTE,
                                            ESTADOS_EN_ESPERA,
                                            LARGO_CLAVE_IDEMPOTENCIA,
                                            OPERACION_OTORGAR,
                                            OPERACION_REVOCAR, OPERACIONES,
                                            PROVEEDORES)

logger = logging.getLogger(__name__)

# Función que ejecuta el worker (por nombre: el mensaje no lleva código).
FUNCION_TRABAJO = 'app.modules.provisioning.ejecucion.ejecutar_trabajo'
# Tiempo de espera de la conexión a Redis del worker (RQ lo sube para su
# espera bloqueada en la cola).
TIEMPO_ESPERA_REDIS_SEGUNDOS = 5
# Al despertar desde la app web (dentro de `after_commit` de la petición): con
# Redis caído, cada commit que encola tarda como mucho esto en conectar y otro
# tanto en enviar; luego el trabajo espera al barrido (revisor, FNC-049).
TIEMPO_ESPERA_REDIS_WEB_SEGUNDOS = 0.5
# Mensajes en JSON, nunca pickle: un mensaje no puede traer código
# (auditor-seguridad, FNC-049). El worker usa el mismo.
SERIALIZADOR_RQ = JSONSerializer
# RQ no guarda el resultado: el estado vive en la BD.
TTL_RESULTADO_RQ = 0
CLAVE_SESION = 'provisioning_por_despertar'


class DatosDeTrabajoInvalidos(ValueError):
    """Operación, nivel, plataforma o clave inválidos al encolar."""


# --------------------------------------------------------------------------- #
# Redis y RQ
# --------------------------------------------------------------------------- #

def conexion_redis(tiempo_espera=TIEMPO_ESPERA_REDIS_SEGUNDOS):
    """Conexión nueva a Redis (bytes, como pide RQ); exige `REDIS_PASS`.

    En el worker, RQ sube el `socket_timeout` por encima de su espera
    bloqueada en la cola.
    """
    cfg = configuracion_redis()
    return redis.Redis(host=cfg.host, port=cfg.puerto, password=cfg.contrasena,
                       socket_connect_timeout=tiempo_espera,
                       socket_timeout=tiempo_espera)


def cola(conexion=None, tiempo_espera=TIEMPO_ESPERA_REDIS_SEGUNDOS):
    """Cola RQ del ejecutor (`PROVISIONING_QUEUE_NAME`)."""
    cfg = cargar_configuracion()
    return Queue(cfg.cola, connection=conexion or conexion_redis(tiempo_espera),
                 default_timeout=cfg.tiempo_intento,
                 serializer=SERIALIZADOR_RQ)


def enviar(cola_rq, trabajo_id):
    """Mensaje RQ que despierta al worker para `trabajo_id`."""
    cfg = cargar_configuracion()
    return cola_rq.enqueue(FUNCION_TRABAJO, trabajo_id,
                           job_timeout=cfg.tiempo_intento,
                           result_ttl=TTL_RESULTADO_RQ)


def despertar(ids):
    """Avisa al worker; nunca lanza (sin Redis, espera al barrido)."""
    if not ids:
        return
    try:
        cola_rq = cola(tiempo_espera=TIEMPO_ESPERA_REDIS_WEB_SEGUNDOS)
        for trabajo_id in ids:
            enviar(cola_rq, trabajo_id)
    except ErrorConfiguracionAprovisionamiento as exc:
        logger.warning('Aprovisionamiento: sin aviso al worker (%s); '
                       'esperará al barrido.', exc)
    except Exception as exc:  # Redis caído: solo el tipo, sin detalle
        logger.warning('Aprovisionamiento: no se avisó al worker (%s); '
                       'esperará al barrido.', type(exc).__name__)


# --------------------------------------------------------------------------- #
# Aviso después del commit
# --------------------------------------------------------------------------- #

def _despues_del_commit(sesion):
    ids = sesion.info.pop(CLAVE_SESION, None)
    if ids:
        despertar(sorted(ids))


def _despues_del_rollback(sesion, transaccion_anterior):
    # Solo al revertir la transacción externa (no un SAVEPOINT).
    if transaccion_anterior.parent is None:
        sesion.info.pop(CLAVE_SESION, None)


def _instalar_eventos():
    for nombre, funcion in (('after_commit', _despues_del_commit),
                            ('after_soft_rollback', _despues_del_rollback)):
        if not event.contains(db.session, nombre, funcion):
            event.listen(db.session, nombre, funcion)


_instalar_eventos()


def despertar_tras_commit(trabajo_id):
    """Avisa al worker por `trabajo_id` cuando la transacción actual haga
    `commit` (nada si se revierte). Lo usan `encolar` y el reintento manual
    (FNC-062)."""
    db.session.info.setdefault(CLAVE_SESION, set()).add(trabajo_id)


# --------------------------------------------------------------------------- #
# Encolado
# --------------------------------------------------------------------------- #

def _validar_clave(clave):
    if not isinstance(clave, str) or not clave.strip():
        raise DatosDeTrabajoInvalidos('Falta la clave de idempotencia.')
    if len(clave) > LARGO_CLAVE_IDEMPOTENCIA:
        raise DatosDeTrabajoInvalidos(
            f'La clave de idempotencia supera {LARGO_CLAVE_IDEMPOTENCIA} '
            'caracteres.')
    return clave


MODULO_AUDITORIA = 'Aprovisionamiento'


def cancelar_otorgar_en_espera(usuario_id, plataforma, nivel, momento):
    """Una revocación deja sin efecto los otorgar en espera de su terna.

    Sin esto, el reintento de un otorgar fallido podría volver a meter a la
    persona después de revocarla (auditor-seguridad, FNC-049). Un otorgar ya
    en ejecución no se cancela: la revocación espera a que termine (orden por
    terna en `ejecucion.reservar`). Auditado en la misma transacción.
    """
    en_espera = ProvisioningJob.query.filter(
        ProvisioningJob.operation == OPERACION_OTORGAR,
        ProvisioningJob.user_id == usuario_id,
        ProvisioningJob.platform_id == plataforma.id,
        ProvisioningJob.level == nivel,
        ProvisioningJob.status.in_(ESTADOS_EN_ESPERA)).all()
    for trabajo in en_espera:
        trabajo.status = ESTADO_CANCELADO
        trabajo.finished_at = trabajo.updated_at = momento
        trabajo.next_attempt_at = None
        add_audit_log(
            Evento.EJECUCION_CANCELADA, status='info',
            detail=(f'Otorgar nivel {nivel} cancelado por una revocación '
                    f'(trabajo {trabajo.id}).'),
            module=MODULO_AUDITORIA, target_user_id=usuario_id,
            area_id=trabajo.area_id, platform_id=plataforma.id,
            grant_id=trabajo.access_id,
            after={'job_id': trabajo.id, 'status': ESTADO_CANCELADO},
            commit=False)
    return en_espera


def encolar(operacion, usuario_id, plataforma, nivel, clave_idempotencia,
            access_id=None):
    """Agrega un trabajo a la transacción actual y lo devuelve.

    - `plataforma`: `Platform`; su `integration_type` elige el proveedor y su
      área queda en el trabajo.
    - No hace `commit`: lo hace el llamador junto con su cambio.
    """
    clave = _validar_clave(clave_idempotencia)
    existente = ProvisioningJob.query.filter_by(idempotency_key=clave).first()
    if existente is not None:
        return existente
    if operacion not in OPERACIONES:
        raise DatosDeTrabajoInvalidos(f'Operación desconocida: {operacion}')
    if nivel not in CAMPOS_DN:
        raise DatosDeTrabajoInvalidos(f'Nivel desconocido: {nivel}')
    if plataforma is None or plataforma.integration_type not in PROVEEDORES:
        raise DatosDeTrabajoInvalidos('Plataforma sin tipo de integración.')
    if not usuario_id:
        raise DatosDeTrabajoInvalidos('Falta el usuario.')

    momento = ahora()
    if operacion == OPERACION_REVOCAR:
        cancelar_otorgar_en_espera(usuario_id, plataforma, nivel, momento)
    trabajo = ProvisioningJob(
        operation=operacion, provider=plataforma.integration_type,
        level=nivel, status=ESTADO_PENDIENTE, user_id=usuario_id,
        platform_id=plataforma.id, area_id=plataforma.area_id,
        access_id=access_id, idempotency_key=clave, attempts_count=0,
        max_attempts=cargar_configuracion().max_intentos,
        next_attempt_at=None, created_at=momento, updated_at=momento)
    db.session.add(trabajo)
    db.session.flush()
    despertar_tras_commit(trabajo.id)
    return trabajo
