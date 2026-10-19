"""Worker de aprovisionamiento: barrido de la BD + worker RQ (FNC-049).

- La BD es la cola (*outbox*); Redis solo despierta. Cada vuelta:
  1. **barrido**: los trabajos en espera vencidos (`next_attempt_at`) y las
     reservas vencidas se envían a la cola RQ (así se cubren los reintentos
     con *backoff* y los avisos perdidos si Redis no estuvo);
  2. worker RQ hasta quedar ocioso `PROVISIONING_POLL_INTERVAL_SECONDS`.
- `SimpleWorker` (sin *fork*): el trabajo corre en este proceso, con el
  contexto de la app y su conexión a la BD. El tiempo de espera por intento lo
  aplica RQ (`job_timeout`).
- Mensajes repetidos son inocuos: la reserva atómica deja ejecutar uno.
- Apagado ordenado: `SIGTERM`/`SIGINT` terminan el intento en curso y salen;
  una segunda señal corta en frío (comportamiento de RQ).
"""
import logging
import signal
import threading
from datetime import timedelta

from rq import SimpleWorker
from rq.worker import WorkerStatus
from sqlalchemy import and_, or_

from app import db
from app.modules.provisioning.models import ProvisioningJob
from app.modules.provisioning.queue import (FUNCION_TRABAJO,
                                            SERIALIZADOR_RQ, enviar)
from app.modules.provisioning.reloj import ahora
from app.modules.provisioning.tipos import (ESTADO_EN_EJECUCION,
                                            ESTADOS_EN_ESPERA)

logger = logging.getLogger(__name__)

# Trabajos enviados a la cola por barrido.
LOTE_BARRIDO = 100
SENALES_APAGADO = (signal.SIGTERM, signal.SIGINT)


class ControlApagado:
    """Bandera de apagado compartida entre el bucle y el worker RQ."""

    def __init__(self):
        self._evento = threading.Event()

    @property
    def detener(self):
        return self._evento.is_set()

    def pedir(self, *_):
        self._evento.set()

    def esperar(self, segundos):
        self._evento.wait(segundos)


def mensaje_valido(job):
    """`True` solo si el mensaje pide `ejecutar_trabajo(<id entero>)`."""
    try:
        args, kwargs = tuple(job.args or ()), job.kwargs or {}
        return (job.func_name == FUNCION_TRABAJO and not kwargs
                and len(args) == 1 and type(args[0]) is int)
    except Exception:  # datos ilegibles o con otra forma
        return False


class WorkerAprovisionamiento(SimpleWorker):
    """Worker RQ que también avisa el apagado al bucle del barrido.

    Rechaza sin ejecutar todo mensaje que no sea `ejecutar_trabajo(<int>)`
    (Redis no es de confianza: auditor-seguridad, FNC-049).
    """

    def execute_job(self, job, queue):
        if mensaje_valido(job):
            return super().execute_job(job, queue)
        logger.warning('Aprovisionamiento: mensaje RQ rechazado sin ejecutar '
                       '(id %s).', getattr(job, 'id', '?'))
        try:
            job.delete()
        except Exception as exc:
            logger.warning('Aprovisionamiento: no se borró el mensaje '
                           'rechazado (%s).', type(exc).__name__)
        try:
            self.set_state(WorkerStatus.IDLE)
        except Exception:
            pass
        return None

    def __init__(self, *args, control=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.control = control or ControlApagado()

    def request_stop(self, signum, frame):
        self.control.pedir()
        super().request_stop(signum, frame)


def vencidos(cfg, momento=None, limite=LOTE_BARRIDO):
    """Ids de trabajos en espera vencidos o con la reserva vencida."""
    momento = momento or ahora()
    vencida = momento - timedelta(seconds=cfg.vencimiento_reserva)
    consulta = (ProvisioningJob.query
                .with_entities(ProvisioningJob.id)
                .filter(or_(
                    and_(ProvisioningJob.status.in_(ESTADOS_EN_ESPERA),
                         or_(ProvisioningJob.next_attempt_at.is_(None),
                             ProvisioningJob.next_attempt_at <= momento)),
                    and_(ProvisioningJob.status == ESTADO_EN_EJECUCION,
                         ProvisioningJob.locked_at < vencida)))
                .order_by(ProvisioningJob.next_attempt_at,
                          ProvisioningJob.id)
                .limit(limite))
    return [fila.id for fila in consulta]


def barrer(cola_rq, cfg, momento=None):
    """Envía a la cola los trabajos vencidos; devuelve cuántos."""
    ids = vencidos(cfg, momento)
    db.session.rollback()  # no dejar la transacción de lectura abierta
    for trabajo_id in ids:
        enviar(cola_rq, trabajo_id)
    return len(ids)


def instalar_senales(control):
    for senal in SENALES_APAGADO:
        signal.signal(senal, control.pedir)


def ejecutar(cola_rq, cfg, control=None, clase_worker=WorkerAprovisionamiento):
    """Bucle del worker hasta que llegue una señal de apagado."""
    control = control or ControlApagado()
    logger.info('Aprovisionamiento: worker en la cola %s.', cfg.cola)
    while not control.detener:
        # RQ deja sus manejadores al salir de `work()`: se reponen los propios.
        instalar_senales(control)
        try:
            enviados = barrer(cola_rq, cfg)
            if enviados:
                logger.info('Aprovisionamiento: %d trabajo(s) del barrido.',
                            enviados)
            if control.detener:
                break
            worker = clase_worker([cola_rq], connection=cola_rq.connection,
                                  serializer=SERIALIZADOR_RQ, control=control)
            worker.work(max_idle_time=cfg.intervalo_barrido,
                        with_scheduler=False)
        except Exception as exc:  # Redis o BD caídos: esperar y reintentar
            logger.error('Aprovisionamiento: fallo del worker (%s); se '
                         'reintenta en %d s.', type(exc).__name__,
                         cfg.intervalo_barrido)
            control.esperar(cfg.intervalo_barrido)
    logger.info('Aprovisionamiento: worker detenido.')
