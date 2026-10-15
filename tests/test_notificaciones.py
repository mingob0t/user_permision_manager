"""Notificaciones: correo por plantilla, configuración SMTP y avisos in-app (FNC-023).

SMTP se simula con `tests/smtp_falso.py`: no hay red. Los defectos conocidos se
prueban con el comportamiento correcto y `xfail(strict=True)` con su tarea.
"""

import smtplib

import pytest

from app import db
from app.authz import ROLE_USER
from app.modules.auth.models import User
from app.modules.notifications import services
from app.modules.notifications.models import (InAppNotification,
                                              NotificationTemplate, SMTPConfig)
from tests.directorio_falso import instalar_directorio
from tests.matriz_proteccion import (CONTRASENA_FICTICIA, CORREO_SSO_FICTICIO,
                                     HOST_SMTP_FICTICIO)
from tests.peticiones_auth import iniciar_sesion_api, usuario_en_sesion
from tests.smtp_falso import instalar_smtp

A = '/api/v1'
SLUG = 'usuario_creado'
DESTINO = 'destino@pruebas.local'
REMITENTE = 'Portal de prueba'
HOST_SMTP_ENTORNO = 'smtp-entorno.pruebas.invalid'
USUARIO_SMTP = 'cuenta-smtp@pruebas.local'


# --------------------------------------------------------------------------- #
# Preparación
# --------------------------------------------------------------------------- #

@pytest.fixture
def correo(app, monkeypatch):
    """SMTP simulado y notificaciones activadas (conftest las apaga)."""
    monkeypatch.setenv('ENABLE_NOTIFICATIONS', 'true')
    return instalar_smtp(monkeypatch)


def _smtp_en_bd(servidor=HOST_SMTP_FICTICIO, **campos):
    datos = {'server': servidor, 'port': 587, 'encryption': 'starttls',
             'auth_enabled': False, 'sender_name': REMITENTE}
    datos.update(campos)
    db.session.add(SMTPConfig(**datos))
    db.session.commit()


def _smtp_en_entorno(monkeypatch, **variables):
    valores = {'SMTP_SERVER': HOST_SMTP_ENTORNO, 'SMTP_PORT': '465',
               'SMTP_ENCRYPTION': 'ssl'}
    valores.update(variables)
    for clave, valor in valores.items():
        monkeypatch.setenv(clave, valor)


def _plantilla(slug=SLUG, asunto='Hola {nombre}',
               cuerpo='Tu usuario es {usuario}. Entra en {url}.',
               html=False):
    db.session.add(NotificationTemplate(slug=slug, name='Bienvenida',
                                        subject=asunto, body=cuerpo,
                                        is_html=html))
    db.session.commit()


def _cuerpo(mensaje):
    parte = mensaje.get_payload()[0]
    return parte.get_payload(decode=True).decode(parte.get_content_charset())


CONTEXTO = {'nombre': 'Ana', 'usuario': 'ana@pruebas.local',
            'url': 'https://portal.pruebas.invalid'}


# --------------------------------------------------------------------------- #
# send_notification_by_slug
# --------------------------------------------------------------------------- #

def test_envia_la_plantilla_con_las_variables_reemplazadas(correo):
    _smtp_en_bd()
    _plantilla()

    resultado = services.send_notification_by_slug(SLUG, DESTINO, CONTEXTO)

    assert resultado['status'] == 'success'
    assert resultado['source'] == 'db'
    assert correo.conexiones == [('SMTP', HOST_SMTP_FICTICIO, 587)]
    [mensaje] = correo.enviados
    assert mensaje['To'] == DESTINO
    assert mensaje['Subject'] == 'Hola Ana'
    assert REMITENTE in mensaje['From']
    assert _cuerpo(mensaje) == ('Tu usuario es ana@pruebas.local. '
                                'Entra en https://portal.pruebas.invalid.')
    assert mensaje.get_payload()[0].get_content_subtype() == 'plain'


def test_variable_sin_valor_queda_tal_cual(correo):
    _smtp_en_bd()
    _plantilla(cuerpo='Hola {nombre}, {desconocida}')

    services.send_notification_by_slug(SLUG, DESTINO, {'nombre': 'Ana'})

    assert _cuerpo(correo.enviados[0]) == 'Hola Ana, {desconocida}'


