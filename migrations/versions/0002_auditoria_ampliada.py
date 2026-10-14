"""Auditoría ampliada e inmutable (FNC-047, SEG-25).

- `user`, `action` y `target` más largos (un correo largo hacía fallar el INSERT).
- Columnas nuevas: actor, usuario afectado, área y plataforma (FK con
  `ON DELETE SET NULL`, sin cascada), antes/después (JSON) y solicitud/acceso.
- Índices por fecha, actor, usuario afectado, área y plataforma.
- `downgrade()` quita lo nuevo y regresa los largos anteriores: en MySQL estricto
  falla si ya hay valores más largos (se respalda y recorta a mano antes).

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Identificadores de la revisión (Alembic).
revision: str = '0002'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLA = 'audit_logs'
AL_BORRAR = 'SET NULL'
# (columna, largo anterior, largo nuevo, admite NULL)
LARGOS = (
    ('user', 100, 255, False),
    ('action', 50, 150, False),
    ('target', 100, 255, True),
)
# (columna, tabla referida)
REFERENCIAS = (
    ('actor_id', 'users'),
    ('target_user_id', 'users'),
    ('area_id', 'areas'),
    ('platform_id', 'platforms'),
)
INDICES = ('timestamp', 'actor_id', 'target_user_id', 'area_id', 'platform_id')


def _fk(columna):
    return f'fk_{TABLA}_{columna}'


def _ix(columna):
    return f'ix_{TABLA}_{columna}'


def upgrade() -> None:
    """Aplica el cambio de esquema."""
    with op.batch_alter_table(TABLA) as tabla:
        for columna, antes, despues, nulo in LARGOS:
            tabla.alter_column(columna, existing_type=sa.String(length=antes),
                               type_=sa.String(length=despues),
                               existing_nullable=nulo)
        for columna, _ in REFERENCIAS:
            tabla.add_column(sa.Column(columna, sa.Integer(), nullable=True))
        tabla.add_column(sa.Column('before_state', sa.JSON(), nullable=True))
        tabla.add_column(sa.Column('after_state', sa.JSON(), nullable=True))
        tabla.add_column(sa.Column('request_id', sa.Integer(), nullable=True))
        tabla.add_column(sa.Column('grant_id', sa.Integer(), nullable=True))
        # Índices antes que las FK: MySQL reutiliza el índice y no crea otro.
        for columna in INDICES:
            tabla.create_index(_ix(columna), [columna], unique=False)
        for columna, referida in REFERENCIAS:
            tabla.create_foreign_key(_fk(columna), referida, [columna], ['id'],
                                     ondelete=AL_BORRAR)


def downgrade() -> None:
    """Revierte el cambio de esquema (se pierden las columnas nuevas)."""
    with op.batch_alter_table(TABLA) as tabla:
        # FK antes que los índices: MySQL no borra un índice que usa una FK.
        for columna, _ in REFERENCIAS:
            tabla.drop_constraint(_fk(columna), type_='foreignkey')
        for columna in INDICES:
            tabla.drop_index(_ix(columna))
        for columna in ('grant_id', 'request_id', 'after_state', 'before_state'):
            tabla.drop_column(columna)
        for columna, _ in REFERENCIAS:
            tabla.drop_column(columna)
        for columna, antes, despues, nulo in LARGOS:
            tabla.alter_column(columna, existing_type=sa.String(length=despues),
                               type_=sa.String(length=antes),
                               existing_nullable=nulo)
