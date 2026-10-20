"""API de accesos (FNC-058, contrato `accesos.md` v1.1): mis accesos,
accesos de una cuenta y revocación manual con alcance por rol."""
from datetime import timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app import db
from app.modules.access.models import PlatformAccessGrant
from app.modules.access.tipos import (ESTADO_ACTIVO, ESTADO_EN_PROCESO,
                                      ESTADO_REVOCADO, ESTADO_REVOCANDO,
                                      LARGO_MOTIVO, ORIGEN_ADMIN_DE_AREA,
                                      ORIGEN_SOLICITUD)
from app.modules.audit.models import AuditLog
from app.modules.platforms.tipos import NIVEL_USUARIO, TIPO_LDAP
from app.modules.provisioning.models import ProvisioningJob
from app.modules.provisioning.reloj import ahora
from tests import fabricas
from tests.access.conftest import recargar

A = '/api/v1'
CAMPOS_ACCESS = {'id', 'status', 'level', 'origin', 'user', 'platform', 'area',
                 'request_id', 'granted_by', 'granted_at', 'revoked_by',
                 'revoked_at', 'revoke_reason', 'last_job_id'}
ORIGEN_AJENO = 'https://atacante.pruebas.invalid'


def _acceso(usuario, plataforma, estado=ESTADO_ACTIVO,
            origen=ORIGEN_SOLICITUD, otorgante=None, hace_minutos=0):
    acceso = PlatformAccessGrant(
        user_id=usuario.id, platform_id=plataforma.id, level=NIVEL_USUARIO,
        origin=origen, request_id=41 if origen == ORIGEN_SOLICITUD else None,
        granted_by=otorgante.id if otorgante else None,
        granted_at=ahora() - timedelta(minutes=hace_minutos), status=estado,
        updated_at=ahora())
    acceso.sincronizar_slots()
    db.session.add(acceso)
    db.session.commit()
    return acceso


@pytest.fixture
def otra_plataforma(escena):
    return fabricas.crear_plataforma(escena['otra'], 'Ventas web',
                                     integration_type=TIPO_LDAP)


def _ids(respuesta):
    assert respuesta.status_code == 200, respuesta.get_json()
    return [a['id'] for a in respuesta.get_json()['items']]


# --------------------------------------------------------------------------- #
# GET /me/access
# --------------------------------------------------------------------------- #

def test_mis_accesos_solo_los_propios_vigentes_y_del_mas_reciente(
        escena, cliente_como, otra_plataforma):
    ana = escena['usuario']
    viejo = _acceso(ana, escena['plataforma'], hace_minutos=30,
                    otorgante=escena['admin'])
    nuevo = _acceso(ana, otra_plataforma, estado=ESTADO_EN_PROCESO)
    _acceso(ana, otra_plataforma, estado=ESTADO_REVOCADO, hace_minutos=60)
    _acceso(escena['ajeno'], otra_plataforma)

    respuesta = cliente_como(ana).get(f'{A}/me/access')

    assert _ids(respuesta) == [nuevo.id, viejo.id]
    datos = respuesta.get_json()
    assert (datos['page'], datos['per_page'], datos['total']) == (1, 25, 2)
    item = datos['items'][1]
    # Rol usuario: sin `last_job_id` (contrato).
    assert set(item) == CAMPOS_ACCESS - {'last_job_id'}
    assert item['user'] == {'id': ana.id, 'name': ana.nombre,
                            'email': ana.email}
    assert item['platform'] == {'id': escena['plataforma'].id,
                                'name': 'Contabilidad',
                                'integration_type': TIPO_LDAP}
    assert item['area'] == {'id': escena['area'].id, 'name': 'Finanzas'}
    assert item['granted_by'] == {'id': escena['admin'].id,
                                  'name': escena['admin'].nombre}
    assert item['granted_at'].endswith('Z')
    assert item['revoked_by'] is None and item['revoked_at'] is None


def test_mis_accesos_filtra_por_estado(escena, cliente_como):
    ana = escena['usuario']
    _acceso(ana, escena['plataforma'])
    revocado = _acceso(ana, escena['plataforma'], estado=ESTADO_REVOCADO)

    respuesta = cliente_como(ana).get(f'{A}/me/access?status=revocado')

    assert _ids(respuesta) == [revocado.id]


@pytest.mark.parametrize('consulta', ['status=todos', 'per_page=101',
                                      'page=0', 'page=uno'])
