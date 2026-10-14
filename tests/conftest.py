"""Base común de las pruebas del backend.

Las pruebas no dependen del `.env` ni de servicios externos:
- no se carga ningún `.env` (ni el del proyecto ni el de carpetas superiores);
- la configuración usa valores ficticios definidos aquí;
- la BD es un SQLite temporal por prueba;
- Redis no se conecta, y SMTP y LDAP quedan bloqueados (fallan si se usan).
"""

import os

import dotenv

# Antes de importar `app`: su `load_dotenv()` buscaría un `.env` hacia arriba
# y metería configuración real (BD, SMTP, LDAP, SSO) en las pruebas.
dotenv.load_dotenv = lambda *args, **kwargs: False

# Variables que apuntan a servicios externos: se quitan del entorno heredado.
PREFIJOS_EXTERNOS = ('DB_', 'REDIS_', 'SMTP_', 'AUTHELIA_', 'LDAP_', 'NOTIFY_',
                     'DEBUG_')
VARIABLES_EXTERNAS = ('TRUSTED_PROXIES', 'FRONTEND_URL', 'BASE_URL',
                      'ENABLE_NOTIFICATIONS')

# Valores ficticios de prueba (no son secretos).
VARIABLES_PRUEBA = {
    'SECRET_KEY': 'clave-ficticia-solo-para-pruebas',
    'DB_ENGINE': 'sqlite',
    'AUTHELIA_ENABLED': 'false',
    'ENABLE_NOTIFICATIONS': 'false',
    'NOTIFY_USER_CREATED': 'false',
}

for _clave in list(os.environ):
    if _clave.startswith(PREFIJOS_EXTERNOS) or _clave in VARIABLES_EXTERNAS:
        del os.environ[_clave]
os.environ.update(VARIABLES_PRUEBA)

import smtplib  # noqa: E402

import pytest  # noqa: E402

from app import create_app, db  # noqa: E402
from app.authz import ROLE_ADMIN, ROLE_AREA_ADMIN, ROLE_USER  # noqa: E402
from app.modules.auth import services as auth_services  # noqa: E402
from app.utils.redis_client import RedisClient  # noqa: E402
from tests import fabricas  # noqa: E402


class ServicioExternoBloqueado(RuntimeError):
    """Una prueba intentó usar un servicio externo real."""


def _bloqueado(nombre):
    def _falla(*args, **kwargs):
        raise ServicioExternoBloqueado(
            f'{nombre} está bloqueado en pruebas: simúlalo con monkeypatch.')
    return _falla


@pytest.fixture(autouse=True)
def sin_servicios_externos(monkeypatch):
    """Redis no conecta; SMTP y LDAP fallan si una prueba los usa sin simular."""
    monkeypatch.setattr(RedisClient, 'connect', lambda self: None)
    monkeypatch.setattr(smtplib, 'SMTP', _bloqueado('SMTP'))
    monkeypatch.setattr(smtplib, 'SMTP_SSL', _bloqueado('SMTP'))
    monkeypatch.setattr(auth_services, 'Connection', _bloqueado('LDAP'))


@pytest.fixture
def app(tmp_path):
    """App con configuración de pruebas y BD SQLite vacía en un archivo temporal.

    `create_app` crea el usuario semilla al arrancar; aquí se borra el esquema y
    se vuelve a crear para que cada prueba empiece con la BD vacía.
    """
    aplicacion = create_app({
        'TESTING': True,
        'SECRET_KEY': VARIABLES_PRUEBA['SECRET_KEY'],
        'SQLALCHEMY_DATABASE_URI': f"sqlite:///{tmp_path / 'pruebas.db'}",
    })
    with aplicacion.app_context():
        db.drop_all()
        db.create_all()
        yield aplicacion
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture
def client(app):
    """Cliente HTTP sin sesión."""
    return app.test_client()


@pytest.fixture
def crear_area(app):
    return fabricas.crear_area


@pytest.fixture
def crear_plataforma(app):
    return fabricas.crear_plataforma


@pytest.fixture
def crear_usuario(app):
    return fabricas.crear_usuario


def iniciar_sesion(cliente, usuario):
    """Deja la sesión de Flask-Login abierta para `usuario` en `cliente`."""
    with cliente.session_transaction() as sesion:
        sesion['_user_id'] = str(usuario.id)
        sesion['_fresh'] = True
    return cliente


@pytest.fixture
def cliente_como(app):
    """Devuelve una función: `cliente_como(usuario)` -> cliente con su sesión."""
    def _cliente_como(usuario):
        return iniciar_sesion(app.test_client(), usuario)
    return _cliente_como


@pytest.fixture
def cliente_de_rol(app, cliente_como):
    """Devuelve una función: `cliente_de_rol(rol)` -> (cliente, usuario).

    El usuario se crea con `fabricas.crear_usuario_de_rol` (con su área).
    """
    def _cliente_de_rol(rol):
        usuario = fabricas.crear_usuario_de_rol(rol)
        return cliente_como(usuario), usuario
    return _cliente_de_rol


@pytest.fixture
def cliente_admin(cliente_de_rol):
    return cliente_de_rol(ROLE_ADMIN)[0]


@pytest.fixture
def cliente_admin_area(cliente_de_rol):
    return cliente_de_rol(ROLE_AREA_ADMIN)[0]


@pytest.fixture
def cliente_usuario(cliente_de_rol):
    return cliente_de_rol(ROLE_USER)[0]
