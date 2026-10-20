"""Servicio de otorgar y revocar (FNC-054): transacción con el trabajo,
estados por el resultado del worker, unicidad, niveles (P5) y alcance."""
import pytest
from sqlalchemy.exc import IntegrityError

from app import db
from app.modules.access import rules, services
from app.modules.access.errores import ErrorDeAcceso
from app.modules.access.models import PlatformAccessGrant
from app.modules.access.tipos import (ESTADO_ACTIVO, ESTADO_EN_PROCESO,
                                      ESTADO_FALLIDO, ESTADO_FALLO_REVOCACION,
                                      ESTADO_REVOCADO, ESTADO_REVOCANDO,
                                      MOTIVO_REEMPLAZO, ORIGEN_ADMIN_DE_AREA,
                                      ORIGEN_SOLICITUD)
from app.modules.audit.models import AuditLog
from app.modules.platforms.tipos import NIVEL_ADMIN, NIVEL_USUARIO
from app.modules.provisioning import ejecucion
from app.modules.provisioning.models import ProvisioningJob
from app.modules.provisioning.providers import permanente
from tests.access.conftest import recargar


def _otorgar(escena, nivel=NIVEL_USUARIO, usuario='usuario', actor='admin',
             request_id=41):
    acceso = services.otorgar(escena[usuario], escena['plataforma'], nivel,
                              ORIGEN_SOLICITUD, actor=escena[actor],
                              request_id=request_id)
    db.session.commit()
    return acceso


def _codigo(info):
    return info.value.codigo


def _trabajos():
    return ProvisioningJob.query.order_by(ProvisioningJob.id).all()


def _activar(escena, cola_falsa, nivel=NIVEL_USUARIO):
    acceso = _otorgar(escena, nivel)
    cola_falsa.procesar()
    return recargar(acceso.id)


# --------------------------------------------------------------------------- #
# Otorgar
# --------------------------------------------------------------------------- #

def test_otorgar_crea_acceso_en_proceso_y_trabajo_en_la_misma_transaccion(
        escena, cola_falsa):
    acceso = _otorgar(escena)

    trabajo, = _trabajos()
    assert acceso.status == ESTADO_EN_PROCESO
    assert (trabajo.operation, trabajo.access_id, trabajo.level) == (
        'otorgar', acceso.id, NIVEL_USUARIO)
    assert acceso.last_job_id == trabajo.id
    assert acceso.granted_by == escena['admin'].id
    assert cola_falsa.ids() == [trabajo.id]
    evento, = AuditLog.query.filter_by(action='acceso_otorgado').all()
    assert evento.grant_id == acceso.id and evento.request_id == 41
    assert evento.before_state is None
    assert evento.after_state['status'] == ESTADO_EN_PROCESO


def test_si_el_llamador_revierte_no_queda_acceso_ni_trabajo(escena,
                                                            cola_falsa):
    services.otorgar(escena['usuario'], escena['plataforma'], NIVEL_USUARIO,
                     ORIGEN_SOLICITUD, actor=escena['admin'], request_id=1)
    db.session.rollback()

    assert PlatformAccessGrant.query.count() == 0
    assert _trabajos() == []
    assert AuditLog.query.filter_by(action='acceso_otorgado').count() == 0
    assert cola_falsa.ids() == []


def test_si_falla_la_auditoria_no_se_otorga(escena, cola_falsa, monkeypatch):
    def _falla(*args, **kwargs):
        raise RuntimeError('auditoría caída (simulada)')
    monkeypatch.setattr(services, 'add_audit_log', _falla)

    with pytest.raises(RuntimeError):
        services.otorgar(escena['usuario'], escena['plataforma'],
                         NIVEL_USUARIO, ORIGEN_SOLICITUD,
                         actor=escena['admin'], request_id=1)
    db.session.rollback()

    assert PlatformAccessGrant.query.count() == 0 and _trabajos() == []


