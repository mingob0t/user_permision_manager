"""Ejecución: reintentos, errores permanentes, reserva, bitácora y avisos (FNC-049)."""
from datetime import timedelta

import pytest
from rq.timeouts import JobTimeoutException
from sqlalchemy.orm import Session

from app import db
from app.modules.audit.events import ACTOR_SISTEMA
from app.modules.audit.models import AuditLog
from app.modules.provisioning import ejecucion, manejadores
from app.modules.provisioning.configuracion import cargar_configuracion
from app.modules.provisioning.ejecucion import (ejecutar_trabajo, reservar,
                                                sentencia_reserva)
from app.modules.provisioning.models import ProvisioningJob
from app.modules.provisioning.providers import (ResultadoProveedor,
                                                permanente, transitorio)
from app.modules.provisioning.reloj import ahora
from app.modules.provisioning.tipos import (ESTADO_EN_EJECUCION,
                                            ESTADO_EXITOSO, ESTADO_FALLIDO,
                                            ESTADO_REINTENTANDO,
                                            OPERACION_REVOCAR,
                                            RESULTADO_ERROR_PERMANENTE,
                                            RESULTADO_ERROR_TRANSITORIO,
                                            RESULTADO_EXITOSO,
                                            RESULTADO_SIN_CAMBIOS)
from tests import fabricas

SECRETO_FICTICIO = 'Sup3r-Secreto-Ficticio'


def trabajo(trabajo_id):
    return db.session.get(ProvisioningJob, trabajo_id, populate_existing=True)


def adelantar(trabajo_id):
    """Pone el próximo intento en el pasado (simula que pasó la espera)."""
    t = trabajo(trabajo_id)
    t.next_attempt_at = ahora() - timedelta(seconds=1)
    db.session.commit()


def auditorias():
    return AuditLog.query.order_by(AuditLog.id).all()


def test_exito_cierra_audita_con_sistema_y_avisa_al_manejador(
        nuevo_trabajo, proveedor_simulado, avisos):
    exitos = []
    manejadores.registrar_manejador(on_success=lambda t: exitos.append(t.id))
    trabajo_id = nuevo_trabajo()

    assert ejecutar_trabajo(trabajo_id) == ESTADO_EXITOSO

    t = trabajo(trabajo_id)
    assert (t.status, t.attempts_count, t.locked_by) == (ESTADO_EXITOSO, 1, None)
    assert t.finished_at is not None
    assert [(i.number, i.result, i.error) for i in t.attempts] == [
        (1, RESULTADO_EXITOSO, None)]
    registro = auditorias()[-1]
    assert (registro.action, registro.user, registro.actor_id) == (
        'acceso_activo', ACTOR_SISTEMA, None)
    assert (registro.platform_id, registro.grant_id) == (t.platform_id, 77)
    assert exitos == [trabajo_id]
    assert avisos == []
    operacion = proveedor_simulado.llamadas[0][1]
    assert (operacion.id_operacion, operacion.clave_idempotencia) == (
        str(trabajo_id), 'clave-1')


def test_sin_cambios_cuenta_como_exito(nuevo_trabajo, proveedor_simulado):
    proveedor_simulado.resultados = [ResultadoProveedor(RESULTADO_SIN_CAMBIOS)]
    trabajo_id = nuevo_trabajo()

    assert ejecutar_trabajo(trabajo_id) == ESTADO_EXITOSO
    assert trabajo(trabajo_id).attempts[0].result == RESULTADO_SIN_CAMBIOS


def test_transitorio_reintenta_con_backoff_hasta_el_maximo_y_avisa(
        nuevo_trabajo, proveedor_simulado, avisos, monkeypatch):
    monkeypatch.setenv('PROVISIONING_MAX_ATTEMPTS', '3')
    monkeypatch.setenv('PROVISIONING_BACKOFF_BASE_SECONDS', '10')
    fallos = []
    manejadores.registrar_manejador(on_failure=lambda t: fallos.append(t.id))
    proveedor_simulado.resultados = [transitorio('directorio')] * 3
    trabajo_id = nuevo_trabajo()

    antes = ahora()
    assert ejecutar_trabajo(trabajo_id) == ESTADO_REINTENTANDO
    t = trabajo(trabajo_id)
    # Primer escalón: 10 s, con jitter entre 5 y 10 s.
    espera = (t.next_attempt_at - antes).total_seconds()
    assert 5 <= espera <= 11
    assert t.locked_at is None

    # Aún no le toca: no se ejecuta.
    assert ejecutar_trabajo(trabajo_id) is None
    assert len(proveedor_simulado.llamadas) == 1

    adelantar(trabajo_id)
    antes = ahora()
    assert ejecutar_trabajo(trabajo_id) == ESTADO_REINTENTANDO
    espera = (trabajo(trabajo_id).next_attempt_at - antes).total_seconds()
    assert 10 <= espera <= 21  # segundo escalón: 20 s

    adelantar(trabajo_id)
    assert ejecutar_trabajo(trabajo_id) == ESTADO_FALLIDO

    t = trabajo(trabajo_id)
    assert (t.status, t.attempts_count, t.next_attempt_at) == (
        ESTADO_FALLIDO, 3, None)
    assert [i.result for i in t.attempts] == [RESULTADO_ERROR_TRANSITORIO] * 3
    assert t.attempts[0].error == 'El directorio no respondió.'
    assert auditorias()[-1].action == 'acceso_fallido'
    assert fallos == [trabajo_id]
    assert avisos == [(t.user_id, t.platform_id, 'usuario', 'otorgar')]
    # Ya terminó: otro aviso del worker no hace nada.
    assert ejecutar_trabajo(trabajo_id) is None


