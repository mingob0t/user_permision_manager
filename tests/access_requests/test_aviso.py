"""Aviso `solicitud_nueva` al crear una solicitud (FNC-056 sobre FNC-048)."""
import pytest

from app import db
from app.authz import ROLE_AREA_ADMIN
from app.modules.access_requests.models import PlatformAccessRequest
from app.modules.notifications.models import SMTPConfig
from tests import fabricas
from tests.access_requests.conftest import pedir
from tests.matriz_proteccion import HOST_SMTP_FICTICIO
from tests.notifications.plantillas_migracion import cargar_plantillas
from tests.smtp_falso import instalar_smtp


@pytest.fixture
def correo(app, monkeypatch):
    monkeypatch.setenv('ENABLE_NOTIFICATIONS', 'true')
    monkeypatch.setenv('BASE_URL', 'https://portal.pruebas.invalid')
    db.session.add(SMTPConfig(server=HOST_SMTP_FICTICIO, port=587,
                              encryption='starttls', auth_enabled=False,
                              sender_name='Portal de prueba'))
    db.session.commit()
    cargar_plantillas()
    return instalar_smtp(monkeypatch)


def _para(mensaje):
    return sorted(d.strip() for d in mensaje['To'].split(','))


def test_avisa_a_todos_los_admins_del_area(escena, correo, cliente_como):
    otro = fabricas.crear_usuario(ROLE_AREA_ADMIN, 'admin2@pruebas.local',
                                  areas_administradas=[escena['area']])

    respuesta = pedir(cliente_como(escena['usuario']), escena['plataforma'])

    assert respuesta.status_code == 201
    assert len(correo.enviados) == 1
    assert _para(correo.enviados[0]) == sorted(['admin@pruebas.local',
                                                otro.email])


def test_un_fallo_del_correo_no_revierte_la_solicitud(escena, correo,
                                                      cliente_como):
    correo.error = OSError('SMTP caído')

    respuesta = pedir(cliente_como(escena['usuario']), escena['plataforma'])

    assert respuesta.status_code == 201
    assert PlatformAccessRequest.query.count() == 1


def test_sin_aviso_si_la_solicitud_se_rechaza(escena, correo, cliente_como):
    pedir(cliente_como(escena['admin']), escena['plataforma'])

    assert correo.enviados == []