def test_resultado_exitoso_del_worker_lleva_el_acceso_a_activo(
        escena, cola_falsa, proveedor_simulado):
    acceso = _otorgar(escena)

    assert cola_falsa.procesar() == ['exitoso']
    assert recargar(acceso.id).status == ESTADO_ACTIVO


def test_resultado_fallido_del_worker_lleva_el_acceso_a_fallido(
        escena, cola_falsa, proveedor_simulado, sin_correo):
    proveedor_simulado.resultados = [permanente('grupo_inexistente')]
    acceso = _otorgar(escena)

    assert cola_falsa.procesar() == ['fallido']
    assert recargar(acceso.id).status == ESTADO_FALLIDO


def test_no_se_duplica_un_acceso_vigente(escena, cola_falsa):
    _otorgar(escena)

    with pytest.raises(ErrorDeAcceso) as info:
        _otorgar(escena)

    assert _codigo(info) == 'nivel_vigente'
    db.session.rollback()
    assert PlatformAccessGrant.query.count() == 1 and len(_trabajos()) == 1


def test_la_bd_impide_dos_vigentes_aunque_se_salte_el_servicio(escena):
    """Carrera: dos transacciones que pasan las reglas a la vez."""
    for _ in range(2):
        acceso = PlatformAccessGrant(
            user_id=escena['usuario'].id,
            platform_id=escena['plataforma'].id, level=NIVEL_USUARIO,
            origin=ORIGEN_SOLICITUD, status=ESTADO_EN_PROCESO)
        acceso.sincronizar_slots()
        db.session.add(acceso)
    with pytest.raises(IntegrityError):
        db.session.flush()
    db.session.rollback()


def test_la_bd_impide_dos_niveles_ocupantes_en_la_misma_plataforma(escena):
    for nivel in (NIVEL_USUARIO, NIVEL_ADMIN):
        acceso = PlatformAccessGrant(
            user_id=escena['usuario'].id,
            platform_id=escena['plataforma'].id, level=nivel,
            origin=ORIGEN_SOLICITUD, status=ESTADO_ACTIVO)
        acceso.sincronizar_slots()
        db.session.add(acceso)
    with pytest.raises(IntegrityError):
        db.session.flush()
    db.session.rollback()


def test_tras_revocado_se_puede_volver_a_otorgar(escena, cola_falsa,
                                                proveedor_simulado):
    acceso = _activar(escena, cola_falsa)
    services.revocar(acceso, actor=escena['admin'])
    db.session.commit()
    cola_falsa.procesar()
    assert recargar(acceso.id).status == ESTADO_REVOCADO

    nuevo = _otorgar(escena, request_id=42)

    assert nuevo.id != acceso.id and nuevo.status == ESTADO_EN_PROCESO


# --------------------------------------------------------------------------- #
# Revocar
# --------------------------------------------------------------------------- #

def test_revocar_activo_pasa_a_revocando_y_encola(escena, cola_falsa,
                                                 proveedor_simulado):
    acceso = _activar(escena, cola_falsa)

    services.revocar(acceso, actor=escena['admin'], motivo='  Ya no la usa ')
    db.session.commit()

    acceso = recargar(acceso.id)
    trabajo = _trabajos()[-1]
    assert acceso.status == ESTADO_REVOCANDO
    assert acceso.revoke_reason == 'Ya no la usa'
    assert acceso.revoked_by == escena['admin'].id
    assert (trabajo.operation, trabajo.access_id) == ('revocar', acceso.id)
    assert acceso.last_job_id == trabajo.id
    evento = AuditLog.query.filter_by(action='acceso_revocado').one()
    assert evento.before_state['status'] == ESTADO_ACTIVO
    assert evento.after_state['status'] == ESTADO_REVOCANDO

    cola_falsa.procesar()
    acceso = recargar(acceso.id)
    assert acceso.status == ESTADO_REVOCADO and acceso.revoked_at is not None


def test_revocar_sin_motivo_es_valido(escena, cola_falsa, proveedor_simulado):
    acceso = _activar(escena, cola_falsa)

    services.revocar(acceso, actor=escena['super'])
    db.session.commit()

    assert recargar(acceso.id).revoke_reason is None


