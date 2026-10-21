"""Datos y entorno de las pruebas de conectores (FNC-050).

- `entorno_conector`: dev con la lista blanca de hosts y la credencial del
  conector `noop` en una variable de entorno con un valor ficticio.
- `conector_noop`: plataforma `conector` con su configuración `noop` y un
  usuario con correo.
- La caché de credenciales y el estado del `noop` se vacían en cada prueba.
"""
import pytest

from app import db
from app.modules.connectors import credenciales, noop
from app.modules.connectors.models import PlatformConnector
from app.modules.connectors.tipos import TIPO_NOOP
from app.modules.platforms.tipos import TIPO_CONECTOR
from tests import fabricas

HOST_PERMITIDO = 'noop.pruebas.local'
REFERENCIA = 'pokemon/pruebas-noop'
VARIABLE_CREDENCIAL = 'CONNECTOR_CREDENTIAL_POKEMON_PRUEBAS_NOOP'
# Valor ficticio de prueba (no es un secreto).
SECRETO_FICTICIO = 'Cr3dencial-Ficticia-De-Prueba'


@pytest.fixture(autouse=True)
def estado_limpio():
    credenciales.limpiar_cache()
    noop.limpiar()
    yield
    credenciales.limpiar_cache()
    noop.limpiar()


@pytest.fixture
def entorno_conector(monkeypatch):
    monkeypatch.setenv('APP_ENV', 'development')
    monkeypatch.setenv('CONNECTOR_ALLOWED_HOSTS', HOST_PERMITIDO)
    monkeypatch.setenv(VARIABLE_CREDENCIAL, SECRETO_FICTICIO)


def crear_conector(plataforma, **campos):
    valores = {'type': TIPO_NOOP, 'host': HOST_PERMITIDO, 'port': 443,
               'params': {}, 'credential_ref': REFERENCIA, 'active': True}
    valores.update(campos)
    conector = PlatformConnector(platform_id=plataforma.id, **valores)
    db.session.add(conector)
    db.session.commit()
    return conector


@pytest.fixture
def conector_noop(app, entorno_conector):
    """(plataforma, configuración, usuario) listos para aprovisionar."""
    area = fabricas.crear_area()
    plataforma = fabricas.crear_plataforma(area, integration_type=TIPO_CONECTOR,
                                           status='Activo')
    configuracion = crear_conector(plataforma)
    usuario = fabricas.crear_usuario(email='ana.ruiz@pruebas.local',
                                     areas=[area])
    return plataforma, configuracion, usuario
