"""Ejecución de un trabajo de aprovisionamiento (FNC-049).

Pasos de `ejecutar_trabajo(id)` (la función que corre el worker RQ):
1. **Reserva** atómica (`UPDATE … WHERE` estado en espera y vencido, o
   `en_ejecucion` con la reserva vencida): solo un worker la gana; los demás
   no hacen nada. Con la reserva se abre el intento y se hace `commit`.
2. Llamada al proveedor fuera de la transacción. Una excepción (incluido el
   tiempo de espera de RQ) cuenta como error transitorio y su texto no se
   guarda.
3. **Cierre** en una transacción: intento con resultado y error saneado
   (SEC-CON-10); trabajo `exitoso`, `fallido` (permanente o sin intentos) o
   `reintentando` con *backoff* y *jitter* (SEC-CON-08). Si es final, en la
   misma transacción: auditoría con actor `sistema` y manejadores de
   resultado (SEC-AUD-06, SEC-CON-09).
4. Después del `commit` y dentro de `try`: correo `aprovisionamiento_fallido`
   si falló (FNC-048, P10).
"""
import logging
import os
import socket
from datetime import timedelta

from rq.timeouts import JobTimeoutException
from sqlalchemy import and_, or_, update

from app import db
from app.modules.audit.events import Evento
from app.modules.audit.services import add_audit_log
from app.modules.auth.models import User
from app.modules.core.models import Platform
from app.modules.notifications.access_notifications import \
    notificar_aprovisionamiento_fallido
from app.modules.provisioning.configuracion import cargar_configuracion
from app.modules.provisioning.manejadores import avisar_resultado
from app.modules.provisioning.models import (ProvisioningJob,
                                             ProvisioningJobAttempt)
from app.modules.provisioning.providers import (Operacion, obtener_proveedor,
                                                permanente, transitorio)
from app.modules.provisioning.reintentos import segundos_de_espera
from app.modules.provisioning.reloj import ahora
from app.modules.provisioning.saneo import (MOTIVO_CONECTOR_NO_DISPONIBLE,
                                            MOTIVO_INESPERADO,
                                            MOTIVO_INTERRUMPIDO,
                                            MOTIVO_TIEMPO_AGOTADO,
                                            mensaje_de_error)
from app.modules.provisioning.tipos import (ESTADO_EN_EJECUCION,
                                            ESTADO_EXITOSO, ESTADO_FALLIDO,
                                            ESTADO_PENDIENTE,
                                            ESTADO_REINTENTANDO,
                                            ESTADOS_EN_ESPERA,
                                            ESTADOS_SIN_TERMINAR,
                                            LARGO_RESERVADO_POR,
                                            OPERACION_OTORGAR,
                                            OPERACION_REVOCAR,
                                            RESULTADO_ERROR_TRANSITORIO)

logger = logging.getLogger(__name__)

MODULO_AUDITORIA = 'Aprovisionamiento'
EVENTOS = {
    (OPERACION_OTORGAR, True): Evento.ACCESO_ACTIVO,
    (OPERACION_OTORGAR, False): Evento.ACCESO_FALLIDO,
    (OPERACION_REVOCAR, True): Evento.ACCESO_REVOCADO,
    (OPERACION_REVOCAR, False): Evento.REVOCACION_FALLIDA,
}
ESTADO_AUDITORIA = {True: 'success', False: 'error'}


def identificador_worker():
    """`<host>:<pid>` del proceso (nombre de host, nunca IP)."""
    return f'{socket.gethostname()}:{os.getpid()}'


# --------------------------------------------------------------------------- #
# 1. Reserva
# --------------------------------------------------------------------------- #

def sentencia_reserva(trabajo_id, worker, cfg, momento):
    """`UPDATE` que reserva el trabajo solo si está libre y le toca."""
    vencida = momento - timedelta(seconds=cfg.vencimiento_reserva)
    return (
        update(ProvisioningJob)
        .where(ProvisioningJob.id == trabajo_id,
               or_(and_(ProvisioningJob.status.in_(ESTADOS_EN_ESPERA),
                        or_(ProvisioningJob.next_attempt_at.is_(None),
                            ProvisioningJob.next_attempt_at <= momento)),
                   and_(ProvisioningJob.status == ESTADO_EN_EJECUCION,
                        ProvisioningJob.locked_at < vencida)))
        .values(status=ESTADO_EN_EJECUCION, locked_at=momento,
                locked_by=worker[:LARGO_RESERVADO_POR], updated_at=momento)
        .execution_options(synchronize_session=False))


def bloqueado_por_anterior(trabajo_id):
    """`True` si un trabajo anterior de la misma terna no terminó.

    Los trabajos de una terna (usuario, plataforma, nivel) corren en orden de
    creación (auditor-seguridad, FNC-049). Consulta previa y no subconsulta
    del `UPDATE` (MySQL no la permite sobre la misma tabla): sin carrera, un
    anterior solo puede pasar a terminado y los ids nuevos son mayores.
    """
    actual = (ProvisioningJob.query
              .with_entities(ProvisioningJob.user_id,
                             ProvisioningJob.platform_id,
                             ProvisioningJob.level)
              .filter(ProvisioningJob.id == trabajo_id).first())
    if actual is None:
        return True
    return db.session.query(
        ProvisioningJob.query.filter(
            ProvisioningJob.id < trabajo_id,
            ProvisioningJob.user_id == actual.user_id,
            ProvisioningJob.platform_id == actual.platform_id,
            ProvisioningJob.level == actual.level,
            ProvisioningJob.status.in_(ESTADOS_SIN_TERMINAR)).exists()
    ).scalar()


