"""Arranque: `create_app` con configuración válida, inválida y faltante (FNC-023).

`create_app` se llama sin `config_overrides`, como en producción. La carpeta
`instance/` de Flask se redirige a un directorio temporal para que el SQLite
por defecto no quede en el repo, y `db.create_all` se sustituye donde la BD
sería externa (MySQL) para no abrir conexiones.
"""

import flask
import pytest

from app import create_app, db
from tests.conftest import VARIABLES_PRUEBA

CLAVE_POR_DEFECTO = 'nexus-premium-secret-key'
HOST_BD_FICTICIO = 'bd.pruebas.invalid'
BD_MYSQL = {'DB_ENGINE': 'mysql', 'DB_USER': 'usuario', 'DB_PASS': 'clave',
            'DB_HOST': HOST_BD_FICTICIO, 'DB_PORT': '3306',
            'DB_NAME': 'nexus_pruebas'}


@pytest.fixture
def instancia(tmp_path, monkeypatch):
    """`instance/` en un directorio temporal; libera el motor al terminar."""
    monkeypatch.setattr(flask.Flask, 'auto_find_instance_path',
                        lambda self: str(tmp_path))
    creadas = []

    def _crear():
        aplicacion = create_app()
        creadas.append(aplicacion)
        return aplicacion

    yield _crear
    for aplicacion in creadas:
        with aplicacion.app_context():
            db.session.remove()
            db.engine.dispose()


@pytest.fixture
def sin_bd_externa(monkeypatch):
    """`db.create_all` falla antes de conectar: create_app captura el error."""
    def _sin_conexion(*args, **kwargs):
        raise RuntimeError('BD externa no disponible en pruebas')
    monkeypatch.setattr(db, 'create_all', _sin_conexion)


def test_configuracion_minima_arranca_con_sqlite(instancia, tmp_path):
    aplicacion = instancia()

    assert aplicacion.config['SECRET_KEY'] == VARIABLES_PRUEBA['SECRET_KEY']
    assert aplicacion.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///nexus.db'
    assert (tmp_path / 'nexus.db').exists()
    respuesta = aplicacion.test_client().get('/api/v1/auth/context')
    assert respuesta.status_code == 200


def test_mysql_arma_la_url_desde_las_variables(instancia, sin_bd_externa,
                                               monkeypatch):
    for clave, valor in BD_MYSQL.items():
        monkeypatch.setenv(clave, valor)

    aplicacion = instancia()

    assert aplicacion.config['SQLALCHEMY_DATABASE_URI'] == (
        f'mysql+pymysql://usuario:clave@{HOST_BD_FICTICIO}:3306/nexus_pruebas')


def test_la_sesion_dura_siete_dias_y_tiene_nombre_propio(instancia):
    aplicacion = instancia()

    assert aplicacion.config['PERMANENT_SESSION_LIFETIME'].days == 7
    assert aplicacion.config['SESSION_COOKIE_NAME'] == 'nexus_session'


# --------------------------------------------------------------------------- #
# Configuración faltante o inválida: debe fallar con un mensaje claro
# --------------------------------------------------------------------------- #

@pytest.mark.xfail(strict=True, reason='SEG-07 / FNC-009: sin SECRET_KEY '
                   'arranca con una clave por defecto que está en el código')
def test_sin_secret_key_no_arranca(instancia, monkeypatch):
    monkeypatch.delenv('SECRET_KEY')

    with pytest.raises(Exception):
        instancia()


@pytest.mark.xfail(strict=True, reason='SEG-07 / FNC-009: acepta como '
                   'SECRET_KEY el valor por defecto publicado en el repo')
def test_secret_key_conocida_no_arranca(instancia, monkeypatch):
    monkeypatch.setenv('SECRET_KEY', CLAVE_POR_DEFECTO)

    with pytest.raises(Exception):
        instancia()


@pytest.mark.xfail(strict=True, reason='FNC-009: un DB_ENGINE desconocido '
                   'cae en silencio a SQLite (deuda 10 de docs/backend)')
@pytest.mark.parametrize('motor', ['postgresql', 'MySQL', 'otro'])
def test_db_engine_invalido_no_arranca(instancia, monkeypatch, motor):
    monkeypatch.setenv('DB_ENGINE', motor)

    with pytest.raises(Exception):
        instancia()


@pytest.mark.xfail(strict=True, reason='FNC-009: sin DB_ENGINE cae en '
                   'silencio a SQLite; debe declararse explícito')
def test_sin_db_engine_no_arranca(instancia, monkeypatch):
    monkeypatch.delenv('DB_ENGINE')

    with pytest.raises(Exception):
        instancia()

