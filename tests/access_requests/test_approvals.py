"""Bandeja, aprobar y rechazar (FNC-057, contrato `solicitudes.md` 1.1)."""
import pytest
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError

from app import db
from app.modules.access.errores import ErrorDeAcceso
from app.modules.access.models import PlatformAccessGrant
from app.modules.access.tipos import (ESTADO_ACTIVO, ESTADO_EN_PROCESO,
                                      ESTADO_REVOCANDO, ORIGEN_SOLICITUD)
from app.modules.access_requests import api as api_solicitudes
from app.modules.access_requests import approvals
from app.modules.access_requests.models import PlatformAccessRequest
from app.modules.access_requests.tipos import (
    ACCESS_REQUEST_REJECTION_MIN_LENGTH, ESTADO_APROBADA, ESTADO_PENDIENTE,
    ESTADO_RECHAZADA, LARGO_TEXTO)
from app.modules.audit.models import AuditLog
from app.modules.platforms.tipos import TIPO_LDAP
from app.modules.provisioning import queue
from app.modules.provisioning.models import ProvisioningJob
from app.modules.provisioning.reloj import ahora
from tests import fabricas
from tests.access_requests.conftest import RUTA, cambiar_de_actor, dar_acceso
from tests.provisioning.conftest import ColaFalsa

BANDEJA = f'{RUTA}/inbox'
MOTIVO = 'Usa el reporte compartido del área.'


@pytest.fixture
def cola_falsa(monkeypatch):
    falsa = ColaFalsa()
    monkeypatch.setattr(queue, 'cola', lambda conexion=None, **_: falsa)
    return falsa


@pytest.fixture
def avisos(monkeypatch):
    """Registra los avisos al solicitante en lugar de enviarlos."""
    enviados = []
    monkeypatch.setattr(api_solicitudes, 'notificar_solicitud_aprobada',
                        lambda *a: enviados.append(('aprobada', a)))
    monkeypatch.setattr(api_solicitudes, 'notificar_solicitud_rechazada',
                        lambda *a: enviados.append(('rechazada', a)))
    return enviados


def pendiente(usuario, plataforma, nivel='usuario', current_level=None,
              creada=None):
    solicitud = PlatformAccessRequest(
        user_id=usuario.id, platform_id=plataforma.id, level=nivel,
        status=ESTADO_PENDIENTE, current_level=current_level,
        created_at=creada or ahora())
    solicitud.sincronizar_slot()
    db.session.add(solicitud)
    db.session.commit()
    return solicitud


def aprobar(cliente, solicitud_id, **kwargs):
    kwargs.setdefault('json', {})
    return cliente.post(f'{RUTA}/{solicitud_id}/approve', **kwargs)


def rechazar(cliente, solicitud_id, motivo=MOTIVO, **kwargs):
    kwargs.setdefault('json', {'reason': motivo})
    return cliente.post(f'{RUTA}/{solicitud_id}/reject', **kwargs)


def _codigo(respuesta):
    return respuesta.status_code, (respuesta.get_json() or {}).get('code')


def recargar(solicitud_id):
    db.session.expire_all()
    return db.session.get(PlatformAccessRequest, solicitud_id)


def _sigue_pendiente(solicitud_id):
    registro = recargar(solicitud_id)
    assert registro.status == ESTADO_PENDIENTE
    assert registro.decided_by is None and registro.decided_at is None
    assert registro.slot_pendiente is not None
    assert PlatformAccessGrant.query.filter_by(
        request_id=solicitud_id).count() == 0
    assert AuditLog.query.filter(AuditLog.action.in_(
        ['solicitud_aprobada', 'solicitud_rechazada'])).count() == 0


def _ids(respuesta):
    assert respuesta.status_code == 200, respuesta.get_json()
    return [s['id'] for s in respuesta.get_json()['items']]


# --------------------------------------------------------------------------- #
# GET /access-requests/inbox
# --------------------------------------------------------------------------- #