def reservar(trabajo_id, worker, cfg, momento=None):
    """Reserva el trabajo para `worker`; `True` si la ganó."""
    if bloqueado_por_anterior(trabajo_id):
        db.session.rollback()
        return False
    sentencia = sentencia_reserva(trabajo_id, worker, cfg, momento or ahora())
    ganada = db.session.execute(sentencia).rowcount == 1
    if not ganada:
        db.session.rollback()
    return ganada


def confirmar_reserva(trabajo_id, worker):
    """`True` si la reserva sigue siendo de `worker` (y la bloquea hasta el
    commit). Si otro worker la retomó al vencer, este no cierra nada
    (auditor-seguridad, FNC-049)."""
    sentencia = (
        update(ProvisioningJob)
        .where(ProvisioningJob.id == trabajo_id,
               ProvisioningJob.status == ESTADO_EN_EJECUCION,
               ProvisioningJob.locked_by == worker[:LARGO_RESERVADO_POR])
        .values(updated_at=ahora())
        .execution_options(synchronize_session=False))
    return db.session.execute(sentencia).rowcount == 1


def reabrir(trabajo, cfg):
    """Vuelve a `pendiente` un trabajo `fallido` (reintento manual, FNC-062).

    Decisión del orquestador (pendiente de validar en la prueba de concepto):
    se conserva la bitácora y se dan `PROVISIONING_MAX_ATTEMPTS` intentos más
    (`max_attempts` sube); no se reinicia el contador. Sin commit ni
    auditoría: los hace FNC-062 (`ejecucion_reintentada`).
    """
    if trabajo.status != ESTADO_FALLIDO:
        raise EstadoInvalido('Solo se reabre un trabajo fallido.')
    momento = ahora()
    trabajo.status = ESTADO_PENDIENTE
    trabajo.max_attempts = trabajo.attempts_count + cfg.max_intentos
    trabajo.next_attempt_at = trabajo.finished_at = None
    trabajo.locked_at = trabajo.locked_by = None
    trabajo.updated_at = momento
    return trabajo


class EstadoInvalido(ValueError):
    """El trabajo no está en el estado que pide la operación."""


def _cerrar_interrumpidos(trabajo, momento):
    """Intentos abiertos de una reserva vencida: transitorio interrumpido.

    Devuelve `True` si había alguno (la reserva se retomó).
    """
    retomada = False
    for intento in trabajo.attempts:
        if intento.finished_at is None:
            retomada = True
            intento.finished_at = momento
            intento.result = RESULTADO_ERROR_TRANSITORIO
            intento.error = mensaje_de_error(RESULTADO_ERROR_TRANSITORIO,
                                             MOTIVO_INTERRUMPIDO)
    return retomada


def _abrir_intento(trabajo, momento):
    trabajo.attempts_count += 1
    intento = ProvisioningJobAttempt(job=trabajo,
                                     number=trabajo.attempts_count,
                                     started_at=momento)
    db.session.add(intento)
    return intento


# --------------------------------------------------------------------------- #
# 2. Proveedor
# --------------------------------------------------------------------------- #

def _operacion(trabajo):
    return Operacion(id_operacion=str(trabajo.id),
                     clave_idempotencia=trabajo.idempotency_key,
                     operacion=trabajo.operation, nivel=trabajo.level,
                     plataforma_id=trabajo.platform_id,
                     usuario_id=trabajo.user_id, acceso_id=trabajo.access_id)


def llamar_proveedor(trabajo):
    """Resultado del proveedor; nunca lanza ni deja pasar texto de excepción."""
    proveedor = obtener_proveedor(trabajo.provider)
    if proveedor is None:
        return permanente(MOTIVO_CONECTOR_NO_DISPONIBLE)
    metodo = (proveedor.otorgar if trabajo.operation == OPERACION_OTORGAR
              else proveedor.revocar)
    try:
        return metodo(_operacion(trabajo))
    except JobTimeoutException:
        logger.error('Aprovisionamiento: trabajo %s sin respuesta en el '
                     'tiempo de espera.', trabajo.id)
        return transitorio(MOTIVO_TIEMPO_AGOTADO)
    except Exception as exc:  # solo el tipo: el texto puede traer secretos
        logger.error('Aprovisionamiento: error inesperado del proveedor en el '
                     'trabajo %s (%s).', trabajo.id, type(exc).__name__)
        return transitorio(MOTIVO_INESPERADO)


# --------------------------------------------------------------------------- #
# 3. Cierre
# --------------------------------------------------------------------------- #