def test_mis_accesos_parametro_invalido_400(escena, cliente_como, consulta):
    respuesta = cliente_como(escena['usuario']).get(f'{A}/me/access?{consulta}')

    assert respuesta.status_code == 400
    assert respuesta.get_json()['code'] == 'parametro_invalido'


def test_mis_accesos_de_un_admin_incluye_el_trabajo(escena, cliente_como):
    _acceso(escena['admin'], escena['plataforma'],
            origen=ORIGEN_ADMIN_DE_AREA)

    item, = cliente_como(escena['admin']).get(
        f'{A}/me/access').get_json()['items']

    assert set(item) == CAMPOS_ACCESS


def test_mis_accesos_del_superadmin_vacio(escena, cliente_como):
    respuesta = cliente_como(escena['super']).get(f'{A}/me/access')

    assert _ids(respuesta) == []


# --------------------------------------------------------------------------- #
# GET /users/<id>/access
# --------------------------------------------------------------------------- #

def test_admin_ve_solo_los_accesos_de_las_plataformas_de_sus_areas(
        escena, cliente_como, otra_plataforma):
    ana = escena['usuario']
    ana.areas = [escena['area'], escena['otra']]
    db.session.commit()
    propio = _acceso(ana, escena['plataforma'])
    _acceso(ana, otra_plataforma)

    respuesta = cliente_como(escena['admin']).get(f'{A}/users/{ana.id}/access')

    assert _ids(respuesta) == [propio.id]
    assert set(respuesta.get_json()['items'][0]) == CAMPOS_ACCESS


def test_superadmin_ve_todos_los_accesos_de_una_cuenta(
        escena, cliente_como, otra_plataforma):
    ana = escena['usuario']
    uno = _acceso(ana, escena['plataforma'], hace_minutos=5)
    dos = _acceso(ana, otra_plataforma)

    respuesta = cliente_como(escena['super']).get(f'{A}/users/{ana.id}/access')

    assert _ids(respuesta) == [dos.id, uno.id]


@pytest.mark.parametrize('destino', ['ajeno', 'admin2', 'super', 'inexistente'])
def test_admin_fuera_de_alcance_recibe_404(escena, cliente_como, destino):
    usuario_id = escena[destino].id if destino != 'inexistente' else 9999

    respuesta = cliente_como(escena['admin']).get(
        f'{A}/users/{usuario_id}/access')

    assert respuesta.status_code == 404
    assert respuesta.get_json()['code'] == 'no_encontrado'


def test_usuario_no_consulta_accesos_de_otra_cuenta(escena, cliente_como):
    respuesta = cliente_como(escena['usuario']).get(
        f'{A}/users/{escena["usuario"].id}/access')

    assert respuesta.status_code == 403


# --------------------------------------------------------------------------- #
# POST /access/<id>/revoke
# --------------------------------------------------------------------------- #

def _revocar(cliente, acceso_id, **kwargs):
    # El cliente web siempre envía JSON (CSRF provisional, H1).
    kwargs.setdefault('json', {})
    return cliente.post(f'{A}/access/{acceso_id}/revoke', **kwargs)


@pytest.mark.parametrize('actor', ['admin', 'super'])
def test_revocar_deja_revocando_encola_y_audita(escena, cliente_como,
                                                cola_falsa, actor):
    acceso = _acceso(escena['usuario'], escena['plataforma'])

    respuesta = _revocar(cliente_como(escena[actor]), acceso.id,
                         json={'reason': '  Cambió de puesto  '})

    assert respuesta.status_code == 200, respuesta.get_json()
    datos = respuesta.get_json()
    assert datos['status'] == 'success'
    assert set(datos['access']) == CAMPOS_ACCESS
    acceso = recargar(acceso.id)
    assert acceso.status == ESTADO_REVOCANDO
    assert acceso.revoke_reason == 'Cambió de puesto'
    assert acceso.revoked_by == escena[actor].id
    trabajo, = ProvisioningJob.query.all()
    assert (trabajo.operation, trabajo.access_id) == ('revocar', acceso.id)
    assert datos['access']['last_job_id'] == trabajo.id
    assert datos['access']['revoked_by'] == {'id': escena[actor].id,
                                             'name': escena[actor].nombre}
    assert cola_falsa.ids() == [trabajo.id]
    evento, = AuditLog.query.filter_by(action='acceso_revocado').all()
    assert evento.grant_id == acceso.id
    assert evento.user == escena[actor].email


