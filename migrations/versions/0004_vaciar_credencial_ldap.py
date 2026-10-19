"""Credencial de bind fuera de la BD (FNC-043, SEG-08). Solo datos.

- Vacía `auth_config.ldap_pass`: la credencial de bind es `LDAP_BIND_PASSWORD`
  (`.env` en dev, Vaultwarden en staging/prod; SEC-LDAP-11, SEC-CFG-03).
- La columna se conserva, marcada obsoleta en el modelo y en
  `docs/configuracion/VARIABLES.md`; el modelo rechaza escribirla.
- `downgrade()` no restaura el valor (irreversible en datos, a propósito):
  la columna queda vacía y el código anterior la lee como "sin contraseña".

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Identificadores de la revisión (Alembic).
revision: str = '0004'
down_revision: Union[str, Sequence[str], None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLA = 'auth_config'
COLUMNA = 'ldap_pass'


def upgrade() -> None:
    """Pone en NULL la contraseña de bind guardada."""
    tabla = sa.table(TABLA, sa.column(COLUMNA, sa.String))
    op.execute(tabla.update().where(tabla.c[COLUMNA].isnot(None))
               .values({COLUMNA: None}))


def downgrade() -> None:
    """Sin cambios: el valor borrado no se puede recuperar."""