def _auditar(trabajo, exito):
    usuario = db.session.get(User, trabajo.user_id) if trabajo.user_id else None
    add_audit_log(
        EVENTOS[(trabajo.operation, exito)], status=ESTADO_AUDITORIA[exito],
        detail=(f'{trabajo.operation.capitalize()} nivel {trabajo.level}: '
                f'{trabajo.status} tras {trabajo.attempts_count} intento(s) '
                f'(trabajo {trabajo.id}).'),
        module=MODULO_AUDITORIA, target=usuario.email if usuario else None,
        target_user_id=trabajo.user_id, area_id=trabajo.area_id,
        platform_id=trabajo.platform_id, grant_id=trabajo.access_id,
        after={'job_id': trabajo.id, 'status': trabajo.status,
               'provider': trabajo.provider,
               'attempts': trabajo.attempts_count},
        as_system=True, commit=False)


def _finalizar(trabajo, exito, momento):
    trabajo.status = ESTADO_EXITOSO if exito else ESTADO_FALLIDO
    trabajo.finished_at = momento
    trabajo.next_attempt_at = None
    _auditar(trabajo, exito)
    avisar_resultado(trabajo, exito)


def cerrar_intento(trabajo, intento, resultado, cfg, momento=None,
                   aleatorio=None):
    """Aplica `resultado` al intento y al trabajo (sin commit)."""
    momento = momento or ahora()
    intento.finished_at = momento
    intento.result = resultado.resultado
    intento.error = (None if resultado.exito else
                     mensaje_de_error(resultado.resultado, resultado.motivo,
                                      resultado.detalle))
    trabajo.locked_at = None
    trabajo.locked_by = None
    trabajo.updated_at = momento
    if resultado.exito:
        _finalizar(trabajo, True, momento)
    elif (not resultado.reintentable
          or trabajo.attempts_count >= trabajo.max_attempts):
        _finalizar(trabajo, False, momento)
    else:
        opciones = {'aleatorio': aleatorio} if aleatorio else {}
        espera = segundos_de_espera(trabajo.attempts_count, cfg.backoff_base,
                                    cfg.backoff_max, **opciones)
        trabajo.status = ESTADO_REINTENTANDO
        trabajo.next_attempt_at = momento + timedelta(seconds=espera)


# --------------------------------------------------------------------------- #
# 4. Aviso de fallo
# --------------------------------------------------------------------------- #

def avisar_fallo(trabajo_id):
    """Correo `aprovisionamiento_fallido`; nunca lanza (FNC-048)."""
    try:
        trabajo = db.session.get(ProvisioningJob, trabajo_id)
        usuario = db.session.get(User, trabajo.user_id) if trabajo.user_id else None
        plataforma = (db.session.get(Platform, trabajo.platform_id)
                      if trabajo.platform_id else None)
        notificar_aprovisionamiento_fallido(usuario, plataforma, trabajo.level,
                                            trabajo.operation)
    except Exception as exc:
        logger.error('Aprovisionamiento: no se pudo avisar el fallo del '
                     'trabajo %s (%s).', trabajo_id, type(exc).__name__)
        db.session.rollback()


# --------------------------------------------------------------------------- #
# Punto de entrada del worker
# --------------------------------------------------------------------------- #

def ejecutar_trabajo(trabajo_id, worker=None):
    """Ejecuta un intento del trabajo si lo puede reservar.

    Devuelve el estado en que quedó, o `None` si otro worker lo tiene, ya
    terminó o aún no le toca.
    """
    cfg = cargar_configuracion()
    worker = worker or identificador_worker()
    try:
        if not reservar(trabajo_id, worker, cfg):
            return None
        momento = ahora()
        trabajo = db.session.get(ProvisioningJob, trabajo_id,
                                 populate_existing=True)
        retomada = _cerrar_interrumpidos(trabajo, momento)
        if retomada and trabajo.attempts_count >= trabajo.max_attempts:
            # Reserva vencida en el último intento: no queda otro.
            trabajo.locked_at = trabajo.locked_by = None
            trabajo.updated_at = momento
            _finalizar(trabajo, False, momento)
            db.session.commit()
            avisar_fallo(trabajo_id)
            return ESTADO_FALLIDO
        intento = _abrir_intento(trabajo, momento)
        db.session.commit()

        resultado = llamar_proveedor(trabajo)

        if not confirmar_reserva(trabajo_id, worker):
            db.session.rollback()
            logger.warning('Aprovisionamiento: la reserva del trabajo %s ya '
                           'no es de este worker; no se cierra.', trabajo_id)
            return None
        cerrar_intento(trabajo, intento, resultado, cfg)
        estado = trabajo.status
        db.session.commit()
    except Exception as exc:
        # BD caída o manejador con error: se revierte; la reserva vence y el
        # trabajo se retoma (las operaciones son idempotentes).
        db.session.rollback()
        logger.error('Aprovisionamiento: no se cerró el trabajo %s (%s); se '
                     'retomará al vencer la reserva.', trabajo_id,
                     type(exc).__name__)
        return None
    logger.info('Aprovisionamiento: trabajo %s → %s', trabajo_id, estado)
    if estado == ESTADO_FALLIDO:
        avisar_fallo(trabajo_id)
    return estado
