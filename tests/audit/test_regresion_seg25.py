"""Regresión de SEG-20261013-25 (FNC-047, absorbe parte de FNC-015).

- Un correo largo en un login fallido queda registrado: `action` corta y el
  correo en `target`, sin exceder el largo de las columnas (en MySQL estricto
  un valor más largo hace fallar el INSERT y el intento no queda registrado).
- La IP registrada es la del cliente cuando la petición llega del proxy de
  confianza, y `X-Forwarded-For` se ignora si llega de otro origen.

Sin direcciones IP: los orígenes son nombres ficticios (como en test_sso.py).
"""

from app.modules.audit.models import AuditLog
from app.modules.audit.services import add_audit_log
from tests.peticiones_auth import iniciar_sesion_api

LARGO_CORREO = 120
DOMINIO = '@pruebas.local'
PROXY_FICTICIO = 'proxy.pruebas.invalid'
CLIENTE_REAL = 'cliente-real.pruebas.invalid'
ORIGEN_AJENO = 'ajeno.pruebas.invalid'
CLIENTE_FALSO = 'falso.pruebas.invalid'
ACCION_PRUEBA = 'PRUEBA IP'


def _largo_columna(nombre):
    return AuditLog.__table__.c[nombre].type.length


def test_login_fallido_con_correo_de_120_caracteres_queda_registrado(client):
    correo = 'a' * (LARGO_CORREO - len(DOMINIO)) + DOMINIO
    assert len(correo) == LARGO_CORREO

    respuesta = iniciar_sesion_api(client, correo, 'contrasena-ficticia')

    assert respuesta.status_code == 401
    registro = AuditLog.query.filter_by(status='error').one()
    assert registro.action == 'ACCESO FALLIDO'
    assert registro.target == correo
    for columna in ('user', 'action', 'module', 'target', 'ip_address'):
        valor = getattr(registro, columna)
        assert valor is None or len(valor) <= _largo_columna(columna), columna


def test_valores_mas_largos_que_la_columna_se_recortan(app):
    largo = _largo_columna('target')

    add_audit_log('x' * (_largo_columna('action') + 10), target='t' * (largo + 10))

    registro = AuditLog.query.one()
    assert len(registro.action) == _largo_columna('action')
    assert len(registro.target) == largo


def _registrar_con(app, origen, reenviada, monkeypatch):
    monkeypatch.setenv('TRUSTED_PROXIES', PROXY_FICTICIO)
    entorno = {'REMOTE_ADDR': origen}
    with app.test_request_context(headers={'X-Forwarded-For': reenviada},
                                  environ_base=entorno):
        add_audit_log(ACCION_PRUEBA)
    return AuditLog.query.filter_by(action=ACCION_PRUEBA).one().ip_address


def test_ip_real_del_cliente_detras_del_proxy_de_confianza(app, monkeypatch):
    # nginx agrega la dirección real al final ($proxy_add_x_forwarded_for).
    reenviada = f'{CLIENTE_FALSO}, {CLIENTE_REAL}'

    assert _registrar_con(app, PROXY_FICTICIO, reenviada, monkeypatch) \
        == CLIENTE_REAL


def test_x_forwarded_for_de_otro_origen_se_ignora(app, monkeypatch):
    assert _registrar_con(app, ORIGEN_AJENO, CLIENTE_FALSO, monkeypatch) \
        == ORIGEN_AJENO


def test_proxy_de_confianza_sin_x_forwarded_for_registra_su_direccion(
        app, monkeypatch):
    assert _registrar_con(app, PROXY_FICTICIO, '', monkeypatch) \
        == PROXY_FICTICIO
