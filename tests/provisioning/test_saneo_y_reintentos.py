"""Error saneado (SEC-CON-10) y espera entre intentos (SEC-CON-08)."""
import pytest

from app.modules.provisioning.reintentos import segundos_de_espera
from app.modules.provisioning.saneo import mensaje_de_error, sanear_error

ENTORNO = {'LDAP_BIND_PASSWORD': 'Clave-Ficticia-1', 'REDIS_PASS': 'abc'}


@pytest.mark.parametrize('texto, prohibido', [
    ('fallo con Clave-Ficticia-1 al enlazar', 'Clave-Ficticia-1'),
    ('ldap_password=xyz789 y más', 'xyz789'),
    ('api_key: "k 1 2"', 'k 1 2'),
    ("token='t0k'", 't0k'),
    ('Authorization: Bearer eyJabc', 'eyJabc'),
    ('ssh://root:pw123@srv.ejemplo.local/', 'pw123'),
    ('línea1\r\nlínea2\x00', '\n'),
])
def test_sanear_quita_secretos_y_control(texto, prohibido):
    assert prohibido not in sanear_error(texto, ENTORNO)


def test_sanear_no_busca_secretos_cortos():
    # `REDIS_PASS=abc` es demasiado corta: no se borra "abc" de cualquier texto.
    assert sanear_error('abcdef', ENTORNO) == 'abcdef'


def test_sanear_trunca_a_500():
    assert len(sanear_error('x' * 2000, ENTORNO)) == 500


def test_mensaje_del_catalogo_y_generico():
    assert mensaje_de_error('error_permanente', 'grupo_inexistente') == (
        'El grupo no existe en el directorio.')
    assert mensaje_de_error('error_permanente', 'directorio') == (
        'El directorio rechazó la operación.')
    assert mensaje_de_error('error_permanente', 'otro_desconocido') == (
        'Error del proveedor.')


@pytest.mark.parametrize('intentos, azar, esperado', [
    (1, 0.0, 30), (1, 1.0, 60), (2, 0.0, 60), (3, 1.0, 240),
    (10, 1.0, 900), (10, 0.0, 450),
])
def test_backoff_exponencial_con_jitter_y_tope(intentos, azar, esperado):
    assert segundos_de_espera(intentos, 60, 900, lambda: azar) == esperado
