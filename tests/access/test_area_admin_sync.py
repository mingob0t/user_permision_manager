"""Acceso automático de los admins a las plataformas de sus áreas (FNC-055).

P6 (dueño, 2026-10-14): nivel `usuario`, origen `admin_de_area`, para todos
los admins del área (incluido el creador); el superadmin no recibe nada; al
quitarle el área a un admin se revocan sus accesos automáticos de esa área.
"""
import pytest
from flask import g

from app import db
from app.authz import ROLE_AREA_ADMIN, ROLE_USER
from app.modules.access import services
from app.modules.access.models import PlatformAccessGrant
from app.modules.access.tipos import (ESTADO_ACTIVO, ESTADO_EN_PROCESO,
                                      ESTADO_REVOCANDO, MOTIVO_RETIRO_ADMIN,
                                      ORIGEN_ADMIN_DE_AREA, ORIGEN_SOLICITUD)
from app.modules.audit.events import Evento
from app.modules.audit.models import AuditLog
from app.modules.core.models import Platform
from app.modules.platforms.tipos import NIVEL_USUARIO, TIPO_CONECTOR, TIPO_LDAP
from tests import fabricas
from tests.access.conftest import recargar

A = '/api/v1'


@pytest.fixture
def cliente_como(cliente_como):
    """Como el común, pero olvida la cuenta de la petición anterior: las
    pruebas comparten el contexto de la app y Flask-Login la guarda en `g`."""
    def _cliente(usuario):
        g.pop('_login_user', None)
        return cliente_como(usuario)
    return _cliente


def _alta(area_id, nombre='Nómina'):
    return {'name': nombre, 'description': 'Plataforma de prueba',
            'area_id': area_id, 'integration_type': TIPO_CONECTOR}


def _automaticos(**filtros):
    return (PlatformAccessGrant.query
            .filter_by(origin=ORIGEN_ADMIN_DE_AREA, **filtros)
            .order_by(PlatformAccessGrant.id).all())


def _de(cuenta, plataforma=None):
    filtros = {'user_id': cuenta.id}
    if plataforma is not None:
        filtros['platform_id'] = plataforma.id
    return _automaticos(**filtros)


def _activar_todo(cola_falsa):
    resultados = cola_falsa.procesar()
    db.session.expire_all()
    return resultados


# --------------------------------------------------------------------------- #
# Alta de una plataforma en el área
# --------------------------------------------------------------------------- #

def test_alta_de_plataforma_otorga_a_todos_los_admins_del_area(
        escena, cliente_como, cola_falsa):
    respuesta = cliente_como(escena['admin']).post(
        f'{A}/platforms', json=_alta(escena['area'].id))

    assert respuesta.status_code == 201, respuesta.get_json()
    plataforma_id = respuesta.get_json()['platform']['id']
    accesos = _automaticos(platform_id=plataforma_id)
    assert sorted(a.user_id for a in accesos) == sorted(
        [escena['admin'].id, escena['admin2'].id])
    for acceso in accesos:
        assert (acceso.level, acceso.status, acceso.granted_by) == (
            NIVEL_USUARIO, ESTADO_EN_PROCESO, None)
        assert acceso.last_job_id is not None
    # Ni el admin de otra área, ni usuarios, ni el superadmin.
    assert not _de(escena['admin_otra'])
    assert not _de(escena['usuario'])
    assert not _de(escena['super'])


def test_alta_audita_al_admin_y_luego_al_sistema(escena, cliente_como,
                                                 cola_falsa):
    cliente_como(escena['admin']).post(f'{A}/platforms',
                                       json=_alta(escena['area'].id))

    registros = AuditLog.query.order_by(AuditLog.id).all()
    acciones = [r.action for r in registros]
    creada = acciones.index(Evento.PLATAFORMA_CREADA.value)
    otorgados = [r for r in registros
                 if r.action == Evento.ACCESO_OTORGADO.value]
    assert len(otorgados) == 2
    assert all(registros.index(r) > creada for r in otorgados)
    assert registros[creada].detail.startswith(
        f'admin {escena["admin"].email} dio de alta la plataforma')
    assert all(r.user == 'sistema' for r in otorgados)
    assert {r.detail for r in otorgados} == {
        f'sistema dio permisos de acceso a admin {escena["admin"].email}',
        f'sistema dio permisos de acceso a admin {escena["admin2"].email}'}


def test_alta_por_el_superadmin_otorga_a_los_admins_y_no_a_el(
        escena, cliente_como, cola_falsa):
    respuesta = cliente_como(escena['super']).post(
        f'{A}/platforms', json=_alta(escena['area'].id))

    assert respuesta.status_code == 201
    assert len(_automaticos()) == 2
    assert not _de(escena['super'])


def test_un_admin_inactivo_no_recibe_acceso_automatico(escena, cliente_como,
                                                      cola_falsa):
    escena['admin2'].is_active = False
    db.session.commit()

    cliente_como(escena['admin']).post(f'{A}/platforms',
                                       json=_alta(escena['area'].id))

    assert [a.user_id for a in _automaticos()] == [escena['admin'].id]


