"""Accesos otorgados: quién tiene qué plataforma, con qué nivel y por qué
(FNC-054, migración 0007, contrato `accesos.md`).

- Un registro por otorgamiento; nunca se borra (inventario F-AUD-02).
- Unicidad en la BD, también ante peticiones simultáneas:
  - `slot_vigente`: un acceso vigente por usuario, plataforma y nivel;
  - `slot_ocupante`: un acceso `en_proceso`/`activo`/`fallido` por usuario y
    plataforma (P5); el que sale (`revocando`) deja su lugar al nuevo nivel.
  Valen `OCUPA` o NULL y los mantiene `sincronizar_slots` al cambiar el estado.
- `user_id` y `platform_id` sin `ON DELETE`: la BD impide borrar una cuenta o
  plataforma con accesos (quedaría gente en los grupos sin rastro).
  Decisión del orquestador (pendiente de validar en la prueba de concepto).
- `request_id` sin FK hasta que exista la tabla de solicitudes (FNC-056);
  `last_job_id` sin FK para no crear un ciclo con `provisioning_jobs`.
- Fechas en UTC sin zona (`provisioning.reloj.ahora`).
"""
from app import db
from app.modules.access.tipos import (ESTADO_EN_PROCESO, ESTADOS_OCUPANTES,
                                      ESTADOS_VIGENTES, LARGO_ESTADO,
                                      LARGO_MOTIVO, LARGO_NIVEL, LARGO_ORIGEN,
                                      OCUPA)
from app.modules.provisioning.reloj import ahora

AL_BORRAR_ACTOR = 'SET NULL'


def _actor(columna):
    return db.ForeignKey('users.id', name=f'fk_platform_access_grants_{columna}',
                         ondelete=AL_BORRAR_ACTOR)


class PlatformAccessGrant(db.Model):
    __tablename__ = 'platform_access_grants'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'platform_id', 'level', 'slot_vigente',
                            name='uq_platform_access_grants_vigente'),
        db.UniqueConstraint('user_id', 'platform_id', 'slot_ocupante',
                            name='uq_platform_access_grants_ocupante'),
        db.Index('ix_platform_access_grants_platform_status', 'platform_id',
                 'status'),
        db.Index('ix_platform_access_grants_user_status', 'user_id', 'status'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.id',
                                      name='fk_platform_access_grants_user_id'),
                        nullable=False)
    platform_id = db.Column(
        db.Integer,
        db.ForeignKey('platforms.id',
                      name='fk_platform_access_grants_platform_id'),
        nullable=False)
    level = db.Column(db.String(LARGO_NIVEL), nullable=False)
    origin = db.Column(db.String(LARGO_ORIGEN), nullable=False)
    request_id = db.Column(db.Integer, nullable=True)
    granted_by = db.Column(db.Integer, _actor('granted_by'), nullable=True)
    granted_at = db.Column(db.DateTime, nullable=False, default=ahora)
    status = db.Column(db.String(LARGO_ESTADO), nullable=False,
                       default=ESTADO_EN_PROCESO)
    revoked_by = db.Column(db.Integer, _actor('revoked_by'), nullable=True)
    revoked_at = db.Column(db.DateTime, nullable=True)
    revoke_reason = db.Column(db.String(LARGO_MOTIVO), nullable=True)
    last_job_id = db.Column(db.Integer, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=ahora)
    slot_vigente = db.Column(db.SmallInteger, nullable=True)
    slot_ocupante = db.Column(db.SmallInteger, nullable=True)

    user = db.relationship('User', foreign_keys=[user_id], viewonly=True)
    platform = db.relationship('Platform', viewonly=True)

    def sincronizar_slots(self):
        """Ajusta las columnas de unicidad al estado actual."""
        self.slot_vigente = OCUPA if self.status in ESTADOS_VIGENTES else None
        self.slot_ocupante = OCUPA if self.status in ESTADOS_OCUPANTES else None
