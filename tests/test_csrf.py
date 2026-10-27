"""CSRF: manejo del error y exención de la API (FNC-023).

Hoy toda la API v1 está exenta de CSRF y la cookie no declara `SameSite`
(SEG-06). Lo correcto se prueba con `xfail(strict=True)` hasta FNC-008.
"""

import io

import pytest
from flask import jsonify

from app.modules.auth.models import User

RUTA_PROTEGIDA = '/prueba-csrf'
ORIGEN_AJENO = 'https://atacante.pruebas.invalid'
CABECERAS_AJENAS = {'Origin': ORIGEN_AJENO, 'Sec-Fetch-Site': 'cross-site'}


@pytest.fixture
def app_con_ruta_protegida(app):
    """Una ruta de prueba no exenta, para ver la respuesta del CSRFError."""
    app.add_url_rule(RUTA_PROTEGIDA, 'prueba_csrf',
                     lambda: jsonify({'status': 'success'}), methods=['POST'])
    return app


def test_sin_token_csrf_responde_400_en_json(app_con_ruta_protegida):
    respuesta = app_con_ruta_protegida.test_client().post(RUTA_PROTEGIDA)

    assert respuesta.status_code == 400
    assert respuesta.get_json() == {'status': 'error',
                                    'message': 'Token CSRF ausente o no válido.'}


@pytest.mark.xfail(strict=True, reason='SEG-06 / FNC-008: la cookie de sesión '
                   'no declara SameSite')
def test_cookie_de_sesion_con_samesite(app):
    assert app.config.get('SESSION_COOKIE_SAMESITE') in ('Lax', 'Strict')


@pytest.mark.xfail(strict=True, reason='SEG-06 / FNC-008: la API está exenta '
                   'de CSRF; un formulario de otro sitio importa un respaldo')
def test_formulario_de_otro_sitio_no_importa_un_respaldo(cliente_admin):
    respuesta = cliente_admin.post(
        '/api/v1/backup', headers=CABECERAS_AJENAS,
        data={'file': (io.BytesIO(b'no es zip'), 'r.zip')},
        content_type='multipart/form-data')

    assert respuesta.status_code in (400, 403)
    assert 'CSRF' in respuesta.get_json()['message'] or \
        respuesta.status_code == 403


@pytest.mark.xfail(strict=True, reason='SEG-06 / FNC-008: un POST sin cuerpo '
                   'desde otro sitio ejecuta la purga de cuentas')
def test_post_de_otro_sitio_no_purga_cuentas(cliente_admin):
    usuarios_antes = User.query.count()

    respuesta = cliente_admin.post('/api/v1/users/purge',
                                   headers=CABECERAS_AJENAS)

    assert respuesta.status_code in (400, 403)
    assert User.query.count() == usuarios_antes
