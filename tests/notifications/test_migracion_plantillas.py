"""Migración `0003`: plantillas del gestor de accesos (FNC-048)."""

import pytest
from alembic import command
from sqlalchemy import create_engine, text

from tests.notifications.plantillas_migracion import PLANTILLAS
from tests.test_migraciones import migrar

SLUGS = sorted(p['slug'] for p in PLANTILLAS)


@pytest.fixture
def motor(app, tmp_path):
    motor = create_engine(f"sqlite:///{tmp_path / 'plantillas.db'}")
    yield motor
    motor.dispose()


def _slugs(motor):
    with motor.connect() as conexion:
        return sorted(conexion.execute(text(
            'SELECT slug FROM notification_templates')).scalars())


def test_upgrade_inserta_las_cuatro_plantillas_html(motor):
    migrar(motor, command.upgrade, '0003')

    assert _slugs(motor) == SLUGS
    with motor.connect() as conexion:
        assert set(conexion.execute(text(
            'SELECT is_html FROM notification_templates')).scalars()) == {1}


def test_upgrade_no_pisa_una_plantilla_ya_editada(motor):
    migrar(motor, command.upgrade, '0002')
    with motor.begin() as conexion:
        conexion.execute(text(
            "INSERT INTO notification_templates (slug, name, subject, body, "
            "is_html) VALUES ('solicitud_nueva', 'Mía', 'Mi asunto', 'Mi "
            "cuerpo', 0)"))

    migrar(motor, command.upgrade, '0003')

    assert _slugs(motor) == SLUGS
    with motor.connect() as conexion:
        assert conexion.execute(text(
            "SELECT subject FROM notification_templates WHERE "
            "slug = 'solicitud_nueva'")).scalar() == 'Mi asunto'


def test_downgrade_conserva_una_plantilla_preexistente_con_el_mismo_slug(motor):
    migrar(motor, command.upgrade, '0002')
    with motor.begin() as conexion:
        conexion.execute(text(
            "INSERT INTO notification_templates (slug, name, subject, body, "
            "is_html) VALUES ('solicitud_nueva', 'Mía', 'Mi asunto', 'Mi "
            "cuerpo', 0)"))
    migrar(motor, command.upgrade, '0003')

    migrar(motor, command.downgrade, '0002')

    assert _slugs(motor) == ['solicitud_nueva']


def test_downgrade_borra_solo_sus_plantillas(motor):
    migrar(motor, command.upgrade, '0003')
    with motor.begin() as conexion:
        conexion.execute(text(
            "INSERT INTO notification_templates (slug, name, subject, body, "
            "is_html) VALUES ('usuario_creado', 'Alta', 'Hola', 'x', 0)"))

    migrar(motor, command.downgrade, '0002')

    assert _slugs(motor) == ['usuario_creado']
