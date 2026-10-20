"""API de ejecuciones (FNC-062, contrato `conectores-y-ejecuciones.md`):
bitácora con alcance por rol y reintento manual (P10: solo el superadmin)."""
from datetime import timedelta

import pytest
from sqlalchemy import update

from app import db
from app.authz import ROLE_ADMIN, ROLE_AREA_ADMIN, ROLE_USER
from app.modules.access import services as servicios_accesos
from app.modules.access.errores import ErrorDeAcceso
from app.modules.access.models import PlatformAccessGrant
from app.modules.access.tipos import (ESTADO_EN_PROCESO, ESTADO_FALLIDO,
                                      ESTADO_FALLO_REVOCACION,
                                      ESTADO_REVOCADO, ESTADO_REVOCANDO,
                                      ORIGEN_SOLICITUD)
from app.modules.audit.models import AuditLog
from app.modules.platforms.tipos import NIVEL_USUARIO, TIPO_LDAP
from app.modules.provisioning import ejecucion
from app.modules.provisioning.configuracion import cargar_configuracion
from app.modules.provisioning.ejecucion import EstadoInvalido, reabrir
from app.modules.provisioning.models import (ProvisioningJob,
                                             ProvisioningJobAttempt)
from app.modules.provisioning.reloj import ahora
from app.modules.provisioning.tipos import (ESTADO_EXITOSO,
                                            ESTADO_FALLIDO as JOB_FALLIDO,
                                            ESTADO_PENDIENTE,
                                            ESTADO_REINTENTANDO,
                                            OPERACION_OTORGAR,
                                            OPERACION_REVOCAR,
                                            PROVEEDOR_CONECTOR,
                                            PROVEEDOR_LDAP,
                                            RESULTADO_ERROR_PERMANENTE)
from tests import fabricas

A = '/api/v1/provisioning/jobs'
CAMPOS_JOB = {'id', 'status', 'operation', 'provider', 'access_id', 'user',
              'platform', 'area', 'attempts_count', 'max_attempts',
              'next_attempt_at', 'created_at', 'finished_at'}
CAMPOS_INTENTO = {'n', 'started_at', 'finished_at', 'result', 'error'}
SECRETO_FICTICIO = 'valor-secreto-de-prueba-123'
JSON_VACIO = {'json': {}}


@pytest.fixture
def escena(app):
    area = fabricas.crear_area('Finanzas')
    otra = fabricas.crear_area('Ventas')
    plataforma = fabricas.crear_plataforma(area, 'Contabilidad',
                                           integration_type=TIPO_LDAP)
    ajena = fabricas.crear_plataforma(otra, 'CRM', integration_type=TIPO_LDAP)
    return {
        'area': area, 'otra': otra, 'plataforma': plataforma, 'ajena': ajena,
        'admin': fabricas.crear_usuario(ROLE_AREA_ADMIN,
                                        areas_administradas=[area]),
        'usuario': fabricas.crear_usuario(ROLE_USER, areas=[area]),
        'ajeno': fabricas.crear_usuario(ROLE_USER, areas=[otra]),
        'super': fabricas.crear_usuario(ROLE_ADMIN),
    }


def _acceso(usuario, plataforma, estado=ESTADO_FALLIDO):
    acceso = PlatformAccessGrant(
        user_id=usuario.id, platform_id=plataforma.id, level=NIVEL_USUARIO,
        origin=ORIGEN_SOLICITUD, request_id=1, status=estado,
        updated_at=ahora())
    acceso.sincronizar_slots()
    db.session.add(acceso)
    db.session.commit()
    return acceso


