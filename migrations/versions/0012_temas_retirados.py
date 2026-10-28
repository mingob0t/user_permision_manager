"""Temas retirados de la cuenta del usuario (FNC-132).

- Convierte `users.pref_theme`: `esmeralda` y `rosa` pasan a `claro`;
  `obsidiana` y `violeta`, a `oscuro`; cualquier valor fuera de
  `sistema`/`claro`/`oscuro`, a `sistema`. Es idempotente.
- `downgrade()` no cambia datos: el tema exacto anterior no se puede
  recuperar (varios temas pasaron a uno solo), así que los valores quedan
  convertidos. Para volver atrás con fidelidad, respaldar `users.pref_theme`
  antes de aplicar esta revisión. No hay nada más que revertir (sin cambios
  de esquema).

Revision ID: 0012
Revises: 0011
Create Date: 2026-10-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0012'
down_revision: Union[str, Sequence[str], None] = '0011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Valores fijos de esta revisión (no se importan del código, que puede cambiar).
TEMA_INICIAL = 'sistema'
TEMAS_QUE_QUEDAN = ('sistema', 'claro', 'oscuro')
CONVERSION = {
    'esmeralda': 'claro',
    'rosa': 'claro',
    'obsidiana': 'oscuro',
    'violeta': 'oscuro',
}


def upgrade() -> None:
    conexion = op.get_bind()
    for viejo, nuevo in CONVERSION.items():
        conexion.execute(
            sa.text('UPDATE users SET pref_theme = :nuevo '
                    'WHERE pref_theme = :viejo'),
            {'nuevo': nuevo, 'viejo': viejo})
    # Lo que no sea de la lista (la API solo guarda ids exactos, así que la
    # comparación sin distinguir mayúsculas de MySQL no deja casos reales).
    conexion.execute(
        sa.text('UPDATE users SET pref_theme = :inicial '
                'WHERE pref_theme NOT IN :quedan')
        .bindparams(sa.bindparam('quedan', expanding=True)),
        {'inicial': TEMA_INICIAL, 'quedan': list(TEMAS_QUE_QUEDAN)})


def downgrade() -> None:
    """Sin cambio de datos: ver la nota del módulo."""
