"""Regresiones de la revisión de FNC-049.

- auditor-seguridad (Media): revocar cancela los otorgar en espera de la misma
  terna y un trabajo no corre si hay uno anterior de la terna sin terminar.
- auditor-seguridad (Baja): el cierre comprueba que la reserva sigue siendo
  propia.
- revisor (Media): el tope de intentos al reservar solo aplica a reservas
  vencidas; un trabajo reabierto (reintento manual, FNC-062) se ejecuta.
"""
from datetime import timedelta

from app import db
from app.modules.audit.models import AuditLog
from app.modules.provisioning.configuracion import cargar_configuracion
from app.modules.provisioning.ejecucion import ejecutar_trabajo, reabrir
from app.modules.provisioning.models import ProvisioningJob
from app.modules.provisioning.providers import (ResultadoProveedor,
                                                permanente, transitorio)
from app.modules.provisioning.reloj import ahora
from app.modules.provisioning.tipos import (ESTADO_CANCELADO,
                                            ESTADO_EXITOSO, ESTADO_FALLIDO,
                                            ESTADO_REINTENTANDO,
                                            OPERACION_REVOCAR,
                                            RESULTADO_EXITOSO)


def trabajo(trabajo_id):
    return db.session.get(ProvisioningJob, trabajo_id, populate_existing=True)


def adelantar(trabajo_id):
    t = trabajo(trabajo_id)
    t.next_attempt_at = ahora() - timedelta(seconds=1)
    db.session.commit()


def test_revocar_cancela_el_otorgar_en_reintento(nuevo_trabajo,
                                                 proveedor_simulado):
    proveedor_simulado.resultados = [transitorio('directorio')]
    otorgar = nuevo_trabajo('otorgar-1')
    assert ejecutar_trabajo(otorgar) == ESTADO_REINTENTANDO

    revocar = nuevo_trabajo('revocar-1', operacion=OPERACION_REVOCAR)

    t = trabajo(otorgar)
    assert (t.status, t.next_attempt_at) == (ESTADO_CANCELADO, None)
    assert t.finished_at is not None
    registro = AuditLog.query.order_by(AuditLog.id.desc()).first()
    assert registro.action == 'ejecucion_cancelada'
    # El reintento del otorgar ya no corre: la persona no vuelve a entrar.
    adelantar(otorgar)
    assert ejecutar_trabajo(otorgar) is None
    assert ejecutar_trabajo(revocar) == ESTADO_EXITOSO
    assert [n for n, _ in proveedor_simulado.llamadas] == ['otorgar',
                                                          'revocar']


def test_revocar_no_cancela_otra_terna_ni_lo_terminado(datos, nuevo_trabajo,
                                                       proveedor_simulado):
    hecho = nuevo_trabajo('otorgar-hecho')
    ejecutar_trabajo(hecho)
    otro_nivel = nuevo_trabajo('otorgar-admin', nivel='admin')

    nuevo_trabajo('revocar-1', operacion=OPERACION_REVOCAR)

    assert trabajo(hecho).status == ESTADO_EXITOSO
    assert trabajo(otro_nivel).status == 'pendiente'


def test_no_corre_si_hay_uno_anterior_de_la_terna_sin_terminar(
        nuevo_trabajo, proveedor_simulado):
    revocar = nuevo_trabajo('revocar-1', operacion=OPERACION_REVOCAR)
    otorgar = nuevo_trabajo('otorgar-2')

    assert ejecutar_trabajo(otorgar) is None
    assert ejecutar_trabajo(revocar) == ESTADO_EXITOSO
    assert ejecutar_trabajo(otorgar) == ESTADO_EXITOSO
    assert [n for n, _ in proveedor_simulado.llamadas] == ['revocar',
                                                          'otorgar']


def test_el_cierre_comprueba_que_la_reserva_sigue_siendo_propia(
        nuevo_trabajo, proveedor_simulado):
    """El worker A se pasa del vencimiento; B retoma y cierra; A no pisa."""
    cfg = cargar_configuracion()
    trabajo_id = nuevo_trabajo()

    def _a_se_pasa_del_vencimiento():
        t = trabajo(trabajo_id)
        t.locked_at = ahora() - timedelta(seconds=cfg.vencimiento_reserva + 1)
        db.session.commit()
        assert ejecutar_trabajo(trabajo_id, worker='worker-b') == ESTADO_EXITOSO
        return transitorio('directorio')  # respuesta tardía de A

    proveedor_simulado.resultados = [_a_se_pasa_del_vencimiento,
                                     ResultadoProveedor(RESULTADO_EXITOSO)]

    assert ejecutar_trabajo(trabajo_id, worker='worker-a') is None

    t = trabajo(trabajo_id)
    assert t.status == ESTADO_EXITOSO
    assert [i.result for i in t.attempts] == ['error_transitorio', 'exitoso']


def test_reabrir_un_fallido_permite_ejecutarlo(nuevo_trabajo,
                                               proveedor_simulado, avisos,
                                               monkeypatch):
    monkeypatch.setenv('PROVISIONING_MAX_ATTEMPTS', '1')
    proveedor_simulado.resultados = [permanente('grupo_inexistente')]
    trabajo_id = nuevo_trabajo()
    assert ejecutar_trabajo(trabajo_id) == ESTADO_FALLIDO

    reabrir(trabajo(trabajo_id), cargar_configuracion())
    db.session.commit()

    t = trabajo(trabajo_id)
    assert (t.status, t.max_attempts, t.finished_at) == ('pendiente', 2, None)
    assert ejecutar_trabajo(trabajo_id) == ESTADO_EXITOSO
    assert trabajo(trabajo_id).attempts_count == 2


def test_pendiente_con_el_tope_alcanzado_igual_ejecuta_un_intento(
        nuevo_trabajo, proveedor_simulado):
    trabajo_id = nuevo_trabajo()
    t = trabajo(trabajo_id)
    t.attempts_count = t.max_attempts
    db.session.commit()

    assert ejecutar_trabajo(trabajo_id) == ESTADO_EXITOSO
    assert len(proveedor_simulado.llamadas) == 1