def _trabajo(usuario, plataforma, estado=JOB_FALLIDO,
             operacion=OPERACION_OTORGAR, acceso=None, hace_minutos=0,
             proveedor=PROVEEDOR_LDAP, errores=('Tiempo de espera agotado.',)):
    momento = ahora() - timedelta(minutes=hace_minutos)
    trabajo = ProvisioningJob(
        operation=operacion, provider=proveedor, level=NIVEL_USUARIO,
        status=estado, user_id=usuario.id, platform_id=plataforma.id,
        area_id=plataforma.area_id, access_id=acceso.id if acceso else None,
        idempotency_key=f'prueba-{usuario.id}-{operacion}-{momento.timestamp()}',
        attempts_count=len(errores), max_attempts=len(errores),
        created_at=momento, updated_at=momento,
        finished_at=momento if estado == JOB_FALLIDO else None)
    db.session.add(trabajo)
    db.session.flush()
    for n, error in enumerate(errores, start=1):
        db.session.add(ProvisioningJobAttempt(
            job_id=trabajo.id, number=n, started_at=momento,
            finished_at=momento, result=RESULTADO_ERROR_PERMANENTE,
            error=error))
    if acceso is not None:
        acceso.last_job_id = trabajo.id
    db.session.commit()
    return trabajo


def _recargar(modelo, ident):
    db.session.expire_all()
    return db.session.get(modelo, ident)


def _ids(respuesta):
    assert respuesta.status_code == 200, respuesta.get_json()
    return [j['id'] for j in respuesta.get_json()['items']]


# --------------------------------------------------------------------------- #
# GET /provisioning/jobs
# --------------------------------------------------------------------------- #

def test_superadmin_ve_todas_del_mas_reciente_y_sin_intentos(
        escena, cliente_como):
    viejo = _trabajo(escena['usuario'], escena['plataforma'], hace_minutos=30)
    nuevo = _trabajo(escena['ajeno'], escena['ajena'],
                     estado=ESTADO_REINTENTANDO)

    respuesta = cliente_como(escena['super']).get(A)

    assert _ids(respuesta) == [nuevo.id, viejo.id]
    datos = respuesta.get_json()
    assert (datos['page'], datos['per_page'], datos['total']) == (1, 25, 2)
    item = datos['items'][1]
    assert set(item) == CAMPOS_JOB
    assert item['user'] == {'id': escena['usuario'].id,
                            'name': escena['usuario'].nombre}
    assert item['platform'] == {'id': escena['plataforma'].id,
                                'name': 'Contabilidad'}
    assert item['area'] == {'id': escena['area'].id, 'name': 'Finanzas'}
    assert item['created_at'].endswith('Z')


def test_admin_solo_ve_las_de_sus_areas(escena, cliente_como):
    propio = _trabajo(escena['usuario'], escena['plataforma'])
    _trabajo(escena['ajeno'], escena['ajena'])

    cliente = cliente_como(escena['admin'])

    assert _ids(cliente.get(A)) == [propio.id]
    # Filtrar por el área ajena no la revela.
    assert _ids(cliente.get(f'{A}?area_id={escena["otra"].id}')) == []


def test_usuario_403(escena, cliente_como):
    respuesta = cliente_como(escena['usuario']).get(A)
    assert respuesta.status_code == 403


