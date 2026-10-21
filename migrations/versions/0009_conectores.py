"""Configuración del conector de cada plataforma (FNC-050, ADR-005).

- Crea `platform_connectors`: una por plataforma (`platform_id` único, `ON
  DELETE CASCADE`), tipo, host por nombre, puerto, parámetros JSON, referencia
  al ítem del gestor de secretos y estado de su verificación, activo.
- Ninguna columna guarda el valor de una credencial (SEC-CON-02).
- `downgrade()` borra la tabla: las plataformas `conector` quedan sin
  aprovisionar.

Revision ID: 0009
Revises: 0008
Create Date: 2026-10-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0009'
down_revision: Union[str, Sequence[str], None] = '0008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Valores fijos de esta revisión (no se importan del código, que puede cambiar).
TABLA = 'platform_connectors'
AL_BORRAR_PLATAFORMA = 'CASCADE'
LARGO_TIPO = 20
LARGO_HOST = 253
LARGO_REFERENCIA = 200
LARGO_ESTADO_CREDENCIAL = 20


def upgrade() -> None:
    op.create_table(
        TABLA,
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('platform_id', sa.Integer(),
                  sa.ForeignKey('platforms.id',
                                name='fk_platform_connectors_platform_id',
                                ondelete=AL_BORRAR_PLATAFORMA),
                  nullable=False),
        sa.Column('type', sa.String(LARGO_TIPO), nullable=False),
        sa.Column('host', sa.String(LARGO_HOST), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False),
        sa.Column('params', sa.JSON(), nullable=False),
        sa.Column('credential_ref', sa.String(LARGO_REFERENCIA),
                  nullable=False),
        sa.Column('credential_status', sa.String(LARGO_ESTADO_CREDENCIAL),
                  nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('platform_id',
                            name='uq_platform_connectors_platform_id'),
    )


def downgrade() -> None:
    op.drop_table(TABLA)
