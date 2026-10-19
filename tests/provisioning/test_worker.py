"""Barrido, bucle del worker, apagado ordenado y comando (FNC-049)."""
import signal
from datetime import timedelta


from app import db
from app.modules.provisioning import cli, worker
from app.modules.provisioning.configuracion import cargar_configuracion
from app.modules.provisioning.ejecucion import sentencia_reserva
from app.modules.provisioning.models import ProvisioningJob
from app.modules.provisioning.reloj import ahora
from app.modules.provisioning.tipos import ESTADO_EXITOSO, ESTADO_REINTENTANDO
from app.modules.provisioning.worker import (ControlApagado,
                                             WorkerAprovisionamiento, barrer,
                                             ejecutar)


def test_barrido_envia_solo_lo_vencido(nuevo_trabajo, cola_falsa):
    cfg = cargar_configuracion()
    pendiente = nuevo_trabajo('a')
    en_espera = nuevo_trabajo('b')
    terminado = nuevo_trabajo('c')
    reservado = nuevo_trabajo('d')
    abandonado = nuevo_trabajo('e')
    jobs = {i: db.session.get(ProvisioningJob, i) for i in
            (en_espera, terminado)}
    jobs[en_espera].status = ESTADO_REINTENTANDO
    jobs[en_espera].next_attempt_at = ahora() + timedelta(minutes=5)
    jobs[terminado].status = ESTADO_EXITOSO
    db.session.commit()
    # Misma terna: se reservan a mano (la reserva real exige orden).
    for trabajo_id, worker_id, momento in (
            (reservado, 'w1', ahora()),
            (abandonado, 'w0',
             ahora() - timedelta(seconds=cfg.vencimiento_reserva + 1))):
        db.session.execute(sentencia_reserva(trabajo_id, worker_id, cfg,
                                             momento))
    db.session.commit()
    cola_falsa.mensajes.clear()

    assert barrer(cola_falsa, cfg) == 2
    assert sorted(cola_falsa.ids()) == sorted([pendiente, abandonado])


class WorkerFalso:
    creados = []

    def __init__(self, colas, connection=None, control=None, **opciones):
        self.control = control
        WorkerFalso.creados.append(self)

    def work(self, max_idle_time=None, with_scheduler=False):
        self.max_idle_time = max_idle_time
        if len(WorkerFalso.creados) >= 2:
            self.control.pedir()  # simula SIGTERM durante el segundo ciclo


def test_bucle_barre_trabaja_y_se_detiene(app, cola_falsa, monkeypatch):
    WorkerFalso.creados = []
    barridos = []
    monkeypatch.setattr(worker, 'barrer',
                        lambda cola, cfg: barridos.append(cola) or 0)
    cfg = cargar_configuracion()

    ejecutar(cola_falsa, cfg, ControlApagado(), clase_worker=WorkerFalso)

    assert len(barridos) == 2 and len(WorkerFalso.creados) == 2
    assert WorkerFalso.creados[0].max_idle_time == cfg.intervalo_barrido


def test_bucle_sobrevive_a_un_fallo_de_redis(app, cola_falsa, monkeypatch):
    control = ControlApagado()
    llamadas = []

    def _barrer(cola, cfg):
        llamadas.append(1)
        if len(llamadas) == 1:
            raise ConnectionError('redis')
        control.pedir()
        return 0
    monkeypatch.setattr(worker, 'barrer', _barrer)
    monkeypatch.setattr(control, 'esperar', lambda segundos: None)

    ejecutar(cola_falsa, cargar_configuracion(), control,
             clase_worker=WorkerFalso)

    assert len(llamadas) == 2


def test_senal_de_apagado_pide_detener(app):
    control = ControlApagado()
    anteriores = {s: signal.getsignal(s) for s in worker.SENALES_APAGADO}
    try:
        worker.instalar_senales(control)
        signal.getsignal(signal.SIGTERM)(signal.SIGTERM, None)
    finally:
        for senal, manejador in anteriores.items():
            signal.signal(senal, manejador)
    assert control.detener


def test_request_stop_de_rq_tambien_detiene_el_bucle(monkeypatch):
    control = ControlApagado()
    monkeypatch.setattr(worker.SimpleWorker, 'request_stop',
                        lambda self, signum, frame: None)
    instancia = WorkerAprovisionamiento.__new__(WorkerAprovisionamiento)
    instancia.control = control

    instancia.request_stop(signal.SIGTERM, None)

    assert control.detener


def test_comando_sin_redis_pass_sale_con_mensaje(app):
    resultado = app.test_cli_runner().invoke(args=['provisioning', 'worker'])

    assert resultado.exit_code == 1
    assert 'REDIS_PASS es obligatoria' in resultado.output


def test_comando_con_redis_caido_sale_con_mensaje(app, monkeypatch):
    monkeypatch.setenv('REDIS_PASS', 'Ficticia-Redis-1')

    class SinRedis:
        def ping(self):
            raise ConnectionError('host.ejemplo.local:6379')
    monkeypatch.setattr(cli, 'conexion_redis', lambda: SinRedis())

    resultado = app.test_cli_runner().invoke(args=['provisioning', 'worker'])

    assert resultado.exit_code == 1
    assert 'No se pudo conectar con Redis (ConnectionError)' in resultado.output
    assert 'host.ejemplo.local' not in resultado.output


def test_comando_lanza_el_bucle(app, monkeypatch):
    monkeypatch.setenv('REDIS_PASS', 'Ficticia-Redis-1')

    class ConRedis:
        def ping(self):
            return True
    llamadas = []
    monkeypatch.setattr(cli, 'conexion_redis', lambda: ConRedis())
    monkeypatch.setattr(cli, 'ejecutar',
                        lambda cola, cfg: llamadas.append((cola.name, cfg)))

    resultado = app.test_cli_runner().invoke(args=['provisioning', 'worker'])

    assert resultado.exit_code == 0, resultado.output
    assert llamadas[0][0] == 'aprovisionamiento'


def test_conexion_redis_con_contrasena_y_tiempos_de_espera(monkeypatch):
    from app.modules.provisioning.queue import (TIEMPO_ESPERA_REDIS_SEGUNDOS,
                                                conexion_redis)
    monkeypatch.setenv('REDIS_PASS', 'Ficticia-Redis-1')
    opciones = conexion_redis().connection_pool.connection_kwargs
    assert opciones['password'] == 'Ficticia-Redis-1'
    assert opciones['socket_connect_timeout'] == TIEMPO_ESPERA_REDIS_SEGUNDOS