def test_si_el_otorgamiento_falla_no_se_crea_la_plataforma(
        escena, cliente_como, cola_falsa, monkeypatch):
    def _falla(*args, **kwargs):
        raise RuntimeError('cola caída')
    monkeypatch.setattr(services.queue, 'encolar', _falla)

    cliente = cliente_como(escena['admin'])
    cliente.application.config['PROPAGATE_EXCEPTIONS'] = False
    respuesta = cliente.post(f'{A}/platforms', json=_alta(escena['area'].id))

    assert respuesta.status_code == 500
    db.session.rollback()
    assert not PlatformAccessGrant.query.count()
    assert not AuditLog.query.filter_by(
        action=Evento.PLATAFORMA_CREADA.value).count()


def test_plataforma_ldap_sin_grupo_de_usuario_no_genera_acceso(escena):
    from app.modules.access.area_admin_sync import sincronizar_plataforma
    heredada = fabricas.crear_plataforma(escena['area'], 'Heredada',
                                         integration_type=TIPO_LDAP)

    sincronizar_plataforma(heredada)
    db.session.commit()

    assert not _automaticos(platform_id=heredada.id)


# --------------------------------------------------------------------------- #
# Asignación de un admin a un área
# --------------------------------------------------------------------------- #

@pytest.fixture
def area_con_tres(escena):
    area = fabricas.crear_area('Compras')
    for n in range(3):
        fabricas.crear_plataforma(area, f'Compras {n}',
                                  integration_type=TIPO_CONECTOR)
    return area


def test_asignar_un_admin_a_un_area_con_tres_plataformas_da_tres_accesos(
        escena, cliente_como, cola_falsa, area_con_tres):
    nuevo = fabricas.crear_usuario(ROLE_AREA_ADMIN)

    respuesta = cliente_como(escena['super']).put(
        f'{A}/users/{nuevo.id}/managed-areas',
        json={'area_ids': [area_con_tres.id]})

    assert respuesta.status_code == 200, respuesta.get_json()
    accesos = _de(nuevo)
    assert len(accesos) == 3
    assert {a.platform.area_id for a in accesos} == {area_con_tres.id}
    assert all(a.level == NIVEL_USUARIO for a in accesos)


def test_repetir_la_asignacion_no_duplica(escena, cliente_como, cola_falsa,
                                          proveedor_simulado, area_con_tres):
    nuevo = fabricas.crear_usuario(ROLE_AREA_ADMIN)
    cliente = cliente_como(escena['super'])
    cuerpo = {'area_ids': [area_con_tres.id]}

    cliente.put(f'{A}/users/{nuevo.id}/managed-areas', json=cuerpo)
    _activar_todo(cola_falsa)
    cliente.put(f'{A}/users/{nuevo.id}/managed-areas', json=cuerpo)

    accesos = _de(nuevo)
    assert len(accesos) == 3
    assert {a.status for a in accesos} == {ESTADO_ACTIVO}
    assert not cola_falsa.mensajes


def test_sincronizar_dos_veces_no_duplica(escena, cola_falsa):
    from app.modules.access.area_admin_sync import sincronizar_plataforma

    sincronizar_plataforma(escena['plataforma'])
    sincronizar_plataforma(escena['plataforma'])
    db.session.commit()

    assert len(_automaticos(platform_id=escena['plataforma'].id)) == 2


def test_admin_con_acceso_por_solicitud_no_recibe_otro(escena, cola_falsa):
    from app.modules.access.area_admin_sync import sincronizar_cuenta
    usuario = fabricas.crear_usuario(ROLE_USER, areas=[escena['area']])
    services.otorgar(usuario, escena['plataforma'], NIVEL_USUARIO,
                     ORIGEN_SOLICITUD, actor=escena['super'], request_id=9)
    usuario.role = ROLE_AREA_ADMIN
    usuario.managed_areas = [escena['area']]
    db.session.commit()

    sincronizar_cuenta(usuario, [escena['area']])
    db.session.commit()

    assert not _de(usuario)


# --------------------------------------------------------------------------- #
# Retiro de un admin del área
# --------------------------------------------------------------------------- #

@pytest.fixture
def con_automaticos(escena, cliente_como, cola_falsa, proveedor_simulado):
    """Plataforma nueva en el área: los dos admins con acceso activo."""
    respuesta = cliente_como(escena['admin']).post(
        f'{A}/platforms', json=_alta(escena['area'].id))
    _activar_todo(cola_falsa)
    return db.session.get(Platform, respuesta.get_json()['platform']['id'])