def test_revocar_un_acceso_ya_revocado_no_encola_nada(
        escena, cola_falsa, proveedor_simulado):
    acceso = _activar(escena, cola_falsa)
    services.revocar(acceso, actor=escena['admin'])
    db.session.commit()
    cola_falsa.procesar()
    antes = len(_trabajos())

    with pytest.raises(ErrorDeAcceso) as info:
        services.revocar(recargar(acceso.id), actor=escena['admin'])

    assert _codigo(info) == 'estado_invalido'
    db.session.rollback()
    assert len(_trabajos()) == antes and cola_falsa.ids() == []


@pytest.mark.parametrize('estado', [ESTADO_EN_PROCESO, ESTADO_FALLIDO,
                                    ESTADO_REVOCANDO,
                                    ESTADO_FALLO_REVOCACION])
def test_solo_se_revoca_un_acceso_activo(escena, cola_falsa, estado):
    acceso = _otorgar(escena)
    acceso.status = estado
    acceso.sincronizar_slots()
    db.session.commit()

    with pytest.raises(ErrorDeAcceso) as info:
        services.revocar(acceso, actor=escena['admin'])

    assert _codigo(info) == 'estado_invalido'


def test_revocacion_fallida_pasa_a_fallo_revocacion(
        escena, cola_falsa, proveedor_simulado, sin_correo):
    acceso = _activar(escena, cola_falsa)
    services.revocar(acceso, actor=escena['admin'])
    db.session.commit()
    proveedor_simulado.resultados = [permanente('directorio')]

    cola_falsa.procesar()

    assert recargar(acceso.id).status == ESTADO_FALLO_REVOCACION


def test_motivo_de_mas_de_500_da_422(escena, cola_falsa, proveedor_simulado):
    acceso = _activar(escena, cola_falsa)

    with pytest.raises(ErrorDeAcceso) as info:
        services.revocar(acceso, actor=escena['admin'], motivo='x' * 501)

    assert _codigo(info) == 'validacion' and 'reason' in info.value.campos


# --------------------------------------------------------------------------- #
# Niveles (P5): un nivel por plataforma; subir reemplaza
# --------------------------------------------------------------------------- #

def test_subir_a_admin_reemplaza_al_de_usuario_en_una_transaccion(
        escena, cola_falsa, proveedor_simulado):
    usuario_ = _activar(escena, cola_falsa)

    admin_ = _otorgar(escena, NIVEL_ADMIN, request_id=50)

    anterior = recargar(usuario_.id)
    assert anterior.status == ESTADO_REVOCANDO
    assert anterior.revoke_reason == MOTIVO_REEMPLAZO
    assert recargar(admin_.id).status == ESTADO_EN_PROCESO
    operaciones = [(t.operation, t.level) for t in _trabajos()[-2:]]
    assert operaciones == [('revocar', NIVEL_USUARIO), ('otorgar', NIVEL_ADMIN)]

    cola_falsa.procesar()
    assert recargar(usuario_.id).status == ESTADO_REVOCADO
    assert recargar(admin_.id).status == ESTADO_ACTIVO


def test_con_admin_vigente_no_se_otorga_usuario(escena, cola_falsa,
                                               proveedor_simulado):
    _activar(escena, cola_falsa, NIVEL_ADMIN)

    with pytest.raises(ErrorDeAcceso) as info:
        _otorgar(escena, NIVEL_USUARIO, request_id=51)

    assert _codigo(info) == 'nivel_vigente'


def test_no_se_sube_si_el_acceso_actual_no_esta_activo(escena, cola_falsa):
    _otorgar(escena)  # sigue en_proceso

    with pytest.raises(ErrorDeAcceso) as info:
        _otorgar(escena, NIVEL_ADMIN, request_id=52)

    assert _codigo(info) == 'estado_invalido'


def test_no_se_otorga_un_nivel_con_su_revocacion_en_curso(
        escena, cola_falsa, proveedor_simulado):
    acceso = _activar(escena, cola_falsa)
    services.revocar(acceso, actor=escena['admin'])
    db.session.commit()

    with pytest.raises(ErrorDeAcceso) as info:
        _otorgar(escena, request_id=53)

    assert _codigo(info) == 'estado_invalido'


