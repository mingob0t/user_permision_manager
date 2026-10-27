"""Tema de la interfaz en la cuenta del usuario (FNC-122).

- Agrega `users.pref_theme` (texto, no nulo, por defecto `'sistema'`): las
  cuentas existentes quedan en `'sistema'`.
- `downgrade()` quita la columna: se pierde el tema elegido por cada usuario.

Revision ID: 0011
Revises: 0010
Create Date: 2026-10-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0011'
down_revision: Union[str, Sequence[str], None] = '0010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Valores fijos de esta revisión (no se importan del código, que puede cambiar).
TABLA = 'users'
COLUMNA = 'pref_theme'
TEMA_INICIAL = 'sistema'


def upgrade() -> None:
    with op.batch_alter_table(TABLA) as lote:
        lote.add_column(sa.Column(COLUMNA, sa.String(length=20), nullable=False,
                                  server_default=TEMA_INICIAL))


def downgrade() -> None:
    with op.batch_alter_table(TABLA) as lote:
        lote.drop_column(COLUMNA)
