"""Plantillas de correo del gestor de accesos (FNC-048). Solo datos.

- Inserta `solicitud_nueva`, `solicitud_aprobada`, `solicitud_rechazada` y
  `aprovisionamiento_fallido` en `notification_templates` (HTML, en español).
- Si ya existe una plantilla con ese `slug` no la toca (puede venir editada
  desde Ajustes → Plantillas o de un respaldo).
- `downgrade()` borra solo las filas que siguen idénticas a las insertadas
  (`slug`, `name`, `subject` y `body`): una plantilla preexistente o editada
  desde la interfaz se conserva.
- Variables: las de `CLAVES_POR_PLANTILLA` en
  `app/modules/notifications/access_notifications.py`; los valores se escapan
  al enviar (SEC-MAIL-01).

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-15
"""
from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Identificadores de la revisión (Alembic).
revision: str = '0003'
down_revision: Union[str, Sequence[str], None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLA = 'notification_templates'

PLANTILLAS = (
    {
        'slug': 'solicitud_nueva',
        'name': 'Gestor de accesos: nueva solicitud',
        'subject': 'Nueva solicitud de acceso a {plataforma}',
        'body': (
            '<p>Hola:</p>\n'
            '<p><strong>{solicitante}</strong> ({correo_solicitante}) solicitó '
            'acceso de nivel <strong>{nivel}</strong> a la plataforma '
            '<strong>{plataforma}</strong> del área <strong>{area}</strong>.</p>\n'
            '<p>Justificación:</p>\n'
            '<blockquote>{justificacion}</blockquote>\n'
            '<p>Revisa la solicitud en la bandeja de aprobaciones del portal: '
            '{url}</p>\n'
        ),
    },
    {
        'slug': 'solicitud_aprobada',
        'name': 'Gestor de accesos: solicitud aprobada',
        'subject': 'Tu solicitud de acceso a {plataforma} fue aprobada',
        'body': (
            '<p>Hola {solicitante}:</p>\n'
            '<p>Se aprobó tu solicitud de acceso de nivel <strong>{nivel}</strong> '
            'a la plataforma <strong>{plataforma}</strong> del área '
            '<strong>{area}</strong>.</p>\n'
            '<p>El acceso se está aplicando; consulta su estado en el portal: '
            '{url}</p>\n'
        ),
    },
    {
        'slug': 'solicitud_rechazada',
        'name': 'Gestor de accesos: solicitud rechazada',
        'subject': 'Tu solicitud de acceso a {plataforma} fue rechazada',
        'body': (
            '<p>Hola {solicitante}:</p>\n'
            '<p>Se rechazó tu solicitud de acceso de nivel <strong>{nivel}</strong> '
            'a la plataforma <strong>{plataforma}</strong> del área '
            '<strong>{area}</strong>.</p>\n'
            '<p>Motivo:</p>\n'
            '<blockquote>{motivo}</blockquote>\n'
            '<p>Portal: {url}</p>\n'
        ),
    },
    {
        'slug': 'aprovisionamiento_fallido',
        'name': 'Gestor de accesos: fallo de aprovisionamiento',
        'subject': 'Fallo de aprovisionamiento ({operacion}) en {plataforma}',
        'body': (
            '<p>Hola:</p>\n'
            '<p>No se pudo <strong>{operacion}</strong> el acceso de nivel '
            '<strong>{nivel}</strong> de <strong>{usuario}</strong> '
            '({correo_usuario}) en la plataforma <strong>{plataforma}</strong> '
            'del área <strong>{area}</strong>: se agotaron los reintentos.</p>\n'
            '<p>El superadmin puede reintentar la ejecución desde el portal: '
            '{url}</p>\n'
        ),
    },
)


def _tabla():
    return sa.table(
        TABLA,
        sa.column('slug', sa.String),
        sa.column('name', sa.String),
        sa.column('subject', sa.String),
        sa.column('body', sa.Text),
        sa.column('is_html', sa.Boolean),
        sa.column('updated_at', sa.DateTime),
    )


def upgrade() -> None:
    """Inserta las plantillas que falten."""
    tabla = _tabla()
    conexion = op.get_bind()
    existentes = set(conexion.execute(sa.select(tabla.c.slug)).scalars())
    ahora = datetime.now()
    nuevas = [dict(p, is_html=True, updated_at=ahora)
              for p in PLANTILLAS if p['slug'] not in existentes]
    if nuevas:
        op.bulk_insert(tabla, nuevas)


def downgrade() -> None:
    """Borra las plantillas de esta migración que no cambiaron."""
    tabla = _tabla()
    sin_cambios = [sa.and_(*(tabla.c[campo] == p[campo]
                             for campo in ('slug', 'name', 'subject', 'body')))
                   for p in PLANTILLAS]
    op.execute(tabla.delete().where(sa.or_(*sin_cambios)))
