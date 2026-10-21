"""`user_platforms` pasa a accesos `heredado` (FNC-065, contrato `accesos.md` 1.2).

- Cada fila de `user_platforms` se convierte en un acceso de `platform_access_grants`:
  origen `heredado`, nivel `usuario`, estado `activo`, sin otorgante, sin
  solicitud y sin trabajo encolado. No escribe en LDAP (decisión del
  orquestador, pendiente de validar en la prueba de concepto).
- Se omiten y se cuentan (reglas P1, P5, P6):
  - `acceso_vigente`: la cuenta ya tiene un acceso vigente en la plataforma;
  - `cuenta_inactiva`, `plataforma_inactiva`;
  - `superadmin`: tiene acceso por defecto y no recibe registros;
  - `fuera_del_area`: la cuenta no pertenece al área de la plataforma.
- Idempotente: no repite una pareja que ya tiene un acceso `heredado` (ni uno
  revocado después, que no se resucita).
- Auditoría: un solo registro de sistema `migracion_accesos_heredados` con los
  conteos (por fila sería ruido: no hay actor ni solicitud, y las filas
  quedan identificadas por el origen `heredado` en el inventario).
- `user_platforms` queda como tabla obsoleta y sin borrar (otra tarea).
- `downgrade()` borra los accesos `heredado` sin trabajo de aprovisionamiento
  (`last_job_id` nulo): los que ya se usaron o revocaron se conservan para no
  perder su rastro. `user_platforms` nunca se modificó, así que no hay nada
  que restaurar. El registro de auditoría no se borra (inmutable).

Revision ID: 0010
Revises: 0009
Create Date: 2026-10-21
"""
from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0010'
down_revision: Union[str, Sequence[str], None] = '0009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Valores fijos de esta revisión (no se importan del código, que puede cambiar).
ORIGEN = 'heredado'
NIVEL = 'usuario'
ESTADO_ACTIVO = 'activo'
ESTADO_REVOCADO = 'revocado'
ESTADO_ACTIVA = 'Activo'
ROL_SUPERADMIN = 'administrador'
OCUPA = 1
ACCION_AUDITORIA = 'migracion_accesos_heredados'
MODULO_AUDITORIA = 'Accesos'
ACTOR_SISTEMA = 'sistema'
IP_INTERNA = 'INTERNAL'

_metadata = sa.MetaData()
_asignaciones = sa.Table(
    'user_platforms', _metadata,
    sa.Column('user_id', sa.Integer), sa.Column('platform_id', sa.Integer))
_usuarios = sa.Table(
    'users', _metadata,
    sa.Column('id', sa.Integer), sa.Column('role', sa.String),
    sa.Column('is_active', sa.Boolean))
_plataformas = sa.Table(
    'platforms', _metadata,
    sa.Column('id', sa.Integer), sa.Column('area_id', sa.Integer),
    sa.Column('status', sa.String))
_areas_de_usuario = sa.Table(
    'user_areas', _metadata,
    sa.Column('user_id', sa.Integer), sa.Column('area_id', sa.Integer))
_accesos = sa.Table(
    'platform_access_grants', _metadata,
    sa.Column('id', sa.Integer), sa.Column('user_id', sa.Integer),
    sa.Column('platform_id', sa.Integer), sa.Column('level', sa.String),
    sa.Column('origin', sa.String), sa.Column('request_id', sa.Integer),
    sa.Column('granted_by', sa.Integer), sa.Column('granted_at', sa.DateTime),
    sa.Column('status', sa.String), sa.Column('last_job_id', sa.Integer),
    sa.Column('updated_at', sa.DateTime), sa.Column('slot_vigente', sa.SmallInteger),
    sa.Column('slot_ocupante', sa.SmallInteger))
_auditoria = sa.Table(
    'audit_logs', _metadata,
    sa.Column('timestamp', sa.DateTime), sa.Column('user', sa.String),
    sa.Column('action', sa.String), sa.Column('module', sa.String),
    sa.Column('detail', sa.Text), sa.Column('ip_address', sa.String),
    sa.Column('status', sa.String), sa.Column('after_state', sa.JSON))