def test_revocar_sin_motivo(escena, cliente_como, cola_falsa):
    acceso = _acceso(escena['usuario'], escena['plataforma'])

    respuesta = _revocar(cliente_como(escena['admin']), acceso.id)

    assert respuesta.status_code == 200
    assert recargar(acceso.id).revoke_reason is None


def _sin_cambios(acceso_id):
    assert recargar(acceso_id).status == ESTADO_ACTIVO
    assert ProvisioningJob.query.count() == 0
    assert AuditLog.query.filter_by(action='acceso_revocado').count() == 0


def test_admin_no_revoca_accesos_de_un_area_ajena(escena, cliente_como,
                                                  cola_falsa,
                                                  otra_plataforma):
    acceso = _acceso(escena['ajeno'], otra_plataforma)

    respuesta = _revocar(cliente_como(escena['admin']), acceso.id,
                         json={'reason': 'x' * (LARGO_MOTIVO + 1)})

    # 404 antes de validar el cuerpo: no revela que el acceso existe.
    assert respuesta.status_code == 404
    assert respuesta.get_json()['code'] == 'no_encontrado'
    _sin_cambios(acceso.id)


def test_admin_no_revoca_accesos_automaticos_de_otro_admin(
        escena, cliente_como, cola_falsa):
    acceso = _acceso(escena['admin2'], escena['plataforma'],
                     origen=ORIGEN_ADMIN_DE_AREA)

    respuesta = _revocar(cliente_como(escena['admin']), acceso.id,
                         json={'extra': 1})

    assert respuesta.status_code == 404
    _sin_cambios(acceso.id)


def test_superadmin_revoca_un_acceso_automatico(escena, cliente_como,
                                                cola_falsa):
    acceso = _acceso(escena['admin2'], escena['plataforma'],
                     origen=ORIGEN_ADMIN_DE_AREA)

    respuesta = _revocar(cliente_como(escena['super']), acceso.id)

    assert respuesta.status_code == 200
    assert recargar(acceso.id).status == ESTADO_REVOCANDO


def test_no_se_revoca_el_acceso_propio(escena, cliente_como, cola_falsa):
    acceso = _acceso(escena['admin'], escena['plataforma'],
                     origen=ORIGEN_ADMIN_DE_AREA)

    respuesta = _revocar(cliente_como(escena['admin']), acceso.id)

    assert respuesta.status_code == 403
    assert respuesta.get_json()['code'] == 'operacion_propia'
    _sin_cambios(acceso.id)


def test_usuario_no_revoca(escena, cliente_como, cola_falsa):
    acceso = _acceso(escena['usuario'], escena['plataforma'])

    respuesta = _revocar(cliente_como(escena['usuario']), acceso.id)

    assert respuesta.status_code == 403
    _sin_cambios(acceso.id)


def test_revocar_inexistente_404(escena, cliente_como):
    respuesta = _revocar(cliente_como(escena['super']), 9999)

    assert respuesta.status_code == 404
    assert respuesta.get_json()['code'] == 'no_encontrado'


def test_solo_se_revoca_un_acceso_activo(escena, cliente_como, cola_falsa):
    acceso = _acceso(escena['usuario'], escena['plataforma'],
                     estado=ESTADO_EN_PROCESO)

    respuesta = _revocar(cliente_como(escena['admin']), acceso.id)

    assert respuesta.status_code == 409
    assert respuesta.get_json()['code'] == 'estado_invalido'
    assert recargar(acceso.id).status == ESTADO_EN_PROCESO


def test_motivo_de_mas_de_500_caracteres_422(escena, cliente_como, cola_falsa):
    acceso = _acceso(escena['usuario'], escena['plataforma'])

    respuesta = _revocar(cliente_como(escena['admin']), acceso.id,
                         json={'reason': 'x' * (LARGO_MOTIVO + 1)})

    assert respuesta.status_code == 422
    datos = respuesta.get_json()
    assert datos['code'] == 'validacion'
    assert 'reason' in datos['fields']
    _sin_cambios(acceso.id)


@pytest.mark.parametrize('cuerpo,codigo', [
    ({'reason': 'ok', 'status': 'revocado'}, 'campo_no_permitido'),
    ({'revoked_by': 1}, 'campo_no_permitido'),
    (['reason'], 'cuerpo_invalido'),
])
def test_lista_blanca_del_cuerpo(escena, cliente_como, cola_falsa, cuerpo,
                                 codigo):
    acceso = _acceso(escena['usuario'], escena['plataforma'])

    respuesta = _revocar(cliente_como(escena['admin']), acceso.id, json=cuerpo)

    assert respuesta.status_code == 400
    assert respuesta.get_json()['code'] == codigo
    _sin_cambios(acceso.id)