def test_usuario_no_ve_la_bandeja(escena, cliente_como):
    respuesta = cliente_como(escena['usuario']).get(BANDEJA)

    assert respuesta.status_code == 403


def test_admin_ve_solo_las_de_sus_areas(escena, cliente_como):
    propia_area = pendiente(escena['usuario'], escena['plataforma'])
    pendiente(escena['ajeno'], escena['de_otra'])

    respuesta = cliente_como(escena['admin']).get(BANDEJA)

    assert _ids(respuesta) == [propia_area.id]
    cuerpo = respuesta.get_json()
    assert (cuerpo['page'], cuerpo['per_page'], cuerpo['total']) == (1, 25, 1)
    assert cuerpo['items'][0]['requester']['email'] == 'ana@pruebas.local'


def test_admin_no_ve_solicitudes_de_otro_admin(escena, cliente_como):
    """SEC-AUTHZ-06: un admin no otorga a otro admin; solo el superadmin."""
    de_admin = pendiente(escena['admin_otra'], escena['plataforma'])

    assert _ids(cliente_como(escena['admin']).get(BANDEJA)) == []
    cambiar_de_actor()
    assert _ids(cliente_como(escena['super']).get(BANDEJA)) == [de_admin.id]


def test_nadie_ve_su_propia_solicitud_en_la_bandeja(escena, cliente_como):
    """P12: admin de Ventas con una solicitud propia en Finanzas."""
    admin_ventas = escena['admin_otra']
    pendiente(admin_ventas, escena['plataforma'])

    assert _ids(cliente_como(admin_ventas).get(BANDEJA)) == []


def test_superadmin_ve_todas_la_mas_antigua_primero(escena, cliente_como):
    from datetime import timedelta
    reciente = pendiente(escena['usuario'], escena['plataforma'])
    antigua = pendiente(escena['ajeno'], escena['de_otra'],
                        creada=ahora() - timedelta(hours=1))

    respuesta = cliente_como(escena['super']).get(BANDEJA)

    assert _ids(respuesta) == [antigua.id, reciente.id]


def test_por_defecto_solo_pendientes_y_filtro_por_estado(escena, cliente_como):
    decidida = pendiente(escena['usuario'], escena['plataforma'])
    decidida.status = ESTADO_RECHAZADA
    decidida.rejection_reason = MOTIVO
    decidida.sincronizar_slot()
    db.session.commit()
    abierta = pendiente(escena['usuario'], escena['plataforma'])
    cliente = cliente_como(escena['admin'])

    assert _ids(cliente.get(BANDEJA)) == [abierta.id]
    assert _ids(cliente.get(f'{BANDEJA}?status=rechazada')) == [decidida.id]


def test_filtro_por_area_fuera_de_alcance_lista_vacia(escena, cliente_como):
    pendiente(escena['ajeno'], escena['de_otra'])
    propia = pendiente(escena['usuario'], escena['plataforma'])
    cliente = cliente_como(escena['admin'])

    assert _ids(cliente.get(f"{BANDEJA}?area_id={escena['otra'].id}")) == []
    assert _ids(cliente.get(
        f"{BANDEJA}?area_id={escena['area'].id}")) == [propia.id]
    assert _ids(cliente.get(
        f"{BANDEJA}?platform_id={escena['plataforma'].id}")) == [propia.id]


@pytest.mark.parametrize('consulta', ['status=otro', 'area_id=x',
                                      'platform_id=1.5', 'per_page=0',
                                      'page=-1'])
def test_parametro_invalido_400(escena, cliente_como, consulta):
    respuesta = cliente_como(escena['admin']).get(f'{BANDEJA}?{consulta}')

    assert _codigo(respuesta) == (400, 'parametro_invalido')


# --------------------------------------------------------------------------- #
# POST /access-requests/<id>/approve
# --------------------------------------------------------------------------- #

