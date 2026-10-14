from app import db
from app.modules.audit.inmutabilidad import proteger
from datetime import datetime

# Al borrar un usuario, área o plataforma el registro se conserva (sin cascada,
# SEC-AUD-03); la referencia queda en NULL y el texto (`user`, `target`) se mantiene.
AL_BORRAR_REFERENCIA = 'SET NULL'


def _referencia(columna, tabla):
    return db.ForeignKey(f'{tabla}.id', name=f'fk_audit_logs_{columna}',
                         ondelete=AL_BORRAR_REFERENCIA)


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    __table_args__ = (
        db.Index('ix_audit_logs_timestamp', 'timestamp'),
        db.Index('ix_audit_logs_actor_id', 'actor_id'),
        db.Index('ix_audit_logs_target_user_id', 'target_user_id'),
        db.Index('ix_audit_logs_area_id', 'area_id'),
        db.Index('ix_audit_logs_platform_id', 'platform_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    user = db.Column(db.String(255), nullable=False)  # correo del actor o "sistema"
    action = db.Column(db.String(150), nullable=False)  # Evento del catálogo o texto heredado
    module = db.Column(db.String(50), nullable=True) # Usuarios, Áreas, Plataformas, etc.
    target = db.Column(db.String(255), nullable=True) # Nombre o correo del objeto afectado
    detail = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    status = db.Column(db.String(20), default='success') # success, error, warning, info

    # Ampliación FNC-047 (F-AUD-01, SEC-AUD-02).
    actor_id = db.Column(db.Integer, _referencia('actor_id', 'users'), nullable=True)  # NULL = sistema
    target_user_id = db.Column(db.Integer, _referencia('target_user_id', 'users'), nullable=True)
    area_id = db.Column(db.Integer, _referencia('area_id', 'areas'), nullable=True)
    platform_id = db.Column(db.Integer, _referencia('platform_id', 'platforms'), nullable=True)
    before_state = db.Column(db.JSON, nullable=True)
    after_state = db.Column(db.JSON, nullable=True)
    # Sin FK todavía: las tablas de solicitudes y accesos llegan con FNC-054/056.
    request_id = db.Column(db.Integer, nullable=True)
    grant_id = db.Column(db.Integer, nullable=True)

    actor = db.relationship('User', foreign_keys=[actor_id], viewonly=True)
    target_user = db.relationship('User', foreign_keys=[target_user_id],
                                  viewonly=True)
    area = db.relationship('Area', viewonly=True)
    platform = db.relationship('Platform', viewonly=True)

    def to_dict(self):
        return {
            "id": self.id,
            "time": self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "user": self.user,
            "action": self.action,
            "module": self.module,
            "target": self.target,
            "detail": self.detail,
            "ip": self.ip_address,
            "status": self.status,
            "actor": _usuario(self.actor),  # None = sistema (o actor borrado)
            "area": _con_nombre(self.area),
            "platform": _con_nombre(self.platform),
            "target_user": _usuario(self.target_user),
            "before": self.before_state,
            "after": self.after_state,
        }


def _usuario(usuario):
    return {"id": usuario.id, "email": usuario.email} if usuario else None


def _con_nombre(objeto):
    return {"id": objeto.id, "name": objeto.name} if objeto else None


proteger(AuditLog)