def test_choque_simultaneo_responde_409_y_revierte(escena, cliente_como,
                                                   cola_falsa, monkeypatch):
    acceso = _acceso(escena['usuario'], escena['plataforma'])
    commit = db.session.commit

    def _choca():
        db.session.rollback()
        raise IntegrityError('INSERT', {}, Exception('clave repetida'))

    monkeypatch.setattr(db.session, 'commit', _choca)
    respuesta = _revocar(cliente_como(escena['admin']), acceso.id)
    monkeypatch.setattr(db.session, 'commit', commit)

    assert respuesta.status_code == 409
    assert respuesta.get_json()['code'] == 'estado_invalido'
    _sin_cambios(acceso.id)


@pytest.mark.xfail(strict=True, reason='SEG-06 / FNC-008: sin token CSRF ni '
                   'comprobación de Origin; la protección provisional solo '
                   'mira Sec-Fetch-Site y el tipo JSON')
def test_peticion_sin_token_y_origen_ajeno_no_revoca(escena, cliente_como,
                                                     cola_falsa):
    acceso = _acceso(escena['usuario'], escena['plataforma'])

    respuesta = _revocar(cliente_como(escena['admin']), acceso.id,
                         headers={'Origin': ORIGEN_AJENO})

    assert respuesta.status_code in (400, 403)
    assert recargar(acceso.id).status == ESTADO_ACTIVO



# --------------------------------------------------------------------------- #
# H1 (auditoría FNC-058): CSRF provisional
# --------------------------------------------------------------------------- #

def test_formulario_urlencoded_no_revoca_415(escena, cliente_como, cola_falsa):
    acceso = _acceso(escena['usuario'], escena['plataforma'])

    respuesta = cliente_como(escena['admin']).post(
        f'{A}/access/{acceso.id}/revoke', data={'reason': 'x'},
        content_type='application/x-www-form-urlencoded')

    assert respuesta.status_code == 415
    assert respuesta.get_json()['code'] == 'tipo_no_soportado'
    _sin_cambios(acceso.id)


def test_peticion_cross_site_no_revoca_403(escena, cliente_como, cola_falsa):
    acceso = _acceso(escena['usuario'], escena['plataforma'])

    respuesta = _revocar(cliente_como(escena['admin']), acceso.id,
                         headers={'Sec-Fetch-Site': 'cross-site'})

    assert respuesta.status_code == 403
    assert respuesta.get_json()['code'] == 'csrf_invalido'
    _sin_cambios(acceso.id)


# --------------------------------------------------------------------------- #
# H2 (auditoría FNC-058): revocación concurrente
# --------------------------------------------------------------------------- #

def test_segunda_revocacion_concurrente_409_sin_sobrescribir(
        escena, cola_falsa):
    """La otra transacción ya confirmó la revocación; esta aún tiene el
    acceso `activo` en memoria (lectura previa)."""
    from sqlalchemy import update

    from app.modules.access import services
    from app.modules.access.errores import ErrorDeAcceso

    acceso = _acceso(escena['usuario'], escena['plataforma'])
    obsoleto = db.session.get(PlatformAccessGrant, acceso.id)
    assert obsoleto.status == ESTADO_ACTIVO
    with db.engine.begin() as conexion:  # la primera revocación, confirmada
        conexion.execute(
            update(PlatformAccessGrant)
            .where(PlatformAccessGrant.id == acceso.id)
            .values(status=ESTADO_REVOCANDO, revoked_by=escena['super'].id,
                    revoke_reason='primera', slot_ocupante=None))

    with pytest.raises(ErrorDeAcceso) as info:
        services.revocar(obsoleto, actor=escena['admin'], motivo='segunda')
    db.session.rollback()

    assert info.value.http == 409 and info.value.codigo == 'estado_invalido'
    final = recargar(acceso.id)
    assert (final.status, final.revoked_by, final.revoke_reason) == (
        ESTADO_REVOCANDO, escena['super'].id, 'primera')
    assert ProvisioningJob.query.count() == 0
    assert AuditLog.query.filter_by(action='acceso_revocado').count() == 0