def test_aprobar_crea_acceso_en_proceso_trabajo_auditoria_y_aviso(
        escena, cliente_como, cola_falsa, avisos):
    solicitud = pendiente(escena['usuario'], escena['plataforma'])

    respuesta = aprobar(cliente_como(escena['admin']), solicitud.id)

    assert respuesta.status_code == 200, respuesta.get_json()
    cuerpo = respuesta.get_json()
    assert cuerpo['status'] == 'success'
    dto = cuerpo['request']
    assert dto['status'] == ESTADO_APROBADA
    assert dto['decided_by'] == {'id': escena['admin'].id,
                                 'name': escena['admin'].nombre
                                 or escena['admin'].email}
    assert dto['decided_at'].endswith('Z')
    acceso = PlatformAccessGrant.query.filter_by(
        request_id=solicitud.id).one()
    assert dto['access'] == {'id': acceso.id, 'status': ESTADO_EN_PROCESO}
    assert (acceso.origin, acceso.level, acceso.granted_by) == (
        ORIGEN_SOLICITUD, 'usuario', escena['admin'].id)
    trabajo = db.session.get(ProvisioningJob, acceso.last_job_id)
    assert trabajo is not None and trabajo.operation == 'otorgar'
    assert recargar(solicitud.id).slot_pendiente is None
    log = AuditLog.query.filter_by(action='solicitud_aprobada').one()
    assert log.request_id == solicitud.id and log.grant_id == acceso.id
    assert log.target_user_id == escena['usuario'].id
    assert log.before_state['status'] == ESTADO_PENDIENTE
    assert log.after_state['status'] == ESTADO_APROBADA
    assert log.after_state['decided_by'] == escena['admin'].id
    assert [a[0] for a in avisos] == ['aprobada']
    assert avisos[0][1][0].id == escena['usuario'].id


def test_aprobar_subir_de_nivel_reemplaza_el_acceso(escena, cliente_como,
                                                    cola_falsa, avisos):
    anterior = dar_acceso(escena['usuario'], escena['plataforma'], 'usuario')
    solicitud = pendiente(escena['usuario'], escena['plataforma'], 'admin',
                          current_level='usuario')

    respuesta = aprobar(cliente_como(escena['super']), solicitud.id)

    assert respuesta.status_code == 200, respuesta.get_json()
    db.session.expire_all()
    assert db.session.get(PlatformAccessGrant,
                          anterior.id).status == ESTADO_REVOCANDO
    nuevo = PlatformAccessGrant.query.filter_by(request_id=solicitud.id).one()
    assert (nuevo.level, nuevo.status) == ('admin', ESTADO_EN_PROCESO)


def test_superadmin_aprueba_la_solicitud_de_un_admin(escena, cliente_como,
                                                     cola_falsa, avisos):
    solicitud = pendiente(escena['admin_otra'], escena['plataforma'])

    respuesta = aprobar(cliente_como(escena['super']), solicitud.id)

    assert respuesta.status_code == 200, respuesta.get_json()


def test_admin_de_otra_area_recibe_404(escena, cliente_como, cola_falsa):
    """RF-03 / SEC-AUTHZ-07: contrato `Admin (ajena)` → 404."""
    solicitud = pendiente(escena['ajeno'], escena['de_otra'])

    for respuesta in (aprobar(cliente_como(escena['admin']), solicitud.id),
                      rechazar(cliente_como(escena['admin']), solicitud.id)):
        assert _codigo(respuesta) == (404, 'no_encontrado')
    _sigue_pendiente(solicitud.id)


def test_admin_no_aprueba_la_solicitud_de_otro_admin(escena, cliente_como,
                                                     cola_falsa):
    solicitud = pendiente(escena['admin_otra'], escena['plataforma'])

    respuesta = aprobar(cliente_como(escena['admin']), solicitud.id)

    assert _codigo(respuesta) == (404, 'no_encontrado')
    _sigue_pendiente(solicitud.id)