def test_permanente_no_se_reintenta(nuevo_trabajo, proveedor_simulado, avisos):
    proveedor_simulado.resultados = [permanente('grupo_inexistente')]
    trabajo_id = nuevo_trabajo()

    assert ejecutar_trabajo(trabajo_id) == ESTADO_FALLIDO

    t = trabajo(trabajo_id)
    assert t.attempts_count == 1
    assert t.attempts[0].result == RESULTADO_ERROR_PERMANENTE
    assert t.attempts[0].error == 'El grupo no existe en el directorio.'
    assert len(avisos) == 1
    adelantar(trabajo_id)
    assert ejecutar_trabajo(trabajo_id) is None
    assert len(proveedor_simulado.llamadas) == 1


@pytest.mark.parametrize('resultado, evento', [
    (ResultadoProveedor(RESULTADO_EXITOSO), 'acceso_revocado'),
    (permanente('ultimo_miembro'), 'revocacion_fallida'),
])
def test_revocar_audita_su_evento(nuevo_trabajo, proveedor_simulado, avisos,
                                  resultado, evento):
    proveedor_simulado.resultados = [resultado]
    trabajo_id = nuevo_trabajo(operacion=OPERACION_REVOCAR)

    ejecutar_trabajo(trabajo_id)

    assert proveedor_simulado.llamadas[0][0] == 'revocar'
    assert auditorias()[-1].action == evento


def test_conector_sin_proveedor_falla_controlado(datos, nuevo_trabajo, avisos):
    area, _, _ = datos
    plataforma = fabricas.crear_plataforma(area, integration_type='conector')
    trabajo_id = nuevo_trabajo(plataforma_=plataforma)

    assert ejecutar_trabajo(trabajo_id) == ESTADO_FALLIDO

    intento = trabajo(trabajo_id).attempts[0]
    assert intento.result == RESULTADO_ERROR_PERMANENTE
    assert intento.error == 'El conector de la plataforma no está disponible.'
    assert len(avisos) == 1


def test_dos_workers_no_ejecutan_el_mismo_trabajo(app, nuevo_trabajo):
    """Dos procesos (dos sesiones sobre la misma BD) piden la misma reserva."""
    trabajo_id = nuevo_trabajo()
    cfg = cargar_configuracion()
    momento = ahora()

    with Session(db.engine) as worker_a, Session(db.engine) as worker_b:
        ganadas = []
        for sesion, nombre in ((worker_a, 'worker-a'), (worker_b, 'worker-b')):
            ganadas.append(sesion.execute(sentencia_reserva(
                trabajo_id, nombre, cfg, momento)).rowcount)
            sesion.commit()

    assert ganadas == [1, 0]
    t = trabajo(trabajo_id)
    assert (t.status, t.locked_by) == (ESTADO_EN_EJECUCION, 'worker-a')


def test_reserva_tomada_no_se_ejecuta_dos_veces(nuevo_trabajo,
                                                proveedor_simulado):
    trabajo_id = nuevo_trabajo()
    assert reservar(trabajo_id, 'worker-a', cargar_configuracion())
    db.session.commit()

    assert ejecutar_trabajo(trabajo_id, worker='worker-b') is None
    assert proveedor_simulado.llamadas == []


def test_reserva_vencida_se_retoma_y_cierra_el_intento_interrumpido(
        nuevo_trabajo, proveedor_simulado):
    trabajo_id = nuevo_trabajo()
    cfg = cargar_configuracion()
    hace_mucho = ahora() - timedelta(seconds=cfg.vencimiento_reserva + 1)
    assert reservar(trabajo_id, 'worker-caido', cfg, momento=hace_mucho)
    t = trabajo(trabajo_id)
    ejecucion._abrir_intento(t, hace_mucho)
    db.session.commit()

    assert ejecutar_trabajo(trabajo_id) == ESTADO_EXITOSO

    intentos = trabajo(trabajo_id).attempts
    assert [i.result for i in intentos] == [RESULTADO_ERROR_TRANSITORIO,
                                            RESULTADO_EXITOSO]
    assert intentos[0].error == 'El intento se interrumpió antes de terminar.'