def test_plantilla_html_se_envia_como_html(correo):
    _smtp_en_bd()
    _plantilla(cuerpo='<p>Hola {nombre}</p>', html=True)

    services.send_notification_by_slug(SLUG, DESTINO, {'nombre': 'Ana'})

    parte = correo.enviados[0].get_payload()[0]
    assert parte.get_content_subtype() == 'html'
    assert _cuerpo(correo.enviados[0]) == '<p>Hola Ana</p>'


def test_plantilla_html_escapa_los_valores_del_contexto(correo):
    """Regresión SEG-23 (FNC-048; antes xfail de FNC-017)."""
    _smtp_en_bd()
    _plantilla(cuerpo='<p>Hola {nombre}</p>', html=True)

    services.send_notification_by_slug(
        SLUG, DESTINO, {'nombre': '<a href="https://otro.invalid">x</a>'})

    cuerpo = _cuerpo(correo.enviados[0])
    assert '<a href' not in cuerpo
    assert '&lt;a href' in cuerpo


def test_plantilla_de_texto_no_escapa_los_valores(correo):
    _smtp_en_bd()
    _plantilla(cuerpo='Hola {nombre}')

    services.send_notification_by_slug(SLUG, DESTINO, {'nombre': 'A & <B>'})

    assert _cuerpo(correo.enviados[0]) == 'Hola A & <B>'


def test_asunto_sin_saltos_de_linea_de_los_valores(correo):
    """Regresión SEC-MAIL-01: un valor con CR/LF no agrega cabeceras."""
    _smtp_en_bd()
    _plantilla()

    services.send_notification_by_slug(
        SLUG, DESTINO, {'nombre': 'Ana\r\nBcc: otro@pruebas.invalid'})

    [mensaje] = correo.enviados
    assert mensaje['Bcc'] is None
    assert '\n' not in mensaje['Subject'] and '\r' not in mensaje['Subject']
    assert mensaje['Subject'] == 'Hola Ana Bcc: otro@pruebas.invalid'


def test_un_valor_no_inyecta_otra_variable(correo):
    """SEC-MAIL-02: la sustitución es de una pasada; `{url}` en un valor queda literal."""
    _smtp_en_bd()
    _plantilla(cuerpo='{nombre} - {url}')

    services.send_notification_by_slug(
        SLUG, DESTINO, {'nombre': '{url}', 'url': 'https://portal.pruebas.invalid'})

    assert _cuerpo(correo.enviados[0]) == '{url} - https://portal.pruebas.invalid'


def test_plantilla_inexistente_da_error_sin_enviar(correo):
    _smtp_en_bd()

    resultado = services.send_notification_by_slug('no-existe', DESTINO)

    assert resultado['status'] == 'error'
    assert 'no-existe' in resultado['message']
    assert correo.enviados == []


def test_sin_configuracion_smtp_da_error_sin_conectar(correo):
    _plantilla()

    resultado = services.send_notification_by_slug(SLUG, DESTINO, CONTEXTO)

    assert resultado == {'status': 'error',
                         'message': 'No hay configuración SMTP utilizable.'}
    assert correo.conexiones == []


@pytest.mark.parametrize('valor', ['false', 'False', '0', 'no'])
def test_notificaciones_desactivadas_no_conectan(correo, monkeypatch, valor):
    monkeypatch.setenv('ENABLE_NOTIFICATIONS', valor)
    _smtp_en_bd()
    _plantilla()

    resultado = services.send_notification_by_slug(SLUG, DESTINO, CONTEXTO)

    assert resultado['status'] == 'success'
    assert correo.conexiones == []
    assert correo.enviados == []


def test_fallo_de_smtp_devuelve_error_generico_sin_excepcion(correo):
    _smtp_en_bd()
    _plantilla()
    correo.error = smtplib.SMTPException('detalle-interno-del-servidor')

    resultado = services.send_notification_by_slug(SLUG, DESTINO, CONTEXTO)

    assert resultado == {'status': 'error',
                         'message': 'Error interno enviando notificación.'}


def test_inicia_sesion_en_smtp_si_la_autenticacion_esta_activa(correo):
    _smtp_en_bd(auth_enabled=True, username=USUARIO_SMTP,
                password=CONTRASENA_FICTICIA)
    _plantilla()

    services.send_notification_by_slug(SLUG, DESTINO, CONTEXTO)

    assert correo.logins == [(USUARIO_SMTP, CONTRASENA_FICTICIA)]


# --------------------------------------------------------------------------- #
# Un fallo de correo no impide el acceso
# --------------------------------------------------------------------------- #

