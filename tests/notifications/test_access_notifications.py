"""Avisos por correo del gestor de accesos (FNC-048).

SMTP simulado (`tests/smtp_falso.py`) y las plantillas reales de la migración
`0003`. Destinatarios, escape, preferencia, interruptor y fallo de SMTP.
"""

import re
import smtplib

import pytest

from app import db
from app.authz import ROLE_ADMIN, ROLE_AREA_ADMIN, ROLE_USER
from app.modules.audit.events import ACTOR_SISTEMA, Evento
from app.modules.audit.models import AuditLog
from app.modules.notifications import access_notifications as avisos
from app.modules.notifications import services
from app.modules.notifications.models import SMTPConfig
from tests.matriz_proteccion import HOST_SMTP_FICTICIO
from tests.notifications.plantillas_migracion import (PLANTILLAS,
                                                      cargar_plantillas)
from tests.smtp_falso import instalar_smtp

URL_PORTAL = 'https://portal.pruebas.invalid'
JUSTIFICACION = 'Necesito el acceso para el cierre mensual.'
MOTIVO = 'No corresponde a tus funciones actuales.'


# --------------------------------------------------------------------------- #
# Preparación
# --------------------------------------------------------------------------- #

@pytest.fixture
def correo(app, monkeypatch):
    monkeypatch.setenv('ENABLE_NOTIFICATIONS', 'true')
    monkeypatch.setenv('BASE_URL', URL_PORTAL)
    db.session.add(SMTPConfig(server=HOST_SMTP_FICTICIO, port=587,
                              encryption='starttls', auth_enabled=False,
                              sender_name='Portal de prueba'))
    db.session.commit()
    cargar_plantillas()
    return instalar_smtp(monkeypatch)


@pytest.fixture
def escenario(app, crear_area, crear_plataforma, crear_usuario):
    """Área con dos admins, un admin de otra área, superadmin y solicitante."""
    finanzas = crear_area('Finanzas')
    otra = crear_area('Otra')
    plataforma = crear_plataforma(finanzas, 'Contabilidad')
    datos = {
        'area': finanzas,
        'plataforma': plataforma,
        'admin1': crear_usuario(ROLE_AREA_ADMIN, 'admin1@pruebas.local',
                                areas_administradas=[finanzas]),
        'admin2': crear_usuario(ROLE_AREA_ADMIN, 'admin2@pruebas.local',
                                areas_administradas=[finanzas]),
        'ajeno': crear_usuario(ROLE_AREA_ADMIN, 'ajeno@pruebas.local',
                               areas_administradas=[otra]),
        'super': crear_usuario(ROLE_ADMIN, 'super@pruebas.local'),
        'ana': crear_usuario(ROLE_USER, 'ana@pruebas.local', areas=[finanzas]),
    }
    datos['ana'].nombre = 'Ana Ruiz'
    db.session.commit()
    return datos


def _para(mensaje):
    return sorted(d.strip() for d in mensaje['To'].split(','))


def _cuerpo(mensaje):
    parte = mensaje.get_payload()[0]
    return parte.get_payload(decode=True).decode(parte.get_content_charset())


def _fallos():
    return AuditLog.query.filter_by(
        action=Evento.NOTIFICACION_FALLIDA.value).all()


# --------------------------------------------------------------------------- #
# Plantillas
# --------------------------------------------------------------------------- #

def test_cada_plantilla_usa_solo_claves_de_su_lista_blanca():
    assert {p['slug'] for p in PLANTILLAS} == set(avisos.CLAVES_POR_PLANTILLA)
    for plantilla in PLANTILLAS:
        usadas = set(re.findall(r'\{(\w+)\}',
                                plantilla['subject'] + plantilla['body']))
        assert usadas <= set(avisos.CLAVES_POR_PLANTILLA[plantilla['slug']]), \
            plantilla['slug']


# --------------------------------------------------------------------------- #
# Destinatarios por evento
# --------------------------------------------------------------------------- #

def test_solicitud_nueva_va_a_los_admins_del_area(correo, escenario):
    e = escenario

    resultado = avisos.notificar_solicitud_nueva(
        e['ana'], e['plataforma'], 'usuario', JUSTIFICACION)

    assert resultado == {'status': 'success', 'recipients': 2}
    [mensaje] = correo.enviados
    assert _para(mensaje) == ['admin1@pruebas.local', 'admin2@pruebas.local']
    assert mensaje['Subject'] == 'Nueva solicitud de acceso a Contabilidad'
    cuerpo = _cuerpo(mensaje)
    assert 'Ana Ruiz' in cuerpo and JUSTIFICACION in cuerpo
    assert 'Finanzas' in cuerpo and URL_PORTAL in cuerpo


