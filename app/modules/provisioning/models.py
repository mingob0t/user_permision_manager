"""Trabajos de aprovisionamiento y sus intentos (FNC-049, migración 0006).

- `provisioning_jobs`: un trabajo por operación (otorgar o revocar) con su
  estado, intentos, próximo intento, reserva del worker y clave de
  idempotencia única. Es la cola persistente (*outbox*): Redis solo despierta
  al worker (ADR-003).
- `provisioning_job_attempts`: bitácora de cada intento; el error se guarda
  saneado y truncado (SEC-CON-10).
- Las fechas son UTC sin zona (`reloj.ahora`).
- Al borrar un usuario, área o plataforma el trabajo se conserva con la
  referencia en NULL (historial). `access_id` aún no tiene FK: la tabla de
  accesos llega con FNC-054.
"""
from app import db
from app.modules.provisioning.reloj import ahora
from app.modules.provisioning.tipos import (ESTADO_PENDIENTE, LARGO_CLAVE_IDEMPOTENCIA,
                                            LARGO_ERROR, LARGO_ESTADO,
                                            LARGO_NIVEL, LARGO_OPERACION,
                                            LARGO_PROVEEDOR,
                                            LARGO_RESERVADO_POR,
                                            LARGO_RESULTADO)

AL_BORRAR_REFERENCIA = 'SET NULL'
AL_BORRAR_TRABAJO = 'CASCADE'


def _referencia(columna, tabla):
    return db.ForeignKey(f'{tabla}.id', name=f'fk_provisioning_jobs_{columna}',
                         ondelete=AL_BORRAR_REFERENCIA)


class ProvisioningJob(db.Model):
    __tablename__ = 'provisioning_jobs'
    __table_args__ = (
        db.UniqueConstraint('idempotency_key',
                            name='uq_provisioning_jobs_idempotency_key'),
        db.Index('ix_provisioning_jobs_status_next', 'status',
                 'next_attempt_at'),
        db.Index('ix_provisioning_jobs_access_id', 'access_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    operation = db.Column(db.String(LARGO_OPERACION), nullable=False)
    provider = db.Column(db.String(LARGO_PROVEEDOR), nullable=False)
    level = db.Column(db.String(LARGO_NIVEL), nullable=False)
    status = db.Column(db.String(LARGO_ESTADO), nullable=False,
                       default=ESTADO_PENDIENTE)
    user_id = db.Column(db.Integer, _referencia('user_id', 'users'),
                        nullable=True)
    platform_id = db.Column(db.Integer, _referencia('platform_id', 'platforms'),
                            nullable=True)
    area_id = db.Column(db.Integer, _referencia('area_id', 'areas'),
                        nullable=True)
    access_id = db.Column(db.Integer, nullable=True)
    idempotency_key = db.Column(db.String(LARGO_CLAVE_IDEMPOTENCIA),
                                nullable=False)
    attempts_count = db.Column(db.Integer, nullable=False, default=0)
    max_attempts = db.Column(db.Integer, nullable=False)
    next_attempt_at = db.Column(db.DateTime, nullable=True)
    locked_at = db.Column(db.DateTime, nullable=True)
    locked_by = db.Column(db.String(LARGO_RESERVADO_POR), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=ahora)
    updated_at = db.Column(db.DateTime, nullable=False, default=ahora)
    finished_at = db.Column(db.DateTime, nullable=True)

    attempts = db.relationship(
        'ProvisioningJobAttempt', back_populates='job',
        order_by='ProvisioningJobAttempt.number',
        cascade='all, delete-orphan', passive_deletes=True)


class ProvisioningJobAttempt(db.Model):
    __tablename__ = 'provisioning_job_attempts'
    __table_args__ = (
        db.UniqueConstraint('job_id', 'number',
                            name='uq_provisioning_job_attempts_job_number'),
    )

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer,
                       db.ForeignKey('provisioning_jobs.id',
                                     name='fk_provisioning_job_attempts_job_id',
                                     ondelete=AL_BORRAR_TRABAJO),
                       nullable=False)
    number = db.Column(db.Integer, nullable=False)
    started_at = db.Column(db.DateTime, nullable=False, default=ahora)
    finished_at = db.Column(db.DateTime, nullable=True)
    result = db.Column(db.String(LARGO_RESULTADO), nullable=True)
    error = db.Column(db.String(LARGO_ERROR), nullable=True)

    job = db.relationship('ProvisioningJob', back_populates='attempts')
