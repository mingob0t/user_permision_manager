"""Línea base: esquema actual completo (equivale a `db.create_all()` de hoy).

- BD nueva: `alembic upgrade head` crea todas las tablas.
- BD existente de NEXUS (creada con `create_all()` y `utils/migrations/001-004`):
  no se aplica; se marca con `alembic stamp 0001` (docs/backend/README.md §7).

Revision ID: 0001
Revises: 
Create Date: 2026-10-14 00:21:16.407177

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Identificadores de la revisión (Alembic).
revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Aplica el cambio de esquema."""
    op.create_table('areas',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('icon', sa.String(length=50), nullable=True),
    sa.Column('color', sa.String(length=100), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('audit_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('user', sa.String(length=100), nullable=False),
    sa.Column('action', sa.String(length=50), nullable=False),
    sa.Column('module', sa.String(length=50), nullable=True),
    sa.Column('target', sa.String(length=100), nullable=True),
    sa.Column('detail', sa.Text(), nullable=True),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('auth_config',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ldap_host', sa.String(length=100), nullable=True),
    sa.Column('ldap_port', sa.Integer(), nullable=True),
    sa.Column('ldap_ssl', sa.Boolean(), nullable=True),
    sa.Column('ldap_base_dn', sa.String(length=200), nullable=True),
    sa.Column('ldap_user', sa.String(length=100), nullable=True),
    sa.Column('ldap_pass', sa.String(length=100), nullable=True),
    sa.Column('ldap_user_attr', sa.String(length=50), nullable=True),
    sa.Column('ldap_group_admin', sa.String(length=200), nullable=True),
    sa.Column('ldap_group_user', sa.String(length=200), nullable=True),
    sa.Column('ldap_role_mappings', sa.Text(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('notification_templates',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('subject', sa.String(length=255), nullable=False),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('is_html', sa.Boolean(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('slug')
    )
    op.create_table('smtp_config',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('server', sa.String(length=100), nullable=True),
    sa.Column('port', sa.Integer(), nullable=True),
    sa.Column('encryption', sa.String(length=20), nullable=True),
    sa.Column('auth_enabled', sa.Boolean(), nullable=True),
    sa.Column('username', sa.String(length=100), nullable=True),
    sa.Column('password', sa.String(length=100), nullable=True),
    sa.Column('sender_name', sa.String(length=100), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('system_config',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('portal_name', sa.String(length=100), nullable=True),
    sa.Column('portal_identity_type', sa.String(length=10), nullable=True),
    sa.Column('portal_icon', sa.Text(), nullable=True),
    sa.Column('bg_color', sa.String(length=20), nullable=True),
    sa.Column('text_color', sa.String(length=20), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('nombre', sa.String(length=100), nullable=True),
    sa.Column('password_hash', sa.String(length=255), nullable=True),
    sa.Column('role', sa.String(length=20), nullable=True),
    sa.Column('auth_source', sa.String(length=10), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('last_login_at', sa.DateTime(), nullable=True),
    sa.Column('pref_notifications', sa.Boolean(), nullable=True),
    sa.Column('pref_email_notifications', sa.Boolean(), nullable=True),
    sa.Column('pref_refresh_interval', sa.Integer(), nullable=True),
    sa.Column('pref_tour_enabled', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('area_admins',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('area_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['area_id'], ['areas.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'area_id')
    )
    op.create_table('in_app_notifications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('type', sa.String(length=20), nullable=True),
    sa.Column('title', sa.String(length=100), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('is_read', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('platforms',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('area_id', sa.Integer(), nullable=False),
    sa.Column('direct_link', sa.String(length=255), nullable=True),
    sa.Column('icon', sa.String(length=50), nullable=True),
    sa.Column('logo_url', sa.String(length=255), nullable=True),
    sa.Column('bg_color', sa.String(length=20), nullable=True),
    sa.Column('text_color', sa.String(length=20), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('visits', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['area_id'], ['areas.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user_areas',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('area_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['area_id'], ['areas.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'area_id')
    )
    op.create_table('user_favorites',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('platform_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['platform_id'], ['platforms.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'platform_id')
    )
    op.create_table('user_platforms',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('platform_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['platform_id'], ['platforms.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'platform_id')
    )


def downgrade() -> None:
    """Revierte el cambio de esquema."""
    op.drop_table('user_platforms')
    op.drop_table('user_favorites')
    op.drop_table('user_areas')
    op.drop_table('platforms')
    op.drop_table('in_app_notifications')
    op.drop_table('area_admins')
    op.drop_table('users')
    op.drop_table('system_config')
    op.drop_table('smtp_config')
    op.drop_table('notification_templates')
    op.drop_table('auth_config')
    op.drop_table('audit_logs')
    op.drop_table('areas')