def test_solicitud_nueva_omite_inactivos_sin_preferencia_y_otro_rol(
        correo, escenario):
    e = escenario
    e['admin1'].is_active = False
    e['admin2'].pref_email_notifications = False
    db.session.commit()

    resultado = avisos.notificar_solicitud_nueva(
        e['ana'], e['plataforma'], 'usuario', JUSTIFICACION)

    assert resultado == {'status': 'skipped', 'recipients': 0}
    assert correo.enviados == []


def test_solicitud_nueva_no_va_a_un_usuario_degradado_que_sigue_en_area_admins(
        correo, escenario):
    e = escenario
    e['admin2'].role = ROLE_USER
    db.session.commit()

    avisos.notificar_solicitud_nueva(e['ana'], e['plataforma'], 'admin',
                                     JUSTIFICACION)

    assert _para(correo.enviados[0]) == ['admin1@pruebas.local']


@pytest.mark.parametrize('funcion,extra,asunto', [
    (avisos.notificar_solicitud_aprobada, (),
     'Tu solicitud de acceso a Contabilidad fue aprobada'),
    (avisos.notificar_solicitud_rechazada, (MOTIVO,),
     'Tu solicitud de acceso a Contabilidad fue rechazada'),
])
def test_decision_va_solo_al_solicitante(correo, escenario, funcion, extra,
                                         asunto):
    e = escenario

    resultado = funcion(e['ana'], e['plataforma'], 'usuario', *extra)

    assert resultado == {'status': 'success', 'recipients': 1}
    [mensaje] = correo.enviados
    assert _para(mensaje) == ['ana@pruebas.local']
    assert mensaje['Subject'] == asunto


def test_rechazo_incluye_el_motivo(correo, escenario):
    e = escenario

    avisos.notificar_solicitud_rechazada(e['ana'], e['plataforma'], 'usuario',
                                         MOTIVO)

    assert MOTIVO in _cuerpo(correo.enviados[0])


def test_decision_respeta_la_preferencia_del_solicitante(correo, escenario):
    e = escenario
    e['ana'].pref_email_notifications = False
    db.session.commit()

    resultado = avisos.notificar_solicitud_aprobada(e['ana'], e['plataforma'],
                                                    'usuario')

    assert resultado['status'] == 'skipped'
    assert correo.enviados == []


def test_fallo_de_aprovisionamiento_va_a_admins_del_area_y_superadmin(
        correo, escenario):
    """P10; no depende de `pref_email_notifications` (contrato, Por confirmar)."""
    e = escenario
    e['admin1'].pref_email_notifications = False
    e['super'].pref_email_notifications = False
    db.session.commit()

    resultado = avisos.notificar_aprovisionamiento_fallido(
        e['ana'], e['plataforma'], 'usuario', avisos.OPERACION_OTORGAR)

    assert resultado == {'status': 'success', 'recipients': 3}
    [mensaje] = correo.enviados
    assert _para(mensaje) == ['admin1@pruebas.local', 'admin2@pruebas.local',
                              'super@pruebas.local']
    assert mensaje['Subject'] == \
        'Fallo de aprovisionamiento (otorgar) en Contabilidad'
    assert 'ana@pruebas.local' in _cuerpo(mensaje)


def test_fallo_de_aprovisionamiento_rechaza_operacion_desconocida(escenario):
    with pytest.raises(ValueError):
        avisos.notificar_aprovisionamiento_fallido(
            escenario['ana'], escenario['plataforma'], 'usuario', 'borrar')


def test_correo_invalido_en_la_bd_se_omite(correo, escenario):
    e = escenario
    e['admin2'].email = 'admin2@pruebas.local\r\nBcc: x@pruebas.invalid'
    db.session.commit()

    avisos.notificar_solicitud_nueva(e['ana'], e['plataforma'], 'usuario',
                                     JUSTIFICACION)

    [mensaje] = correo.enviados
    assert _para(mensaje) == ['admin1@pruebas.local']
    assert mensaje['Bcc'] is None


# --------------------------------------------------------------------------- #
# Escape (regresión SEG-23)
# --------------------------------------------------------------------------- #

