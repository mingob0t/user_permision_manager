"""Plataformas: tipo de integración y grupos del directorio por nivel (FNC-046).

- Agrega a `platforms`: `integration_type` (`ldap` | `conector`),
  `ldap_group_user_dn`, `ldap_group_admin_dn` y `groups_status`.
- Las plataformas existentes quedan `ldap` sin grupos y `sin_verificar`: no se
  pueden solicitar hasta que el superadmin complete sus grupos.
- `downgrade()` quita las columnas (se pierden los DN guardados).

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Identificadores de la revisión (Alembic).
revision: str = '0005'
down_revision: Union[str, Sequence[str], None] = '0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLA = 'platforms'
# Valores fijos de esta revisión (no se importan del código, que puede cambiar).
TIPO_POR_DEFECTO = 'ldap'
ESTADO_POR_DEFECTO = 'sin_verificar'
LARGO_TIPO = 20
LARGO_DN = 512
LARGO_ESTADO = 20


def upgrade() -> None:
    with op.batch_alter_table(TABLA) as tabla:
        tabla.add_column(sa.Column('integration_type', sa.String(LARGO_TIPO),
                                   nullable=False,
                                   server_default=TIPO_POR_DEFECTO))
        tabla.add_column(sa.Column('ldap_group_user_dn', sa.String(LARGO_DN),
                                   nullable=True))
        tabla.add_column(sa.Column('ldap_group_admin_dn', sa.String(LARGO_DN),
                                   nullable=True))
        tabla.add_column(sa.Column('groups_status', sa.String(LARGO_ESTADO),
                                   nullable=False,
                                   server_default=ESTADO_POR_DEFECTO))


def downgrade() -> None:
    with op.batch_alter_table(TABLA) as tabla:
        tabla.drop_column('groups_status')
        tabla.drop_column('ldap_group_admin_dn')
        tabla.drop_column('ldap_group_user_dn')
        tabla.drop_column('integration_type')