def test_filtros(escena, cliente_como):
    fallido = _trabajo(escena['usuario'], escena['plataforma'])
    exitoso = _trabajo(escena['usuario'], escena['plataforma'],
                       estado=ESTADO_EXITOSO, operacion=OPERACION_REVOCAR,
                       proveedor=PROVEEDOR_CONECTOR, hace_minutos=60 * 24 * 3)
    acceso = _acceso(escena['ajeno'], escena['ajena'])
    con_acceso = _trabajo(escena['ajeno'], escena['ajena'], acceso=acceso)
    cliente = cliente_como(escena['super'])

    assert _ids(cliente.get(f'{A}?status=exitoso')) == [exitoso.id]
    assert _ids(cliente.get(f'{A}?operation=otorgar')) == [con_acceso.id,
                                                            fallido.id]
    assert _ids(cliente.get(f'{A}?provider=conector')) == [exitoso.id]
    assert _ids(cliente.get(
        f'{A}?platform_id={escena["ajena"].id}')) == [con_acceso.id]
    assert _ids(cliente.get(
        f'{A}?user_id={escena["usuario"].id}')) == [fallido.id, exitoso.id]
    assert _ids(cliente.get(f'{A}?access_id={acceso.id}')) == [con_acceso.id]
    assert _ids(cliente.get(
        f'{A}?area_id={escena["area"].id}')) == [fallido.id, exitoso.id]
    ayer = (ahora() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
    assert _ids(cliente.get(f'{A}?to={ayer}')) == [exitoso.id]
    assert _ids(cliente.get(f'{A}?from={ayer}')) == [con_acceso.id,
                                                      fallido.id]
    pagina = cliente.get(f'{A}?per_page=1&page=2').get_json()
    assert ([j['id'] for j in pagina['items']], pagina['total']) == (
        [fallido.id], 3)


@pytest.mark.parametrize('consulta', [
    'status=otro', 'operation=otra', 'provider=ssh', 'access_id=x',
    'area_id=0', 'per_page=101', 'page=0', 'from=ayer',
])
def test_parametro_invalido_400(escena, cliente_como, consulta):
    respuesta = cliente_como(escena['super']).get(f'{A}?{consulta}')
    assert respuesta.status_code == 400
    assert respuesta.get_json()['code'] == 'parametro_invalido'


# --------------------------------------------------------------------------- #
# GET /provisioning/jobs/<id>
# --------------------------------------------------------------------------- #

# Un actor por prueba: en el contexto de la prueba, Flask-Login guarda en `g`
# al usuario de la primera petición.

@pytest.mark.parametrize('actor', ['super', 'admin'])
def test_detalle_con_intentos(escena, cliente_como, actor):
    trabajo = _trabajo(escena['usuario'], escena['plataforma'],
                       errores=('Primero.', 'Segundo.'))

    respuesta = cliente_como(escena[actor]).get(f'{A}/{trabajo.id}')

    assert respuesta.status_code == 200, respuesta.get_json()
    datos = respuesta.get_json()
    assert set(datos) == CAMPOS_JOB | {'attempts'}
    assert [i['n'] for i in datos['attempts']] == [1, 2]
    assert set(datos['attempts'][0]) == CAMPOS_INTENTO
    assert datos['attempts'][1]['error'] == 'Segundo.'


def test_detalle_ajeno_o_inexistente_404(escena, cliente_como):
    ajeno = _trabajo(escena['ajeno'], escena['ajena'])
    cliente = cliente_como(escena['admin'])

    for ruta in (f'{A}/{ajeno.id}', f'{A}/999999'):
        respuesta = cliente.get(ruta)
        assert respuesta.status_code == 404
        assert respuesta.get_json()['code'] == 'no_encontrado'


def test_detalle_usuario_403(escena, cliente_como):
    trabajo = _trabajo(escena['usuario'], escena['plataforma'])
    respuesta = cliente_como(escena['usuario']).get(f'{A}/{trabajo.id}')
    assert respuesta.status_code == 403


def test_error_mostrado_saneado_sin_datos_internos(escena, cliente_como,
                                                   monkeypatch):
    """SEC-CON-10: aunque la bitácora tuviera texto crudo (versión previa o
    proveedor nuevo), la API lo devuelve saneado."""
    monkeypatch.setenv('LDAP_BIND_PASSWORD', SECRETO_FICTICIO)
    crudo = (f'Fallo: password={SECRETO_FICTICIO}\nBearer abc.def '
             f'ldap://cn=admin:{SECRETO_FICTICIO}@directorio.local '
             + 'x' * 600)
    trabajo = _trabajo(escena['usuario'], escena['plataforma'],
                       errores=(crudo,))
    trabajo.locked_by = 'host-interno:1234'
    db.session.commit()

    respuesta = cliente_como(escena['super']).get(f'{A}/{trabajo.id}')

    texto = respuesta.get_data(as_text=True)
    assert SECRETO_FICTICIO not in texto
    assert 'abc.def' not in texto and '\\n' not in texto
    assert 'host-interno' not in texto and 'prueba-' not in texto
    assert len(respuesta.get_json()['attempts'][0]['error']) <= 500


# --------------------------------------------------------------------------- #
# POST /provisioning/jobs/<id>/retry
# --------------------------------------------------------------------------- #

def test_reintento_del_superadmin(escena, cliente_como, cola_falsa):
    acceso = _acceso(escena['usuario'], escena['plataforma'])
    trabajo = _trabajo(escena['usuario'], escena['plataforma'], acceso=acceso)
    cfg = cargar_configuracion()

    respuesta = cliente_como(escena['super']).post(
        f'{A}/{trabajo.id}/retry', **JSON_VACIO)

    assert respuesta.status_code == 200, respuesta.get_json()
    datos = respuesta.get_json()
    assert datos['status'] == 'success'
    assert datos['job']['status'] == ESTADO_PENDIENTE
    assert datos['job']['max_attempts'] == 1 + cfg.max_intentos
    assert [i['n'] for i in datos['job']['attempts']] == [1]
    assert _recargar(PlatformAccessGrant, acceso.id).status == ESTADO_EN_PROCESO
    registro = AuditLog.query.filter_by(action='ejecucion_reintentada').one()
    assert registro.actor_id == escena['super'].id
    assert registro.grant_id == acceso.id
    assert registro.area_id == escena['area'].id
    assert cola_falsa.ids() == [trabajo.id]


def test_reintento_de_revocar_vuelve_a_revocando(escena, cliente_como,
                                                cola_falsa):
    acceso = _acceso(escena['usuario'], escena['plataforma'],
                     estado=ESTADO_FALLO_REVOCACION)
    trabajo = _trabajo(escena['usuario'], escena['plataforma'], acceso=acceso,
                       operacion=OPERACION_REVOCAR)

    respuesta = cliente_como(escena['super']).post(
        f'{A}/{trabajo.id}/retry', **JSON_VACIO)

    assert respuesta.status_code == 200, respuesta.get_json()
    assert _recargar(PlatformAccessGrant, acceso.id).status == ESTADO_REVOCANDO


@pytest.mark.parametrize('actor', ['admin', 'usuario'])
def test_reintento_solo_superadmin_403(escena, cliente_como, actor):
    trabajo = _trabajo(escena['usuario'], escena['plataforma'])

    respuesta = cliente_como(escena[actor]).post(f'{A}/{trabajo.id}/retry',
                                                 **JSON_VACIO)

    assert respuesta.status_code == 403
    assert _recargar(ProvisioningJob, trabajo.id).status == JOB_FALLIDO


def test_reintento_inexistente_404(escena, cliente_como):
    respuesta = cliente_como(escena['super']).post(f'{A}/999999/retry',
                                                   **JSON_VACIO)
    assert respuesta.status_code == 404


@pytest.mark.parametrize('estado', [ESTADO_PENDIENTE, ESTADO_REINTENTANDO,
                                    ESTADO_EXITOSO])
def test_reintento_de_un_no_fallido_409(escena, cliente_como, estado):
    trabajo = _trabajo(escena['usuario'], escena['plataforma'], estado=estado)

    respuesta = cliente_como(escena['super']).post(
        f'{A}/{trabajo.id}/retry', **JSON_VACIO)

    assert respuesta.status_code == 409
    assert respuesta.get_json()['code'] == 'estado_invalido'
    assert _recargar(ProvisioningJob, trabajo.id).status == estado
    assert AuditLog.query.filter_by(action='ejecucion_reintentada').count() == 0


def test_reintento_de_otorgar_ya_revocado_409_sin_volver_a_meterlo(
        escena, cliente_como, cola_falsa):
    acceso = _acceso(escena['usuario'], escena['plataforma'])
    otorgar = _trabajo(escena['usuario'], escena['plataforma'], acceso=acceso)
    _trabajo(escena['usuario'], escena['plataforma'], estado=ESTADO_EXITOSO,
             operacion=OPERACION_REVOCAR, acceso=acceso, errores=())
    acceso.status = ESTADO_REVOCADO
    acceso.sincronizar_slots()
    db.session.commit()

    respuesta = cliente_como(escena['super']).post(
        f'{A}/{otorgar.id}/retry', **JSON_VACIO)

    assert respuesta.status_code == 409
    assert _recargar(ProvisioningJob, otorgar.id).status == JOB_FALLIDO
    assert _recargar(PlatformAccessGrant, acceso.id).status == ESTADO_REVOCADO
    assert cola_falsa.ids() == []


def test_reintento_sin_json_415_y_de_otro_sitio_403(escena, cliente_como):
    trabajo = _trabajo(escena['usuario'], escena['plataforma'])
    cliente = cliente_como(escena['super'])

    assert cliente.post(f'{A}/{trabajo.id}/retry').status_code == 415
    respuesta = cliente.post(f'{A}/{trabajo.id}/retry', json={},
                             headers={'Sec-Fetch-Site': 'cross-site'})
    assert respuesta.get_json()['code'] == 'csrf_invalido'
    assert _recargar(ProvisioningJob, trabajo.id).status == JOB_FALLIDO


def test_reintento_con_cuerpo_no_permitido_400(escena, cliente_como):
    trabajo = _trabajo(escena['usuario'], escena['plataforma'])

    respuesta = cliente_como(escena['super']).post(
        f'{A}/{trabajo.id}/retry', json={'status': 'pendiente'})

    assert respuesta.status_code == 400
    assert respuesta.get_json()['code'] == 'campo_no_permitido'


# --------------------------------------------------------------------------- #
# Reintentos simultáneos (UPDATE condicional)
# --------------------------------------------------------------------------- #

def _confirmar_desde_otra_conexion(sentencia):
    with db.engine.begin() as conexion:
        conexion.execute(sentencia)


def test_reabrir_obsoleto_no_reabre_dos_veces(escena):
    """El otro reintento ya confirmó `pendiente`; este aún lo tiene
    `fallido` en memoria."""
    trabajo = _trabajo(escena['usuario'], escena['plataforma'])
    obsoleto = db.session.get(ProvisioningJob, trabajo.id)
    _confirmar_desde_otra_conexion(
        update(ProvisioningJob).where(ProvisioningJob.id == trabajo.id)
        .values(status=ESTADO_PENDIENTE, max_attempts=99))

    with pytest.raises(EstadoInvalido):
        reabrir(obsoleto, cargar_configuracion())
    db.session.rollback()

    assert _recargar(ProvisioningJob, trabajo.id).max_attempts == 99


def test_reabrir_acceso_obsoleto_no_pisa_otro_cambio(escena):
    acceso = _acceso(escena['usuario'], escena['plataforma'])
    trabajo = _trabajo(escena['usuario'], escena['plataforma'], acceso=acceso)
    assert db.session.get(PlatformAccessGrant, acceso.id).status == \
        ESTADO_FALLIDO
    _confirmar_desde_otra_conexion(
        update(PlatformAccessGrant).where(PlatformAccessGrant.id == acceso.id)
        .values(status=ESTADO_REVOCANDO, slot_ocupante=None))

    with pytest.raises(ErrorDeAcceso):
        servicios_accesos.reabrir_acceso(trabajo)
    db.session.rollback()

    assert _recargar(PlatformAccessGrant, acceso.id).status == ESTADO_REVOCANDO


def test_segundo_reintento_simultaneo_409(escena, cliente_como, cola_falsa,
                                         monkeypatch):
    """El primer reintento confirma mientras el segundo ya leyó `fallido`."""
    acceso = _acceso(escena['usuario'], escena['plataforma'])
    trabajo = _trabajo(escena['usuario'], escena['plataforma'], acceso=acceso)
    original = ejecucion.revocado_despues

    def _primero_gana(t):
        _confirmar_desde_otra_conexion(
            update(ProvisioningJob).where(ProvisioningJob.id == trabajo.id)
            .values(status=ESTADO_PENDIENTE))
        return original(t)

    monkeypatch.setattr(ejecucion, 'revocado_despues', _primero_gana)

    respuesta = cliente_como(escena['super']).post(
        f'{A}/{trabajo.id}/retry', **JSON_VACIO)

    assert respuesta.status_code == 409
    assert respuesta.get_json()['code'] == 'estado_invalido'
    assert _recargar(PlatformAccessGrant, acceso.id).status == ESTADO_FALLIDO
    assert AuditLog.query.filter_by(action='ejecucion_reintentada').count() == 0
    assert cola_falsa.ids() == []
