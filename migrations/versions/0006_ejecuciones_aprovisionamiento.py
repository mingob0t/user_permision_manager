"""Ejecuciones de aprovisionamiento: trabajos e intentos (FNC-049).

- Crea `provisioning_jobs` (cola persistente con estado, intentos, reserva y
  clave de idempotencia única) y `provisioning_job_attempts` (bitácora).
- Referencias a usuarios, plataformas y áreas con `ON DELETE SET NULL`: el
  historial se conserva. `access_id` sin FK hasta FNC-054.
- `downgrade()` borra ambas tablas (se pierde la bitácora de ejecuciones).

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Identificadores de la revisión (Alembic).
revision: str = '0006'
down_revision: Union[str, Sequence[str], None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Valores fijos de esta revisión (no se importan del código, que puede cambiar).
TABLA_TRABAJOS = 'provisioning_jobs'
TABLA_INTENTOS = 'provisioning_job_attempts'
AL_BORRAR_REFERENCIA = 'SET NULL'
AL_BORRAR_TRABAJO = 'CASCADE'
LARGO_OPERACION = 10
LARGO_PROVEEDOR = 20
LARGO_NIVEL = 10
LARGO_ESTADO = 20
LARGO_RESULTADO = 20
LARGO_CLAVE = 100
LARGO_RESERVADO_POR = 100
LARGO_ERROR = 500


def _referencia(columna, tabla):
    return sa.ForeignKey(f'{tabla}.id', name=f'fk_provisioning_jobs_{columna}',
                         ondelete=AL_BORRAR_REFERENCIA)


def upgrade() -> None:
    op.create_table(
        TABLA_TRABAJOS,
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('operation', sa.String(LARGO_OPERACION), nullable=False),
        sa.Column('provider', sa.String(LARGO_PROVEEDOR), nullable=False),
        sa.Column('level', sa.String(LARGO_NIVEL), nullable=False),
        sa.Column('status', sa.String(LARGO_ESTADO), nullable=False),
        sa.Column('user_id', sa.Integer(), _referencia('user_id', 'users'),
                  nullable=True),
        sa.Column('platform_id', sa.Integer(),
                  _referencia('platform_id', 'platforms'), nullable=True),
        sa.Column('area_id', sa.Integer(), _referencia('area_id', 'areas'),
                  nullable=True),
        sa.Column('access_id', sa.Integer(), nullable=True),
        sa.Column('idempotency_key', sa.String(LARGO_CLAVE), nullable=False),
        sa.Column('attempts_count', sa.Integer(), nullable=False),
        sa.Column('max_attempts', sa.Integer(), nullable=False),
        sa.Column('next_attempt_at', sa.DateTime(), nullable=True),
        sa.Column('locked_at', sa.DateTime(), nullable=True),
        sa.Column('locked_by', sa.String(LARGO_RESERVADO_POR), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('idempotency_key',
                            name='uq_provisioning_jobs_idempotency_key'),
    )
    op.create_index('ix_provisioning_jobs_status_next', TABLA_TRABAJOS,
                    ['status', 'next_attempt_at'])
    op.create_index('ix_provisioning_jobs_access_id', TABLA_TRABAJOS,
                    ['access_id'])
    op.create_table(
        TABLA_INTENTOS,
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('job_id', sa.Integer(),
                  sa.ForeignKey(f'{TABLA_TRABAJOS}.id',
                                name='fk_provisioning_job_attempts_job_id',
                                ondelete=AL_BORRAR_TRABAJO),
                  nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('result', sa.String(LARGO_RESULTADO), nullable=True),
        sa.Column('error', sa.String(LARGO_ERROR), nullable=True),
        sa.UniqueConstraint('job_id', 'number',
                            name='uq_provisioning_job_attempts_job_number'),
    )


def downgrade() -> None:
    op.drop_table(TABLA_INTENTOS)
    op.drop_index('ix_provisioning_jobs_access_id', table_name=TABLA_TRABAJOS)
    op.drop_index('ix_provisioning_jobs_status_next', table_name=TABLA_TRABAJOS)
    op.drop_table(TABLA_TRABAJOS)
