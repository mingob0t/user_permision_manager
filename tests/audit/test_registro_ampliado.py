"""Registro de auditoría ampliado (FNC-047, F-AUD-01, SEC-AUD-02 y 05).

- `add_audit_log` sigue aceptando las llamadas existentes y suma, por nombre,
  usuario afectado, área, plataforma, antes/después y solicitud/acceso.
- El actor sale de la sesión; `as_system=True`, sin sesión o fuera de una
  petición, el actor es "sistema" (sin id).
- El catálogo `Evento` coincide con `docs/contratos/auditoria.md`.
- `GET /audit` sin `page` sigue devolviendo un arreglo, ahora con los campos nuevos.
"""

import pathlib
import re
from datetime import datetime

from app.authz import ROLE_ADMIN, ROLE_USER
from app.modules.audit.events import ACTOR_SISTEMA, Evento
from app.modules.audit.models import AuditLog
from app.modules.audit.sanitizar import VALOR_OMITIDO
from app.modules.audit.services import IP_INTERNA, add_audit_log
from tests import fabricas

A = '/api/v1'
CONTRATO = pathlib.Path(__file__).resolve().parents[2] / 'docs' / 'contratos' \
    / 'auditoria.md'
CAMPOS_NUEVOS = {'actor', 'area', 'platform', 'target_user', 'before', 'after'}
CAMPOS_EXISTENTES = {'id', 'time', 'user', 'action', 'module', 'target',
                     'detail', 'ip', 'status'}


def _unico():
    return AuditLog.query.one()


def test_llamada_heredada_sigue_funcionando(app):
    add_audit_log('ACCIÓN HEREDADA', 'warning', 'detalle', None, 'Módulo', 'obj')

    registro = _unico()
    assert (registro.action, registro.status, registro.detail, registro.module,
            registro.target) == ('ACCIÓN HEREDADA', 'warning', 'detalle',
                                 'Módulo', 'obj')


def test_fuera_de_peticion_actua_el_sistema(app):
    add_audit_log(Evento.ACCESO_ACTIVO, 'success')

    registro = _unico()
    assert registro.action == 'acceso_activo'
    assert (registro.user, registro.actor_id) == (ACTOR_SISTEMA, None)
    assert registro.ip_address == IP_INTERNA


def test_con_sesion_registra_id_y_correo_del_actor(app):
    actor = fabricas.crear_usuario(ROLE_ADMIN, email='actor@pruebas.local')
    with app.test_request_context():
        from flask_login import login_user
        login_user(actor)
        add_audit_log(Evento.ROL_CAMBIADO, 'success')

    registro = _unico()
    assert (registro.user, registro.actor_id) == ('actor@pruebas.local', actor.id)
    assert registro.to_dict()['actor'] == {'id': actor.id,
                                           'email': 'actor@pruebas.local'}


def test_as_system_ignora_la_sesion(app):
    admin = fabricas.crear_usuario(ROLE_ADMIN)
    with app.test_request_context():
        from flask_login import login_user
        login_user(admin)
        add_audit_log(Evento.ACCESO_OTORGADO, 'success', as_system=True)

    datos = _unico().to_dict()
    assert (datos['user'], datos['actor']) == (ACTOR_SISTEMA, None)


def test_area_plataforma_y_usuario_afectado(app):
    area = fabricas.crear_area('Finanzas')
    plataforma = fabricas.crear_plataforma(area, 'Contabilidad')
    afectado = fabricas.crear_usuario(ROLE_USER, email='luis@pruebas.local')

    add_audit_log(Evento.ACCESO_OTORGADO, 'success', target=afectado.email,
                  target_user_id=afectado.id, area_id=area.id,
                  platform_id=plataforma.id, request_id=7, grant_id=9)

    registro = _unico()
    assert (registro.request_id, registro.grant_id) == (7, 9)
    datos = registro.to_dict()
    assert datos['area'] == {'id': area.id, 'name': 'Finanzas'}
    assert datos['platform'] == {'id': plataforma.id, 'name': 'Contabilidad'}
    assert datos['target_user'] == {'id': afectado.id,
                                    'email': 'luis@pruebas.local'}