def test_nadie_decide_su_propia_solicitud(escena, cliente_como, cola_falsa):
    """P12 / SEC-AUTHZ-08."""
    admin_ventas = escena['admin_otra']
    solicitud = pendiente(admin_ventas, escena['plataforma'])

    for respuesta in (aprobar(cliente_como(admin_ventas), solicitud.id),
                      rechazar(cliente_como(admin_ventas), solicitud.id)):
        assert _codigo(respuesta) == (403, 'solicitud_propia')
    _sigue_pendiente(solicitud.id)


def test_usuario_no_aprueba_ni_rechaza(escena, cliente_como, cola_falsa):
    solicitud = pendiente(escena['ajeno'], escena['de_otra'])

    assert aprobar(cliente_como(escena['usuario']),
                   solicitud.id).status_code == 403
    assert rechazar(cliente_como(escena['usuario']),
                    solicitud.id).status_code == 403
    _sigue_pendiente(solicitud.id)


def test_inexistente_404(escena, cliente_como):
    assert _codigo(aprobar(cliente_como(escena['super']), 999)) == (
        404, 'no_encontrado')
    assert _codigo(rechazar(cliente_como(escena['super']), 999)) == (
        404, 'no_encontrado')


def test_aprobar_una_ya_decidida_409(escena, cliente_como, cola_falsa, avisos):
    solicitud = pendiente(escena['usuario'], escena['plataforma'])
    cliente = cliente_como(escena['admin'])
    assert rechazar(cliente, solicitud.id).status_code == 200

    for respuesta in (aprobar(cliente, solicitud.id),
                      rechazar(cliente, solicitud.id)):
        assert _codigo(respuesta) == (409, 'solicitud_ya_decidida')
    assert PlatformAccessGrant.query.count() == 0


def test_segunda_decision_concurrente_409_un_solo_acceso(escena, cola_falsa):
    """SEC-AUTHZ-10: la otra transacción ya confirmó la aprobación; esta
    aún tiene la solicitud `pendiente` en memoria (lectura previa)."""
    solicitud = pendiente(escena['usuario'], escena['plataforma'])
    obsoleta = db.session.get(PlatformAccessRequest, solicitud.id)
    assert obsoleta.status == ESTADO_PENDIENTE
    with db.engine.begin() as conexion:  # la primera decisión, confirmada
        conexion.execute(
            update(PlatformAccessRequest)
            .where(PlatformAccessRequest.id == solicitud.id)
            .values(status=ESTADO_APROBADA, decided_by=escena['super'].id,
                    decided_at=ahora(), slot_pendiente=None))

    with pytest.raises(ErrorDeAcceso) as info:
        approvals.aprobar(obsoleta, escena['admin'])
    db.session.rollback()

    assert (info.value.http, info.value.codigo) == (409,
                                                    'solicitud_ya_decidida')
    final = recargar(solicitud.id)
    assert (final.status, final.decided_by) == (ESTADO_APROBADA,
                                                escena['super'].id)
    assert PlatformAccessGrant.query.count() == 0
    assert ProvisioningJob.query.count() == 0


def test_rechazo_concurrente_no_sobrescribe_la_aprobacion(escena):
    solicitud = pendiente(escena['usuario'], escena['plataforma'])
    obsoleta = db.session.get(PlatformAccessRequest, solicitud.id)
    with db.engine.begin() as conexion:
        conexion.execute(
            update(PlatformAccessRequest)
            .where(PlatformAccessRequest.id == solicitud.id)
            .values(status=ESTADO_APROBADA, decided_by=escena['super'].id,
                    decided_at=ahora(), slot_pendiente=None))

    with pytest.raises(ErrorDeAcceso) as info:
        approvals.rechazar(obsoleta, escena['admin'], MOTIVO)
    db.session.rollback()

    assert info.value.codigo == 'solicitud_ya_decidida'
    final = recargar(solicitud.id)
    assert (final.status, final.rejection_reason) == (ESTADO_APROBADA, None)


