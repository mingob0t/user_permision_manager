"""Respaldo: exportar e importar la configuración con `/api/v1/backup` (FNC-023).

Solo el superadmin; la protección por rol ya está en la matriz (FNC-020).
"""

import io
import json
import zipfile

import pytest

from app import db
from app.authz import ROLE_ADMIN, ROLE_USER
from app.modules.audit.models import AuditLog
from app.modules.auth.models import AuthConfig, User
from app.modules.notifications.models import NotificationTemplate, SMTPConfig
from app.modules.settings.models import SystemConfig
from tests import fabricas
from tests.matriz_proteccion import (CONTRASENA_FICTICIA, HOST_LDAP_FICTICIO,
                                     HOST_SMTP_FICTICIO)

RUTA = '/api/v1/backup'
ARCHIVO = 'nexus_config.json'
CLAVE_SMTP = 'clave-smtp-ficticia'
CLAVE_LDAP = 'clave-ldap-ficticia'


@pytest.fixture
def configuracion(app):
    """Portal, LDAP, SMTP, una plantilla y una cuenta local con contraseña."""
    db.session.add_all([
        SystemConfig(portal_name='Portal respaldado'),
        AuthConfig(ldap_host=HOST_LDAP_FICTICIO, ldap_base_dn='dc=pruebas',
                   ldap_pass=CLAVE_LDAP),
        SMTPConfig(server=HOST_SMTP_FICTICIO, port=2525, password=CLAVE_SMTP),
        NotificationTemplate(slug='aviso', name='Aviso', subject='Asunto',
                             body='Cuerpo'),
    ])
    db.session.commit()
    return fabricas.crear_usuario(ROLE_USER, email='local@pruebas.local',
                                  contrasena=CONTRASENA_FICTICIA)


def _leer_zip(respuesta):
    with zipfile.ZipFile(io.BytesIO(respuesta.data)) as paquete:
        return json.loads(paquete.read(ARCHIVO))


def _zip(contenido, nombre=ARCHIVO):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as paquete:
        paquete.writestr(nombre, contenido)
    return buffer.getvalue()


def _importar(cliente, datos, nombre='respaldo.zip'):
    return cliente.post(RUTA, data={'file': (io.BytesIO(datos), nombre)},
                        content_type='multipart/form-data')


# --------------------------------------------------------------------------- #
# Exportar
# --------------------------------------------------------------------------- #

def test_exporta_un_zip_con_toda_la_configuracion(configuracion,
                                                  cliente_admin):
    respuesta = cliente_admin.get(RUTA)

    assert respuesta.status_code == 200
    assert respuesta.mimetype == 'application/zip'
    assert 'attachment' in respuesta.headers['Content-Disposition']
    datos = _leer_zip(respuesta)
    carga = datos['payload']
    assert carga['system_config']['portal_name'] == 'Portal respaldado'
    assert carga['auth_config']['ldap_host'] == HOST_LDAP_FICTICIO
    assert carga['smtp_config']['server'] == HOST_SMTP_FICTICIO
    assert [t['slug'] for t in carga['templates']] == ['aviso']
    assert 'local@pruebas.local' in {u['email'] for u in carga['users']}
    assert AuditLog.query.filter_by(action='EXPORTAR CONFIGURACIÓN').count() == 1


def test_exportar_no_incluye_contrasenas_de_servicio(configuracion,
                                                     cliente_admin):
    texto = json.dumps(_leer_zip(cliente_admin.get(RUTA)))

    assert CLAVE_SMTP not in texto
    assert CLAVE_LDAP not in texto


def test_exportar_solo_incluye_cuentas_locales(configuracion, cliente_admin):
    fabricas.crear_usuario(ROLE_USER, email='directorio@pruebas.local')
    usuario = User.query.filter_by(email='directorio@pruebas.local').one()
    usuario.auth_source = 'ldap'
    db.session.commit()

    correos = {u['email'] for u in
               _leer_zip(cliente_admin.get(RUTA))['payload']['users']}

    assert 'directorio@pruebas.local' not in correos