# --------------------------------------------------------------------------- #
# Alcance (SEC-AUTHZ-03/06/07/08) y superadmin (P6)
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('usuario, actor, codigo', [
    ('usuario', 'admin_otra', 'no_encontrado'),   # admin de área ajena
    ('ajeno', 'admin', 'no_encontrado'),          # cuenta fuera de sus áreas
    ('ajeno', 'super', 'no_encontrado'),          # P1: no es del área
    ('admin2', 'admin', 'no_encontrado'),         # otro admin (SEC-AUTHZ-06)
    ('super', 'admin', 'acceso_por_defecto'),     # P6
    ('usuario', 'usuario', 'operacion_propia'),   # SEC-AUTHZ-08
])
def test_otorgar_denegado(escena, cola_falsa, usuario, actor, codigo):
    with pytest.raises(ErrorDeAcceso) as info:
        _otorgar(escena, usuario=usuario, actor=actor)

    assert _codigo(info) == codigo
    db.session.rollback()
    assert PlatformAccessGrant.query.count() == 0 and _trabajos() == []


@pytest.mark.parametrize('actor', ['admin', 'super'])
def test_otorgar_permitido(escena, cola_falsa, actor):
    assert _otorgar(escena, actor=actor).status == ESTADO_EN_PROCESO


def test_solicitud_sin_request_id_da_422(escena, cola_falsa):
    with pytest.raises(ErrorDeAcceso) as info:
        _otorgar(escena, request_id=None)

    assert info.value.campos == {'request_id': 'Falta la solicitud.'}


def test_acceso_automatico_del_admin_lo_otorga_el_sistema(escena, cola_falsa):
    acceso = services.otorgar(escena['admin'], escena['plataforma'],
                              NIVEL_USUARIO, ORIGEN_ADMIN_DE_AREA)
    db.session.commit()

    assert (acceso.origin, acceso.granted_by) == (ORIGEN_ADMIN_DE_AREA, None)
    evento = AuditLog.query.filter_by(action='acceso_otorgado').one()
    assert evento.user == 'sistema' and evento.actor_id is None


@pytest.mark.parametrize('usuario, nivel, codigo', [
    ('usuario', NIVEL_USUARIO, 'no_encontrado'),    # no administra el área
    ('admin_otra', NIVEL_USUARIO, 'no_encontrado'),
    ('admin', NIVEL_ADMIN, 'validacion'),           # P6: nivel usuario
])
def test_acceso_automatico_denegado(escena, cola_falsa, usuario, nivel,
                                    codigo):
    with pytest.raises(ErrorDeAcceso) as info:
        services.otorgar(escena[usuario], escena['plataforma'], nivel,
                         ORIGEN_ADMIN_DE_AREA)

    assert _codigo(info) == codigo


def test_acceso_automatico_con_actor_humano_se_rechaza(escena, cola_falsa):
    with pytest.raises(ErrorDeAcceso):
        services.otorgar(escena['admin'], escena['plataforma'],
                         NIVEL_USUARIO, ORIGEN_ADMIN_DE_AREA,
                         actor=escena['super'])


@pytest.mark.parametrize('actor, codigo', [
    ('usuario', 'operacion_propia'),
    ('admin_otra', 'no_encontrado'),
])
def test_revocar_denegado(escena, cola_falsa, proveedor_simulado, actor,
                          codigo):
    acceso = _activar(escena, cola_falsa)

    with pytest.raises(ErrorDeAcceso) as info:
        services.revocar(acceso, actor=escena[actor])

    assert _codigo(info) == codigo
    assert recargar(acceso.id).status == ESTADO_ACTIVO