# Estados vigentes de la revisión 0007: todo menos `revocado`.
_NO_VIGENTE = ESTADO_REVOCADO


def _motivo_de_omision(fila, vigentes, areas):
    """Razón por la que la fila no se migra, o `None` si se migra."""
    if (fila.user_id, fila.platform_id) in vigentes:
        return 'acceso_vigente'
    if fila.role == ROL_SUPERADMIN:
        return 'superadmin'
    if not fila.is_active:
        return 'cuenta_inactiva'
    if fila.status != ESTADO_ACTIVA:
        return 'plataforma_inactiva'
    if fila.area_id not in areas.get(fila.user_id, ()):
        return 'fuera_del_area'
    return None


def migrar_asignaciones(conexion) -> dict:
    """Convierte `user_platforms` en accesos `heredado`; devuelve los conteos.

    Se puede ejecutar varias veces: no repite lo ya migrado.
    """
    filas = conexion.execute(
        sa.select(_asignaciones.c.user_id, _asignaciones.c.platform_id,
                  _usuarios.c.role, _usuarios.c.is_active,
                  _plataformas.c.status, _plataformas.c.area_id)
        .select_from(_asignaciones
                     .join(_usuarios, _usuarios.c.id == _asignaciones.c.user_id)
                     .join(_plataformas,
                           _plataformas.c.id == _asignaciones.c.platform_id))
        .order_by(_asignaciones.c.user_id, _asignaciones.c.platform_id)).all()
    parejas = conexion.execute(
        sa.select(_accesos.c.user_id, _accesos.c.platform_id,
                  _accesos.c.origin, _accesos.c.status)).all()
    vigentes = {(p.user_id, p.platform_id) for p in parejas
                if p.status != _NO_VIGENTE}
    ya_migradas = {(p.user_id, p.platform_id) for p in parejas
                   if p.origin == ORIGEN}
    areas = {}
    for fila in conexion.execute(sa.select(_areas_de_usuario)).all():
        areas.setdefault(fila.user_id, set()).add(fila.area_id)

    omitidas = {}
    nuevos = []
    ahora = datetime.utcnow()
    for fila in filas:
        pareja = (fila.user_id, fila.platform_id)
        if pareja in ya_migradas:
            continue  # idempotencia: ni se cuenta ni se repite
        motivo = _motivo_de_omision(fila, vigentes, areas)
        if motivo:
            omitidas[motivo] = omitidas.get(motivo, 0) + 1
            continue
        nuevos.append({
            'user_id': fila.user_id, 'platform_id': fila.platform_id,
            'level': NIVEL, 'origin': ORIGEN, 'request_id': None,
            'granted_by': None, 'granted_at': ahora, 'status': ESTADO_ACTIVO,
            'last_job_id': None, 'updated_at': ahora,
            'slot_vigente': OCUPA, 'slot_ocupante': OCUPA})
    if nuevos:
        conexion.execute(sa.insert(_accesos), nuevos)
    return {'filas': len(filas), 'migradas': len(nuevos), 'omitidas': omitidas}


def _detalle(resultado) -> str:
    partes = [f'filas={resultado["filas"]}', f'migradas={resultado["migradas"]}']
    omitidas = resultado['omitidas']
    partes += [f'{motivo}={omitidas[motivo]}' for motivo in sorted(omitidas)]
    return ' '.join(partes)


def upgrade() -> None:
    conexion = op.get_bind()
    resultado = migrar_asignaciones(conexion)
    conexion.execute(sa.insert(_auditoria).values(
        timestamp=datetime.now(), user=ACTOR_SISTEMA, action=ACCION_AUDITORIA,
        module=MODULO_AUDITORIA, detail=_detalle(resultado),
        ip_address=IP_INTERNA, status='info', after_state=resultado))


def downgrade() -> None:
    op.get_bind().execute(sa.delete(_accesos).where(
        _accesos.c.origin == ORIGEN, _accesos.c.last_job_id.is_(None),
        _accesos.c.status == ESTADO_ACTIVO))