def test_choque_al_confirmar_responde_409_y_revierte(escena, cliente_como,
                                                     cola_falsa, monkeypatch):
    solicitud = pendiente(escena['usuario'], escena['plataforma'])
    commit = db.session.commit

    def _choca():
        db.session.rollback()
        raise IntegrityError('INSERT', {}, Exception('clave repetida'))

    monkeypatch.setattr(db.session, 'commit', _choca)
    respuesta = aprobar(cliente_como(escena['admin']), solicitud.id)
    monkeypatch.setattr(db.session, 'commit', commit)

    assert _codigo(respuesta) == (409, 'estado_invalido')
    _sigue_pendiente(solicitud.id)


def test_aprobar_nivel_no_integrado_409(escena, cliente_como, cola_falsa):
    solo_usuario = fabricas.crear_plataforma(
        escena['area'], 'Nómina', integration_type=TIPO_LDAP,
        ldap_group_user_dn='cn=nomina-usuario,ou=grupos,dc=pruebas,dc=local')
    solicitud = pendiente(escena['usuario'], solo_usuario, 'admin')

    respuesta = aprobar(cliente_como(escena['admin']), solicitud.id)

    assert _codigo(respuesta) == (409, 'plataforma_no_disponible')
    _sigue_pendiente(solicitud.id)
    assert ProvisioningJob.query.count() == 0


def test_aprobar_con_el_acceso_ya_vigente_409(escena, cliente_como,
                                              cola_falsa):
    dar_acceso(escena['usuario'], escena['plataforma'], 'usuario')
    solicitud = pendiente(escena['usuario'], escena['plataforma'], 'usuario')

    respuesta = aprobar(cliente_como(escena['admin']), solicitud.id)

    assert _codigo(respuesta) == (409, 'nivel_vigente')
    _sigue_pendiente(solicitud.id)
    assert PlatformAccessGrant.query.filter_by(
        status=ESTADO_ACTIVO).count() == 1
    assert ProvisioningJob.query.count() == 0


def test_aprobar_a_una_cuenta_inactiva_409(escena, cliente_como, cola_falsa):
    solicitud = pendiente(escena['usuario'], escena['plataforma'])
    escena['usuario'].is_active = False
    db.session.commit()

    respuesta = aprobar(cliente_como(escena['super']), solicitud.id)

    assert _codigo(respuesta) == (409, 'cuenta_inactiva')
    _sigue_pendiente(solicitud.id)


def test_aprobar_si_el_solicitante_ya_no_es_del_area_404(escena, cliente_como,
                                                         cola_falsa):
    """P1: la cuenta debe pertenecer al área de la plataforma al aprobar."""
    solicitud = pendiente(escena['usuario'], escena['plataforma'])
    escena['usuario'].areas = [escena['otra']]
    db.session.commit()

    respuesta = aprobar(cliente_como(escena['super']), solicitud.id)

    assert _codigo(respuesta) == (404, 'no_encontrado')
    _sigue_pendiente(solicitud.id)


@pytest.mark.parametrize('cuerpo,esperado', [
    ({'level': 'admin'}, 'campo_no_permitido'),
    ([1], 'cuerpo_invalido'),
])
def test_aprobar_lista_blanca_del_cuerpo(escena, cliente_como, cola_falsa,
                                         cuerpo, esperado):
    solicitud = pendiente(escena['usuario'], escena['plataforma'])

    respuesta = aprobar(cliente_como(escena['admin']), solicitud.id,
                        json=cuerpo)

    assert _codigo(respuesta) == (400, esperado)
    _sigue_pendiente(solicitud.id)


def test_un_fallo_del_aviso_no_revierte_la_aprobacion(escena, cliente_como,
                                                      cola_falsa, monkeypatch):
    def _falla(*_):
        raise RuntimeError('SMTP caído')

    monkeypatch.setattr(api_solicitudes, 'notificar_solicitud_aprobada',
                        _falla)
    solicitud = pendiente(escena['usuario'], escena['plataforma'])

    respuesta = aprobar(cliente_como(escena['admin']), solicitud.id)

    assert respuesta.status_code == 200
    assert recargar(solicitud.id).status == ESTADO_APROBADA