@pytest.fixture
def aviso_de_alta(correo, monkeypatch):
    """Alta de usuario con aviso por correo activo y SMTP que falla."""
    monkeypatch.setenv('NOTIFY_USER_CREATED', 'true')
    monkeypatch.setenv('BASE_URL', 'https://portal.pruebas.invalid')
    _smtp_en_bd()
    _plantilla()
    correo.error = smtplib.SMTPException('servidor caído')
    return correo


def test_sso_entra_aunque_falle_el_correo_de_bienvenida(client, aviso_de_alta,
                                                        monkeypatch):
    monkeypatch.setenv('AUTHELIA_ENABLED', 'true')

    respuesta = client.post(f'{A}/auth/sso',
                            headers={'Remote-Email': CORREO_SSO_FICTICIO})

    assert respuesta.status_code == 200
    assert usuario_en_sesion(client) == CORREO_SSO_FICTICIO


def test_sso_entra_aunque_el_servicio_de_correo_lance_excepcion(
        client, aviso_de_alta, monkeypatch):
    monkeypatch.setenv('AUTHELIA_ENABLED', 'true')

    def _explota(*args, **kwargs):
        raise RuntimeError('fallo inesperado')
    monkeypatch.setattr(services, 'send_notification_by_slug', _explota)

    respuesta = client.post(f'{A}/auth/sso',
                            headers={'Remote-Email': CORREO_SSO_FICTICIO})

    assert respuesta.status_code == 200


def test_directorio_entra_aunque_falle_el_correo_de_bienvenida(
        client, aviso_de_alta, monkeypatch):
    directorio = instalar_directorio(monkeypatch)
    directorio.agregar('jperez', CONTRASENA_FICTICIA)

    respuesta = iniciar_sesion_api(client, 'jperez', CONTRASENA_FICTICIA,
                                   metodo='directory')

    assert respuesta.status_code == 200
    assert usuario_en_sesion(client) is not None


# --------------------------------------------------------------------------- #
# resolve_smtp_settings: base de datos frente a entorno
# --------------------------------------------------------------------------- #

def test_sin_bd_ni_entorno_no_hay_configuracion(app):
    assert services.resolve_smtp_settings() is None


def test_sin_bd_usa_el_entorno(app, monkeypatch):
    _smtp_en_entorno(monkeypatch)

    config = services.resolve_smtp_settings()

    assert (config.source, config.server, config.port, config.encryption) == \
        ('env', HOST_SMTP_ENTORNO, 465, 'ssl')


def test_la_bd_manda_sobre_el_entorno(app, monkeypatch):
    _smtp_en_entorno(monkeypatch)
    _smtp_en_bd()

    config = services.resolve_smtp_settings()

    assert (config.source, config.server) == ('db', HOST_SMTP_FICTICIO)


def test_smtp_force_env_ignora_la_bd(app, monkeypatch):
    _smtp_en_entorno(monkeypatch, SMTP_FORCE_ENV='true')
    _smtp_en_bd()

    config = services.resolve_smtp_settings()

    assert (config.source, config.server) == ('env', HOST_SMTP_ENTORNO)


def test_smtp_force_env_sin_servidor_no_cae_a_la_bd(app, monkeypatch):
    monkeypatch.setenv('SMTP_FORCE_ENV', 'true')
    _smtp_en_bd()

    assert services.resolve_smtp_settings() is None


def test_bd_sin_servidor_cae_al_entorno(app, monkeypatch):
    _smtp_en_entorno(monkeypatch)
    _smtp_en_bd(servidor='')

    assert services.resolve_smtp_settings().source == 'env'


@pytest.mark.parametrize('variable,valor,campo,esperado', [
    ('SMTP_PORT', 'no-numero', 'port', 587),
    ('SMTP_ENCRYPTION', 'otra', 'encryption', 'starttls'),
    ('SMTP_SENDER_NAME', '', 'sender_name', 'Nexus'),
])
def test_valores_invalidos_del_entorno_usan_el_valor_por_defecto(
        app, monkeypatch, variable, valor, campo, esperado):
    _smtp_en_entorno(monkeypatch, **{variable: valor})

    assert getattr(services.resolve_smtp_settings(), campo) == esperado


def test_autenticacion_del_entorno_se_deduce_de_usuario_y_clave(app,
                                                               monkeypatch):
    _smtp_en_entorno(monkeypatch, SMTP_USER=USUARIO_SMTP,
                     SMTP_PASSWORD=CONTRASENA_FICTICIA)
    con_clave = services.resolve_smtp_settings()
    monkeypatch.delenv('SMTP_PASSWORD')
    sin_clave = services.resolve_smtp_settings()

    assert con_clave.auth_enabled is True
    assert sin_clave.auth_enabled is False
    assert con_clave.sender_email == USUARIO_SMTP