def test_antes_y_despues_sin_datos_sensibles(app):
    fecha = datetime(2026, 10, 14, 15, 0, 0)
    antes = {'role': 'usuario', 'password': 'x', 'password_hash': 'h'}
    despues = {'role': 'admin', 'conector': {'token': 't', 'Authorization': 'a',
                                             'host': 'h.pruebas.invalid'},
               'cuando': fecha, 'grupos': [{'secret': 's', 'dn': 'cn=g'}]}

    add_audit_log(Evento.ROL_CAMBIADO, 'success', before=antes, after=despues)

    datos = _unico().to_dict()
    assert datos['before'] == {'role': 'usuario', 'password': VALOR_OMITIDO,
                               'password_hash': VALOR_OMITIDO}
    assert datos['after'] == {
        'role': 'admin',
        'conector': {'token': VALOR_OMITIDO, 'Authorization': VALOR_OMITIDO,
                     'host': 'h.pruebas.invalid'},
        'cuando': str(fecha),
        'grupos': [{'secret': VALOR_OMITIDO, 'dn': 'cn=g'}]}
    assert antes['password'] == 'x', 'no se modifica el diccionario original'


def test_sin_detalle_antes_y_despues_son_nulos(app):
    add_audit_log('SIN DETALLE')

    datos = _unico().to_dict()
    assert (datos['before'], datos['after']) == (None, None)
    assert (datos['area'], datos['platform'], datos['target_user']) == \
        (None, None, None)


def test_el_catalogo_coincide_con_el_contrato():
    texto = CONTRATO.read_text(encoding='utf-8')
    seccion = texto.split('## Catálogo de `action`')[1].split('\n## ')[0]
    filas = [linea.split('|')[1] for linea in seccion.splitlines()
             if linea.startswith('| `') and not linea.startswith('| `action`')]
    del_contrato = {v for fila in filas for v in re.findall(r'`([a-z_]+)`', fila)}

    assert {e.value for e in Evento} == del_contrato


def test_get_audit_sin_page_sigue_siendo_arreglo_con_campos_nuevos(
        app, cliente_admin):
    add_audit_log(Evento.AREA_CREADA, 'success')

    respuesta = cliente_admin.get(f'{A}/audit')

    assert respuesta.status_code == 200
    cuerpo = respuesta.get_json()
    assert isinstance(cuerpo, list) and len(cuerpo) == 1
    assert set(cuerpo[0]) == CAMPOS_EXISTENTES | CAMPOS_NUEVOS


def test_configuracion_ldap_y_smtp_sin_credenciales(app):
    """Campos reales de AuthConfig y SMTPConfig, y la forma par key/value."""
    ldap = {'ldap_host': 'ldap.pruebas.invalid', 'ldap_port': 636,
            'ldap_user': 'cn=servicio', 'ldap_pass': 'p1', 'ldap_ssl': True}
    smtp = {'server': 'smtp.pruebas.invalid', 'username': 'envios',
            'password': 'p2', 'auth_enabled': True}
    otros = {'pwd': 'a', 'passwd': 'b', 'private_key': 'c', 'otp': 'd',
             'session_id': 'e', 'api_key': 'f',
             'pares': [{'key': 'smtp_password', 'value': 'g'},
                       {'name': 'ldap_host', 'value': 'ldap.pruebas.invalid'}]}

    add_audit_log(Evento.CONECTOR_CONFIGURADO, 'success', before=ldap,
                  after={'smtp': smtp, 'otros': otros})

    datos = _unico().to_dict()
    assert datos['before'] == {**ldap, 'ldap_pass': VALOR_OMITIDO}
    assert datos['after']['smtp'] == {**smtp, 'password': VALOR_OMITIDO}
    esperado = {k: VALOR_OMITIDO for k in otros if k != 'pares'}
    esperado['pares'] = [
        {'key': 'smtp_password', 'value': VALOR_OMITIDO},
        {'name': 'ldap_host', 'value': 'ldap.pruebas.invalid'}]
    assert datos['after']['otros'] == esperado
