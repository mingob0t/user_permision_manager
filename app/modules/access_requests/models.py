"""Solicitud de acceso a una plataforma (FNC-056, migración 0008).

- Tabla `platform_access_requests` (nunca `access_requests`, FNC-039).
- Una solicitud pendiente por usuario y plataforma, también ante peticiones
  simultáneas: restricción única `(user_id, platform_id, slot_pendiente)`.
  `slot_pendiente` vale `PENDIENTE` o NULL y lo mantiene
  `sincronizar_slot`.
- `user_id` y `platform_id` sin `ON DELETE`, como `platform_access_grants`:
  la BD impide borrar una cuenta o plataforma con historial de solicitudes.
  Decisión del orquestador (pendiente de validar en la prueba de concepto).
- Fechas en UTC sin zona (`provisioning.reloj.ahora`).
"""
from app import db
from app.modules.access_requests.tipos import (ESTADO_PENDIENTE, LARGO_ESTADO,
                                               LARGO_NIVEL, LARGO_TEXTO,
                                               PENDIENTE)
from app.modules.provisioning.reloj import ahora

TABLA = 'platform_access_requests'
AL_BORRAR_DECISOR = 'SET NULL'


class PlatformAccessRequest(db.Model):
    __tablename__ = TABLA
    __table_args__ = (
        db.UniqueConstraint('user_id', 'platform_id', 'slot_pendiente',
                            name='uq_platform_access_requests_pendiente'),
        db.Index('ix_platform_access_requests_user_status', 'user_id',
                 'status'),
        db.Index('ix_platform_access_requests_platform_status', 'platform_id',
                 'status'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', name='fk_platform_access_requests_user_id'),
        nullable=False)
    platform_id = db.Column(
        db.Integer,
        db.ForeignKey('platforms.id',
                      name='fk_platform_access_requests_platform_id'),
        nullable=False)
    level = db.Column(db.String(LARGO_NIVEL), nullable=False)
    justification = db.Column(db.String(LARGO_TEXTO), nullable=True)
    status = db.Column(db.String(LARGO_ESTADO), nullable=False,
                       default=ESTADO_PENDIENTE)
    current_level = db.Column(db.String(LARGO_NIVEL), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=ahora)
    decided_by = db.Column(
        db.Integer,
        db.ForeignKey('users.id', name='fk_platform_access_requests_decided_by',
                      ondelete=AL_BORRAR_DECISOR),
        nullable=True)
    decided_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.String(LARGO_TEXTO), nullable=True)
    slot_pendiente = db.Column(db.SmallInteger, nullable=True)

    requester = db.relationship('User', foreign_keys=[user_id], viewonly=True)
    decider = db.relationship('User', foreign_keys=[decided_by], viewonly=True)
    platform = db.relationship('Platform', viewonly=True)

    def sincronizar_slot(self):
        """Ajusta la columna de unicidad al estado actual."""
        self.slot_pendiente = (PENDIENTE if self.status == ESTADO_PENDIENTE
                               else None)
