"""Accesos otorgados (FNC-054, contrato `accesos.md`).

- Crea `platform_access_grants`: usuario, plataforma, nivel, origen,
  solicitud, quién otorgó y revocó, fechas, estado y último trabajo.
- Unicidad: un vigente por usuario, plataforma y nivel (`slot_vigente`) y un
  ocupante por usuario y plataforma (`slot_ocupante`, P5).
- `user_id`/`platform_id` sin `ON DELETE` (la BD impide borrar con accesos);
  `granted_by`/`revoked_by` con `SET NULL`.
- `downgrade()` borra la tabla (se pierde el inventario de accesos).

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0007'
down_revision: Union[str, Sequence[str], None] = '0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Valores fijos de esta revisión (no se importan del código, que puede cambiar).
TABLA = 'platform_access_grants'
AL_BORRAR_ACTOR = 'SET NULL'
LARGO_NIVEL = 10
LARGO_ORIGEN = 20
LARGO_ESTADO = 20
LARGO_MOTIVO = 500


def _fk(columna, tabla, ondelete=None):
    return sa.ForeignKey(f'{tabla}.id', name=f'fk_{TABLA}_{columna}',
                         ondelete=ondelete)


def upgrade() -> None:
    op.create_table(
        TABLA,
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), _fk('user_id', 'users'),
                  nullable=False),
        sa.Column('platform_id', sa.Integer(), _fk('platform_id', 'platforms'),
                  nullable=False),
        sa.Column('level', sa.String(LARGO_NIVEL), nullable=False),
        sa.Column('origin', sa.String(LARGO_ORIGEN), nullable=False),
        sa.Column('request_id', sa.Integer(), nullable=True),
        sa.Column('granted_by', sa.Integer(),
                  _fk('granted_by', 'users', AL_BORRAR_ACTOR), nullable=True),
        sa.Column('granted_at', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(LARGO_ESTADO), nullable=False),
        sa.Column('revoked_by', sa.Integer(),
                  _fk('revoked_by', 'users', AL_BORRAR_ACTOR), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('revoke_reason', sa.String(LARGO_MOTIVO), nullable=True),
        sa.Column('last_job_id', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('slot_vigente', sa.SmallInteger(), nullable=True),
        sa.Column('slot_ocupante', sa.SmallInteger(), nullable=True),
        sa.UniqueConstraint('user_id', 'platform_id', 'level', 'slot_vigente',
                            name='uq_platform_access_grants_vigente'),
        sa.UniqueConstraint('user_id', 'platform_id', 'slot_ocupante',
                            name='uq_platform_access_grants_ocupante'),
    )
    op.create_index('ix_platform_access_grants_platform_status', TABLA,
                    ['platform_id', 'status'])
    op.create_index('ix_platform_access_grants_user_status', TABLA,
                    ['user_id', 'status'])


def downgrade() -> None:
    op.drop_index('ix_platform_access_grants_user_status', table_name=TABLA)
    op.drop_index('ix_platform_access_grants_platform_status', table_name=TABLA)
    op.drop_table(TABLA)