def test_script_en_la_justificacion_llega_escapado(correo, escenario):
    e = escenario
    maliciosa = '<script>alert(1)</script><a href="https://otro.invalid">x</a>'

    avisos.notificar_solicitud_nueva(e['ana'], e['plataforma'], 'usuario',
                                     maliciosa)

    cuerpo = _cuerpo(correo.enviados[0])
    assert '<script>' not in cuerpo and '<a href' not in cuerpo
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in cuerpo
    assert correo.enviados[0].get_payload()[0].get_content_subtype() == 'html'


def test_nombre_con_salto_de_linea_no_agrega_cabeceras(correo, escenario):
    e = escenario
    e['plataforma'].name = 'Conta\r\nBcc: x@pruebas.invalid'
    db.session.commit()

    avisos.notificar_solicitud_aprobada(e['ana'], e['plataforma'], 'usuario')

    [mensaje] = correo.enviados
    assert mensaje['Bcc'] is None
    assert '\n' not in mensaje['Subject']


def test_el_enlace_sale_de_base_url_y_no_del_host(correo, escenario,
                                                  monkeypatch):
    monkeypatch.delenv('BASE_URL')
    e = escenario

    avisos.notificar_solicitud_aprobada(e['ana'], e['plataforma'], 'usuario')

    assert 'http' not in _cuerpo(correo.enviados[0])


# --------------------------------------------------------------------------- #
# Interruptores y fallos
# --------------------------------------------------------------------------- #

def test_interruptor_del_modulo_apagado_no_envia(correo, escenario,
                                                 monkeypatch):
    monkeypatch.setenv(avisos.VARIABLE_INTERRUPTOR, 'false')
    e = escenario

    resultado = avisos.notificar_solicitud_nueva(
        e['ana'], e['plataforma'], 'usuario', JUSTIFICACION)

    assert resultado['status'] == 'skipped'
    assert correo.conexiones == []


def test_smtp_caido_no_lanza_y_queda_en_auditoria(correo, escenario):
    e = escenario
    correo.error = smtplib.SMTPException('servidor caído')

    resultado = avisos.notificar_solicitud_nueva(
        e['ana'], e['plataforma'], 'usuario', JUSTIFICACION)

    assert resultado == {'status': 'error', 'recipients': 2}
    [registro] = _fallos()
    assert registro.user == ACTOR_SISTEMA
    assert registro.status == 'error'
    assert registro.target == avisos.SLUG_SOLICITUD_NUEVA
    assert (registro.area_id, registro.platform_id, registro.target_user_id) \
        == (e['area'].id, e['plataforma'].id, e['ana'].id)
    assert 'servidor caído' not in (registro.detail or '')


def test_excepcion_inesperada_del_servicio_no_se_propaga(correo, escenario,
                                                         monkeypatch):
    def _explota(*args, **kwargs):
        raise RuntimeError('fallo inesperado')
    monkeypatch.setattr(services, 'send_notification_by_slug', _explota)
    e = escenario

    resultado = avisos.notificar_aprovisionamiento_fallido(
        e['ana'], e['plataforma'], 'admin', avisos.OPERACION_REVOCAR)

    assert resultado['status'] == 'error'
    assert len(_fallos()) == 1


def test_operacion_de_negocio_conserva_su_commit_con_smtp_caido(correo,
                                                                escenario):
    """El aviso va después del commit: el cambio de negocio persiste."""
    e = escenario
    correo.error = smtplib.SMTPException('servidor caído')
    e['ana'].nombre = 'Ana Ruiz Cambiada'
    db.session.commit()

    avisos.notificar_solicitud_aprobada(e['ana'], e['plataforma'], 'usuario')

    db.session.expire_all()
    assert db.session.get(type(e['ana']), e['ana'].id).nombre == \
        'Ana Ruiz Cambiada'
    assert len(_fallos()) == 1


def test_sin_destinatarios_no_conecta_ni_audita(correo, crear_area,
                                                crear_plataforma,
                                                crear_usuario):
    area = crear_area('Sola')
    plataforma = crear_plataforma(area)
    solicitante = crear_usuario(ROLE_USER, areas=[area])

    resultado = avisos.notificar_solicitud_nueva(solicitante, plataforma,
                                                 'usuario', JUSTIFICACION)

    assert resultado == {'status': 'skipped', 'recipients': 0}
    assert correo.conexiones == []
    assert _fallos() == []
