"""Lectura por usuario de las notificaciones globales (FNC-031).

- Crea `notification_reads`: una fila por (notificación, usuario) con
  `ON DELETE CASCADE` en ambas claves y par único.
- No migra datos: las globales marcadas antes como leídas (`is_read`) eran un
  efecto del defecto; el estado correcto parte de "sin leer" para todos.
- `downgrade()` borra la tabla: se pierde quién leyó cada global.

Revision ID: 0010
Revises: 0009
Create Date: 2026-10-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0010'
down_revision: Union[str, Sequence[str], None] = '0009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Valores fijos de esta revisión (no se importan del código, que puede cambiar).
TABLA = 'notification_reads'
AL_BORRAR = 'CASCADE'


def upgrade() -> None:
    op.create_table(
        TABLA,
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('notification_id', sa.Integer(),
                  sa.ForeignKey('in_app_notifications.id',
                                name='fk_notification_reads_notification_id',
                                ondelete=AL_BORRAR),
                  nullable=False),
        sa.Column('user_id', sa.Integer(),
                  sa.ForeignKey('users.id',
                                name='fk_notification_reads_user_id',
                                ondelete=AL_BORRAR),
                  nullable=False),
        sa.Column('read_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('notification_id', 'user_id',
                            name='uq_notification_reads_par'),
    )
    op.create_index('ix_notification_reads_notification_id', TABLA,
                    ['notification_id'])
    op.create_index('ix_notification_reads_user_id', TABLA, ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_notification_reads_user_id', table_name=TABLA)
    op.drop_index('ix_notification_reads_notification_id', table_name=TABLA)
    op.drop_table(TABLA)