def test_admin_no_revoca_acceso_automatico_de_otro_admin(
        escena, cola_falsa, proveedor_simulado):
    acceso = services.otorgar(escena['admin2'], escena['plataforma'],
                              NIVEL_USUARIO, ORIGEN_ADMIN_DE_AREA)
    db.session.commit()
    cola_falsa.procesar()

    with pytest.raises(ErrorDeAcceso) as info:
        services.revocar(recargar(acceso.id), actor=escena['admin'])
    assert _codigo(info) == 'no_encontrado'

    services.revocar(recargar(acceso.id), actor=escena['super'])
    db.session.commit()
    assert recargar(acceso.id).status == ESTADO_REVOCANDO


def test_el_sistema_revoca_sin_actor(escena, cola_falsa, proveedor_simulado):
    acceso = services.otorgar(escena['admin'], escena['plataforma'],
                              NIVEL_USUARIO, ORIGEN_ADMIN_DE_AREA)
    db.session.commit()
    cola_falsa.procesar()

    services.revocar(recargar(acceso.id))
    db.session.commit()

    acceso = recargar(acceso.id)
    assert acceso.status == ESTADO_REVOCANDO and acceso.revoked_by is None


# --------------------------------------------------------------------------- #
# Transiciones y reintento (FNC-062)
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize('origen, destino, valido', [
    (ESTADO_EN_PROCESO, ESTADO_ACTIVO, True),
    (ESTADO_EN_PROCESO, ESTADO_FALLIDO, True),
    (ESTADO_ACTIVO, ESTADO_REVOCANDO, True),
    (ESTADO_FALLIDO, ESTADO_EN_PROCESO, True),
    (ESTADO_REVOCANDO, ESTADO_REVOCADO, True),
    (ESTADO_REVOCANDO, ESTADO_FALLO_REVOCACION, True),
    (ESTADO_FALLO_REVOCACION, ESTADO_REVOCANDO, True),
    (ESTADO_REVOCADO, ESTADO_EN_PROCESO, False),
    (ESTADO_REVOCADO, ESTADO_REVOCANDO, False),
    (ESTADO_EN_PROCESO, ESTADO_REVOCANDO, False),
    (ESTADO_FALLIDO, ESTADO_ACTIVO, False),
    (ESTADO_ACTIVO, ESTADO_REVOCADO, False),
])
def test_transiciones(origen, destino, valido):
    assert rules.puede_pasar(origen, destino) is valido


def test_resultado_tardio_no_fuerza_un_estado_invalido(
        escena, cola_falsa, proveedor_simulado):
    """SEC-CON-09: un éxito de otorgar sobre un acceso revocado no lo
    reactiva."""
    acceso = _activar(escena, cola_falsa)
    trabajo = db.session.get(ProvisioningJob, acceso.last_job_id)
    acceso.status = ESTADO_REVOCADO
    acceso.sincronizar_slots()
    db.session.commit()

    from app.modules.access.manejadores import al_exito
    al_exito(trabajo)

    assert acceso.status == ESTADO_REVOCADO


def test_reabrir_un_otorgar_fallido_devuelve_el_acceso_a_en_proceso(
        escena, cola_falsa, proveedor_simulado, sin_correo, app):
    proveedor_simulado.resultados = [permanente('grupo_inexistente')]
    acceso = _otorgar(escena)
    cola_falsa.procesar()
    trabajo = db.session.get(ProvisioningJob, acceso.last_job_id)

    from app.modules.provisioning.configuracion import cargar_configuracion
    ejecucion.reabrir(trabajo, cargar_configuracion())
    services.reabrir_acceso(trabajo)
    db.session.commit()

    assert recargar(acceso.id).status == ESTADO_EN_PROCESO
    assert ejecucion.ejecutar_trabajo(trabajo.id) == 'exitoso'
    assert recargar(acceso.id).status == ESTADO_ACTIVO


def test_reabrir_un_acceso_que_no_fallo_da_estado_invalido(
        escena, cola_falsa, proveedor_simulado):
    acceso = _activar(escena, cola_falsa)
    trabajo = db.session.get(ProvisioningJob, acceso.last_job_id)

    with pytest.raises(ErrorDeAcceso):
        services.reabrir_acceso(trabajo)