def test_reserva_vencida_en_el_ultimo_intento_queda_fallido(
        nuevo_trabajo, proveedor_simulado, avisos, monkeypatch):
    monkeypatch.setenv('PROVISIONING_MAX_ATTEMPTS', '1')
    trabajo_id = nuevo_trabajo()
    cfg = cargar_configuracion()
    hace_mucho = ahora() - timedelta(seconds=cfg.vencimiento_reserva + 1)
    reservar(trabajo_id, 'worker-caido', cfg, momento=hace_mucho)
    ejecucion._abrir_intento(trabajo(trabajo_id), hace_mucho)
    db.session.commit()

    assert ejecutar_trabajo(trabajo_id) == ESTADO_FALLIDO
    assert proveedor_simulado.llamadas == []
    assert len(avisos) == 1


def test_el_error_guardado_no_contiene_secretos(nuevo_trabajo,
                                                proveedor_simulado,
                                                monkeypatch):
    monkeypatch.setenv('LDAP_BIND_PASSWORD', SECRETO_FICTICIO)
    proveedor_simulado.resultados = [permanente(
        'inesperado',
        detalle=(f'bind falló con {SECRETO_FICTICIO}; password=otro123 '
                 'token: abc.def https://admin:clave1@erp.ejemplo.local/x '
                 'Authorization: Bearer eyJhbGciOi\n' + 'x' * 600))]
    trabajo_id = nuevo_trabajo()

    ejecutar_trabajo(trabajo_id)

    error = trabajo(trabajo_id).attempts[0].error
    for secreto in (SECRETO_FICTICIO, 'otro123', 'abc.def', 'clave1',
                    'eyJhbGciOi', '\n'):
        assert secreto not in error
    assert len(error) <= 500


def test_excepcion_del_proveedor_no_guarda_su_texto(nuevo_trabajo,
                                                    proveedor_simulado):
    proveedor_simulado.resultados = [RuntimeError(f'falló {SECRETO_FICTICIO}')]
    trabajo_id = nuevo_trabajo()

    assert ejecutar_trabajo(trabajo_id) == ESTADO_REINTENTANDO

    intento = trabajo(trabajo_id).attempts[0]
    assert intento.result == RESULTADO_ERROR_TRANSITORIO
    assert intento.error == 'Error inesperado del proveedor.'


def test_tiempo_de_espera_de_rq_es_transitorio(nuevo_trabajo,
                                               proveedor_simulado):
    proveedor_simulado.resultados = [JobTimeoutException('60 s')]
    trabajo_id = nuevo_trabajo()

    assert ejecutar_trabajo(trabajo_id) == ESTADO_REINTENTANDO
    assert trabajo(trabajo_id).attempts[0].error == 'Tiempo de espera agotado.'


def test_manejador_con_error_revierte_y_no_audita(nuevo_trabajo,
                                                  proveedor_simulado, avisos):
    def _falla(_):
        raise RuntimeError('manejador roto')
    manejadores.registrar_manejador(on_success=_falla)
    trabajo_id = nuevo_trabajo()
    previas = len(auditorias())

    assert ejecutar_trabajo(trabajo_id) is None

    t = trabajo(trabajo_id)
    assert t.status == ESTADO_EN_EJECUCION  # se retoma al vencer la reserva
    assert len(auditorias()) == previas
    assert avisos == []


def test_fallo_del_aviso_no_cambia_el_resultado(nuevo_trabajo,
                                                proveedor_simulado,
                                                monkeypatch):
    def _roto(*_):
        raise RuntimeError('smtp')
    monkeypatch.setattr(ejecucion, 'notificar_aprovisionamiento_fallido', _roto)
    proveedor_simulado.resultados = [permanente('grupo_inexistente')]
    trabajo_id = nuevo_trabajo()

    assert ejecutar_trabajo(trabajo_id) == ESTADO_FALLIDO
    assert trabajo(trabajo_id).status == ESTADO_FALLIDO


def test_aviso_real_respeta_el_contrato_de_fnc048(nuevo_trabajo,
                                                  proveedor_simulado):
    """Sin doble: `notificar_aprovisionamiento_fallido` recibe datos válidos."""
    proveedor_simulado.resultados = [permanente('grupo_inexistente')]
    trabajo_id = nuevo_trabajo()

    # ENABLE_NOTIFICATIONS=false en pruebas: el aviso se omite sin error.
    assert ejecutar_trabajo(trabajo_id) == ESTADO_FALLIDO
