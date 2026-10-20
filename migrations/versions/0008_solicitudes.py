"""Solicitudes de acceso (FNC-056, contrato `solicitudes.md`).

- Crea `platform_access_requests`: solicitante, plataforma, nivel,
  justificación, estado, nivel vigente al solicitar y decisión.
- Unicidad: una pendiente por usuario y plataforma (`slot_pendiente`).
- `user_id`/`platform_id` sin `ON DELETE` (la BD impide borrar con
  solicitudes); `decided_by` con `SET NULL`.
- `downgrade()` borra la tabla (se pierde el historial de solicitudes).

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0008'
down_revision: Union[str, Sequence[str], None] = '0007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Valores fijos de esta revisión (no se importan del código, que puede cambiar).
TABLA = 'platform_access_requests'
AL_BORRAR_DECISOR = 'SET NULL'
LARGO_NIVEL = 10
LARGO_ESTADO = 20
LARGO_TEXTO = 500


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
        sa.Column('justification', sa.String(LARGO_TEXTO), nullable=True),
        sa.Column('status', sa.String(LARGO_ESTADO), nullable=False),
        sa.Column('current_level', sa.String(LARGO_NIVEL), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('decided_by', sa.Integer(),
                  _fk('decided_by', 'users', AL_BORRAR_DECISOR),
                  nullable=True),
        sa.Column('decided_at', sa.DateTime(), nullable=True),
        sa.Column('rejection_reason', sa.String(LARGO_TEXTO), nullable=True),
        sa.Column('slot_pendiente', sa.SmallInteger(), nullable=True),
        sa.UniqueConstraint('user_id', 'platform_id', 'slot_pendiente',
                            name='uq_platform_access_requests_pendiente'),
    )
    op.create_index('ix_platform_access_requests_user_status', TABLA,
                    ['user_id', 'status'])
    op.create_index('ix_platform_access_requests_platform_status', TABLA,
                    ['platform_id', 'status'])


def downgrade() -> None:
    op.drop_index('ix_platform_access_requests_platform_status',
                  table_name=TABLA)
    op.drop_index('ix_platform_access_requests_user_status', table_name=TABLA)
    op.drop_table(TABLA)