# --------------------------------------------------------------------------- #
# POST /access-requests/<id>/reject
# --------------------------------------------------------------------------- #

def test_rechazar_con_motivo_audita_y_avisa(escena, cliente_como, avisos):
    solicitud = pendiente(escena['usuario'], escena['plataforma'])

    respuesta = rechazar(cliente_como(escena['admin']), solicitud.id,
                         f'  {MOTIVO}  ')

    assert respuesta.status_code == 200, respuesta.get_json()
    dto = respuesta.get_json()['request']
    assert dto['status'] == ESTADO_RECHAZADA
    assert dto['rejection_reason'] == MOTIVO
    assert dto['decided_by']['id'] == escena['admin'].id
    assert dto['access'] is None
    assert PlatformAccessGrant.query.count() == 0
    log = AuditLog.query.filter_by(action='solicitud_rechazada').one()
    assert log.request_id == solicitud.id
    assert log.before_state['status'] == ESTADO_PENDIENTE
    assert log.after_state['rejection_reason'] == MOTIVO
    assert avisos == [('rechazada', avisos[0][1])]
    assert avisos[0][1][3] == MOTIVO


@pytest.mark.parametrize('cuerpo', [
    {},
    {'reason': None},
    {'reason': ''},
    {'reason': '   corto   '},
    {'reason': 'x' * (ACCESS_REQUEST_REJECTION_MIN_LENGTH - 1)},
    {'reason': 'x' * (LARGO_TEXTO + 1)},
    {'reason': 12345678901},
])
def test_rechazo_exige_motivo_de_10_a_500(escena, cliente_como, cuerpo):
    """RF-06; contrato 1.1: `422 validacion` con `fields.reason`."""
    solicitud = pendiente(escena['usuario'], escena['plataforma'])

    respuesta = rechazar(cliente_como(escena['admin']), solicitud.id,
                         json=cuerpo)

    assert _codigo(respuesta) == (422, 'validacion')
    assert respuesta.get_json()['fields'] == {
        'reason': 'Escribe entre 10 y 500 caracteres.'}
    _sigue_pendiente(solicitud.id)


def test_rechazo_con_motivo_en_los_limites(escena, cliente_como, avisos):
    cliente = cliente_como(escena['admin'])
    for largo in (ACCESS_REQUEST_REJECTION_MIN_LENGTH, LARGO_TEXTO):
        solicitud = pendiente(escena['usuario'], escena['plataforma'])
        assert rechazar(cliente, solicitud.id,
                        'x' * largo).status_code == 200


def test_rechazar_lista_blanca_del_cuerpo(escena, cliente_como):
    solicitud = pendiente(escena['usuario'], escena['plataforma'])

    respuesta = rechazar(cliente_como(escena['admin']), solicitud.id,
                         json={'reason': MOTIVO, 'status': 'aprobada'})

    assert _codigo(respuesta) == (400, 'campo_no_permitido')
    _sigue_pendiente(solicitud.id)


# --------------------------------------------------------------------------- #
# CSRF provisional (escritura_del_portal)
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('decidir', [aprobar, rechazar])
def test_formulario_urlencoded_415(escena, cliente_como, cola_falsa, decidir):
    solicitud = pendiente(escena['usuario'], escena['plataforma'])

    respuesta = decidir(cliente_como(escena['admin']), solicitud.id,
                        json=None, data={'reason': MOTIVO},
                        content_type='application/x-www-form-urlencoded')

    assert _codigo(respuesta) == (415, 'tipo_no_soportado')
    _sigue_pendiente(solicitud.id)


@pytest.mark.parametrize('decidir', [aprobar, rechazar])
def test_cross_site_403(escena, cliente_como, cola_falsa, decidir):
    solicitud = pendiente(escena['usuario'], escena['plataforma'])

    respuesta = decidir(cliente_como(escena['admin']), solicitud.id,
                        headers={'Sec-Fetch-Site': 'cross-site'})

    assert _codigo(respuesta) == (403, 'csrf_invalido')
    _sigue_pendiente(solicitud.id)