def test_quitar_el_area_a_un_admin_revoca_sus_automaticos(
        escena, cliente_como, cola_falsa, con_automaticos):
    respuesta = cliente_como(escena['super']).put(
        f'{A}/users/{escena["admin2"].id}/managed-areas',
        json={'area_ids': []})

    assert respuesta.status_code == 200
    retirado = _de(escena['admin2'], con_automaticos)[0]
    assert (retirado.status, retirado.revoke_reason, retirado.revoked_by) == (
        ESTADO_REVOCANDO, MOTIVO_RETIRO_ADMIN, None)
    # El otro admin conserva el suyo.
    assert _de(escena['admin'], con_automaticos)[0].status == ESTADO_ACTIVO
    revocado = AuditLog.query.filter_by(
        action=Evento.ACCESO_REVOCADO.value).one()
    assert revocado.user == 'sistema'


def test_quitar_el_area_no_toca_accesos_por_solicitud(escena, cliente_como,
                                                     cola_falsa,
                                                     proveedor_simulado):
    escena['admin2'].areas = [escena['area']]
    db.session.commit()
    por_solicitud = services.otorgar(
        escena['usuario'], escena['plataforma'], NIVEL_USUARIO,
        ORIGEN_SOLICITUD, actor=escena['super'], request_id=3)
    db.session.commit()
    _activar_todo(cola_falsa)

    cliente_como(escena['super']).put(
        f'{A}/users/{escena["admin2"].id}/managed-areas',
        json={'area_ids': []})

    assert recargar(por_solicitud.id).status == ESTADO_ACTIVO


def test_degradar_a_usuario_revoca_sus_automaticos(escena, cliente_como,
                                                  cola_falsa,
                                                  con_automaticos):
    respuesta = cliente_como(escena['super']).put(
        f'{A}/users/{escena["admin2"].id}', json={'role': ROLE_USER})

    assert respuesta.status_code == 200
    assert _de(escena['admin2'], con_automaticos)[0].status == \
        ESTADO_REVOCANDO


def test_acceso_en_proceso_de_un_admin_retirado_se_revoca_al_confirmarse(
        escena, cliente_como, cola_falsa, proveedor_simulado):
    cliente_como(escena['admin']).post(f'{A}/platforms',
                                       json=_alta(escena['area'].id))
    cliente_como(escena['super']).put(
        f'{A}/users/{escena["admin2"].id}/managed-areas',
        json={'area_ids': []})
    en_proceso, = _de(escena['admin2'])
    assert en_proceso.status == ESTADO_EN_PROCESO

    _activar_todo(cola_falsa)  # otorgar confirmado → el sistema lo revoca

    acceso = recargar(en_proceso.id)
    assert (acceso.status, acceso.revoke_reason) == (ESTADO_REVOCANDO,
                                                     MOTIVO_RETIRO_ADMIN)
    _activar_todo(cola_falsa)
    assert recargar(en_proceso.id).status == 'revocado'
    assert _de(escena['admin'])[0].status == ESTADO_ACTIVO


def test_revocacion_manual_del_superadmin_no_se_deshace_al_confirmarse(
        escena, cola_falsa, proveedor_simulado, con_automaticos):
    acceso = _de(escena['admin2'], con_automaticos)[0]
    services.revocar(acceso, actor=escena['super'])
    db.session.commit()

    _activar_todo(cola_falsa)

    assert recargar(acceso.id).status == 'revocado'
    assert len(_de(escena['admin2'], con_automaticos)) == 1


# --------------------------------------------------------------------------- #
# Cambio de área de una plataforma
# --------------------------------------------------------------------------- #

def test_mover_la_plataforma_cambia_los_automaticos_de_area(
        escena, cliente_como, cola_falsa, con_automaticos):
    respuesta = cliente_como(escena['super']).put(
        f'{A}/platforms/{con_automaticos.id}',
        json={'area_id': escena['otra'].id})

    assert respuesta.status_code == 200, respuesta.get_json()
    for admin in ('admin', 'admin2'):
        assert _de(escena[admin], con_automaticos)[0].status == \
            ESTADO_REVOCANDO
    nuevo, = _de(escena['admin_otra'], con_automaticos)
    assert (nuevo.status, nuevo.level) == (ESTADO_EN_PROCESO, NIVEL_USUARIO)


def test_mover_con_accesos_por_solicitud_sigue_dando_409(escena, cliente_como,
                                                         cola_falsa):
    services.otorgar(escena['usuario'], escena['plataforma'], NIVEL_USUARIO,
                     ORIGEN_SOLICITUD, actor=escena['super'], request_id=4)
    db.session.commit()

    respuesta = cliente_como(escena['super']).put(
        f'{A}/platforms/{escena["plataforma"].id}',
        json={'area_id': escena['otra'].id})

    assert respuesta.status_code == 409
    assert respuesta.get_json()['code'] == 'plataforma_con_accesos'



def test_completar_la_integracion_de_una_heredada_otorga_a_los_admins(
        escena, cliente_como, cola_falsa):
    heredada = fabricas.crear_plataforma(escena['area'], 'Heredada',
                                         integration_type=TIPO_LDAP)

    respuesta = cliente_como(escena['super']).put(
        f'{A}/platforms/{heredada.id}',
        json={'integration_type': TIPO_CONECTOR})

    assert respuesta.status_code == 200, respuesta.get_json()
    assert len(_automaticos(platform_id=heredada.id)) == 2
