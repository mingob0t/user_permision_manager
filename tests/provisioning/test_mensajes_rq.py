"""Regresión (auditor-seguridad, Media): el worker solo ejecuta su propia función.

Quien pueda escribir en Redis no debe poder hacer ejecutar código: mensajes en
JSON (sin pickle) y, antes de ejecutar, la función y los argumentos se validan.
"""
import pytest
import redis
from rq.serializers import JSONSerializer

from app.modules.provisioning import worker
from app.modules.provisioning.queue import FUNCION_TRABAJO, cola
from app.modules.provisioning.worker import (ControlApagado,
                                             WorkerAprovisionamiento)


class MensajeFalso:
    def __init__(self, func_name, args=(), kwargs=None, roto=False):
        self._func_name, self._roto = func_name, roto
        self.args, self.kwargs = args, kwargs or {}
        self.id = 'msg-1'
        self.borrado = False

    @property
    def func_name(self):
        if self._roto:
            raise ValueError('datos que no se pueden deserializar')
        return self._func_name

    def delete(self):
        self.borrado = True


@pytest.fixture
def ejecutados(monkeypatch):
    llamadas = []
    monkeypatch.setattr(worker.SimpleWorker, 'execute_job',
                        lambda self, job, queue: llamadas.append(job))
    return llamadas


@pytest.fixture
def instancia():
    w = WorkerAprovisionamiento.__new__(WorkerAprovisionamiento)
    w.control = ControlApagado()
    w.set_state = lambda estado: None
    return w


def test_la_cola_usa_json(app):
    q = cola(conexion=redis.Redis())
    assert q.serializer is JSONSerializer or isinstance(q.serializer,
                                                        JSONSerializer)


def test_mensaje_propio_se_ejecuta(instancia, ejecutados):
    mensaje = MensajeFalso(FUNCION_TRABAJO, (7,))
    instancia.execute_job(mensaje, None)
    assert ejecutados == [mensaje]


@pytest.mark.parametrize('mensaje', [
    MensajeFalso('os.system', ('rm -rf /',)),
    MensajeFalso(FUNCION_TRABAJO, ('7',)),
    MensajeFalso(FUNCION_TRABAJO, (True,)),
    MensajeFalso(FUNCION_TRABAJO, (7, 8)),
    MensajeFalso(FUNCION_TRABAJO, ()),
    MensajeFalso(FUNCION_TRABAJO, (7,), {'worker': 'otro'}),
    MensajeFalso(FUNCION_TRABAJO, roto=True),
], ids=['funcion-ajena', 'texto', 'bool', 'dos-args', 'sin-args', 'kwargs',
        'ilegible'])
def test_mensaje_ajeno_o_invalido_se_descarta_sin_ejecutar(instancia,
                                                           ejecutados,
                                                           mensaje):
    instancia.execute_job(mensaje, None)  # no lanza
    assert ejecutados == []
    assert mensaje.borrado


def test_el_bucle_crea_el_worker_con_json(app, monkeypatch):
    from app.modules.provisioning.configuracion import cargar_configuracion
    recibidos = {}
    control = ControlApagado()

    class Capturador:
        def __init__(self, colas, **kwargs):
            recibidos.update(kwargs)

        def work(self, **kwargs):
            control.pedir()

    monkeypatch.setattr(worker, 'barrer', lambda c, cfg: 0)

    class Cola:
        connection = object()
    worker.ejecutar(Cola(), cargar_configuracion(), control,
                    clase_worker=Capturador)
    assert recibidos['serializer'] is JSONSerializer
