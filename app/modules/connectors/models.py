"""Configuración del conector de cada plataforma (FNC-050, migración 0009).

- `platform_connectors`: una por plataforma `conector`. Tipo, host por nombre
  (lista blanca, SEC-CON-07), puerto, parámetros no sensibles validados por el
  esquema del tipo y la **referencia** al ítem del gestor de secretos
  (ADR-005). Ninguna columna guarda el valor de una credencial (SEC-CON-02).
- Cambiar `host` o `credential_ref` deja `credential_status` en
  `sin_verificar` (SEC-CON-07).
- Al borrar la plataforma se borra su configuración (`ON DELETE CASCADE`).
- Fechas UTC sin zona (`provisioning.reloj.ahora`).
"""
from sqlalchemy.orm import validates

from app import db
from app.modules.connectors.tipos import (CREDENCIAL_SIN_VERIFICAR,
                                          LARGO_ESTADO_CREDENCIAL, LARGO_HOST,
                                          LARGO_REFERENCIA, LARGO_TIPO)
from app.modules.provisioning.reloj import ahora

AL_BORRAR_PLATAFORMA = 'CASCADE'
FORMATO_FECHA = '%Y-%m-%dT%H:%M:%SZ'
# Cambiarlos invalida la verificación de la credencial.
CAMPOS_QUE_INVALIDAN = ('host', 'credential_ref')


class PlatformConnector(db.Model):
    __tablename__ = 'platform_connectors'
    __table_args__ = (
        db.UniqueConstraint('platform_id',
                            name='uq_platform_connectors_platform_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    platform_id = db.Column(
        db.Integer,
        db.ForeignKey('platforms.id', name='fk_platform_connectors_platform_id',
                      ondelete=AL_BORRAR_PLATAFORMA),
        nullable=False)
    type = db.Column(db.String(LARGO_TIPO), nullable=False)
    host = db.Column(db.String(LARGO_HOST), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    params = db.Column(db.JSON, nullable=False, default=dict)
    credential_ref = db.Column(db.String(LARGO_REFERENCIA), nullable=False)
    credential_status = db.Column(db.String(LARGO_ESTADO_CREDENCIAL),
                                  nullable=False,
                                  default=CREDENCIAL_SIN_VERIFICAR)
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=ahora)
    updated_at = db.Column(db.DateTime, nullable=False, default=ahora,
                           onupdate=ahora)

    @validates(*CAMPOS_QUE_INVALIDAN)
    def _invalidar_verificacion(self, campo, valor):
        if getattr(self, campo) is not None and getattr(self, campo) != valor:
            self.credential_status = CREDENCIAL_SIN_VERIFICAR
        return valor

    def to_dict(self):
        """Forma `Connector` del contrato; nunca el valor de la credencial."""
        return {
            'platform_id': self.platform_id,
            'type': self.type,
            'host': self.host,
            'port': self.port,
            'params': dict(self.params or {}),
            'credential_ref': self.credential_ref,
            'credential_status': self.credential_status,
            'active': self.active,
            'updated_at': (self.updated_at.strftime(FORMATO_FECHA)
                           if self.updated_at else None),
        }