def test_put_smtp_rechazado_con_smtp_force_env(app, cliente_admin,
                                               monkeypatch):
    _smtp_en_entorno(monkeypatch, SMTP_FORCE_ENV='true')

    respuesta = cliente_admin.put(f'{A}/smtp',
                                  json={'server': HOST_SMTP_FICTICIO})

    assert respuesta.status_code == 409
    assert SMTPConfig.query.count() == 0


def test_get_smtp_indica_el_origen_y_si_es_editable(app, cliente_admin,
                                                    monkeypatch):
    _smtp_en_entorno(monkeypatch, SMTP_FORCE_ENV='true')

    datos = cliente_admin.get(f'{A}/smtp').get_json()

    assert datos['source'] == 'env'
    assert datos['forced_by_env'] is True
    assert datos['editable'] is False


# --------------------------------------------------------------------------- #
# /api/v1/notifications: cada quien ve y borra las suyas
# --------------------------------------------------------------------------- #

def _aviso(usuario=None, titulo='Aviso'):
    services.add_in_app_notification('info', titulo, 'Mensaje de prueba',
                                     user_id=usuario.id if usuario else None)
    return InAppNotification.query.filter_by(title=titulo).one()


@pytest.fixture
def avisos(app, crear_usuario):
    """Dos usuarios con un aviso propio cada uno y un aviso global."""
    ana = crear_usuario(ROLE_USER)
    beto = crear_usuario(ROLE_USER)
    return {'ana': ana, 'beto': beto,
            'de_ana': _aviso(ana, 'De Ana').id,
            'de_beto': _aviso(beto, 'De Beto').id,
            'global': _aviso(None, 'Global').id}


def _titulos(respuesta):
    assert respuesta.status_code == 200
    return {n['title'] for n in respuesta.get_json()}


def _leida(id_aviso):
    db.session.expire_all()
    return db.session.get(InAppNotification, id_aviso).is_read


def test_add_in_app_notification_por_usuario_y_global(avisos):
    assert db.session.get(InAppNotification, avisos['de_ana']).user_id == \
        avisos['ana'].id
    assert db.session.get(InAppNotification, avisos['global']).user_id is None


def test_lista_las_propias_y_las_globales(avisos, cliente_como):
    respuesta = cliente_como(avisos['ana']).get(f'{A}/notifications')

    assert _titulos(respuesta) == {'De Ana', 'Global'}


def test_sin_preferencia_de_notificaciones_lista_vacia(avisos, cliente_como):
    avisos['ana'].pref_notifications = False
    db.session.commit()

    respuesta = cliente_como(avisos['ana']).get(f'{A}/notifications')

    assert respuesta.get_json() == []


def test_marca_leidas_solo_las_indicadas_y_propias(avisos, cliente_como):
    respuesta = cliente_como(avisos['ana']).post(
        f'{A}/notifications/read',
        json={'ids': [avisos['de_ana'], avisos['de_beto']]})

    assert respuesta.status_code == 200
    assert _leida(avisos['de_ana']) is True
    assert _leida(avisos['de_beto']) is False


def test_marcar_todas_no_toca_las_de_otro(avisos, cliente_como):
    cliente_como(avisos['ana']).post(f'{A}/notifications/read', json={})

    assert _leida(avisos['de_ana']) is True
    assert _leida(avisos['de_beto']) is False


@pytest.mark.xfail(strict=True, reason='FNC-031: POST /notifications/read '
                   'marca las globales como leídas para todos los usuarios')
def test_leer_una_global_no_la_marca_para_los_demas(avisos, cliente_como):
    cliente_como(avisos['ana']).post(f'{A}/notifications/read', json={})

    respuesta = cliente_como(avisos['beto']).get(f'{A}/notifications')

    globales = [n for n in respuesta.get_json() if n['title'] == 'Global']
    assert globales[0]['is_read'] is False


def test_borrar_elimina_solo_las_propias(avisos, cliente_como):
    respuesta = cliente_como(avisos['ana']).delete(f'{A}/notifications')

    assert respuesta.status_code == 200
    restantes = {n.title for n in InAppNotification.query.all()}
    assert restantes == {'De Beto', 'Global'}
    assert User.query.count() == 2