@pytest.mark.xfail(strict=True, reason='SEG-17 / FNC-010: el respaldo '
                   'incluye los password_hash de las cuentas locales')
def test_exportar_no_incluye_hashes_de_contrasena(configuracion,
                                                  cliente_admin):
    usuarios = _leer_zip(cliente_admin.get(RUTA))['payload']['users']

    assert all(not u.get('password_hash') for u in usuarios)


# --------------------------------------------------------------------------- #
# Importar
# --------------------------------------------------------------------------- #

def test_exportar_e_importar_restaura_la_configuracion(configuracion,
                                                       cliente_admin):
    paquete = cliente_admin.get(RUTA).data
    for modelo in (SystemConfig, AuthConfig, SMTPConfig, NotificationTemplate):
        modelo.query.delete()
    User.query.filter_by(email='local@pruebas.local').delete()
    db.session.commit()

    respuesta = _importar(cliente_admin, paquete)

    assert respuesta.status_code == 200
    restaurado = respuesta.get_json()['restored']
    assert {'portal', 'directorio', 'correo'} <= set(restaurado)
    assert SystemConfig.query.one().portal_name == 'Portal respaldado'
    assert AuthConfig.query.one().ldap_host == HOST_LDAP_FICTICIO
    assert SMTPConfig.query.one().port == 2525
    assert NotificationTemplate.query.filter_by(slug='aviso').one().body == \
        'Cuerpo'
    restaurada = User.query.filter_by(email='local@pruebas.local').one()
    assert restaurada.check_password(CONTRASENA_FICTICIA)
    assert AuditLog.query.filter_by(action='IMPORTAR CONFIGURACIÓN').count() == 1


def test_importar_no_borra_las_contrasenas_guardadas(configuracion,
                                                     cliente_admin):
    _importar(cliente_admin, cliente_admin.get(RUTA).data)

    assert SMTPConfig.query.one().password == CLAVE_SMTP
    assert AuthConfig.query.one().ldap_pass == CLAVE_LDAP


def test_importar_no_sobrescribe_usuarios_existentes(configuracion,
                                                     cliente_admin):
    carga = {'payload': {'users': [{'email': 'LOCAL@pruebas.local',
                                    'nombre': 'Intruso',
                                    'role': ROLE_ADMIN}]}}

    respuesta = _importar(cliente_admin, _zip(json.dumps(carga)))

    assert respuesta.status_code == 200
    existente = User.query.filter_by(email='local@pruebas.local').one()
    assert (existente.nombre, existente.role) != ('Intruso', ROLE_ADMIN)
    assert existente.check_password(CONTRASENA_FICTICIA)


@pytest.mark.xfail(strict=True, reason='SEG-17 / FNC-010: la importación '
                   'restaura cuentas con rol administrador sin confirmación')
def test_importar_no_crea_superadmins(app, cliente_admin):
    carga = {'payload': {'users': [{'email': 'nuevo-admin@pruebas.local',
                                    'role': ROLE_ADMIN}]}}

    _importar(cliente_admin, _zip(json.dumps(carga)))

    nuevo = User.query.filter_by(email='nuevo-admin@pruebas.local').first()
    assert nuevo is None or nuevo.role != ROLE_ADMIN


@pytest.mark.parametrize('datos', [
    b'esto no es un zip',
    _zip('{}', nombre='otro.json'),
    _zip('{json roto'),
], ids=['no_zip', 'sin_nexus_config', 'json_invalido'])
def test_paquete_invalido_da_400_sin_cambios(configuracion, cliente_admin,
                                             datos):
    respuesta = _importar(cliente_admin, datos)

    assert respuesta.status_code == 400
    assert respuesta.get_json()['status'] == 'error'
    assert SystemConfig.query.one().portal_name == 'Portal respaldado'


def test_sin_archivo_da_400(app, cliente_admin):
    respuesta = cliente_admin.post(RUTA, data={},
                                   content_type='multipart/form-data')

    assert respuesta.status_code == 400
