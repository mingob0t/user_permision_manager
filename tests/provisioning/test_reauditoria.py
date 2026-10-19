"""Regresiones de la re-auditoría de seguridad de FNC-049.

- Media: `reabrir()` no puede saltarse una revocación posterior de la terna,
  y un trabajo reabierto espera a cualquier trabajo de su terna en curso.
- Baja: un mensaje RQ con *callbacks* se rechaza (importarían código).
"""
import pytest

from app import db
from app.modules.provisioning.configuracion import cargar_configuracion
from app.modules.provisioning.ejecucion import (EstadoInvalido,
                                                ejecutar_trabajo, reabrir,
                                                sentencia_reserva)
from app.modules.provisioning.models import ProvisioningJob
from app.modules.provisioning.providers import permanente
from app.modules.provisioning.queue import FUNCION_TRABAJO
from app.modules.provisioning.reloj import ahora
from app.modules.provisioning.tipos import (ESTADO_EXITOSO, ESTADO_FALLIDO,
                                            OPERACION_REVOCAR)
from app.modules.provisioning.worker import mensaje_valido


def trabajo(trabajo_id):
    return db.session.get(ProvisioningJob, trabajo_id, populate_existing=True)


def test_reabrir_un_otorgar_con_revocacion_posterior_se_rechaza(
        nuevo_trabajo, proveedor_simulado, avisos):
    proveedor_simulado.resultados = [permanente('grupo_inexistente')]
    otorgar = nuevo_trabajo('otorgar-1')
    assert ejecutar_trabajo(otorgar) == ESTADO_FALLIDO
    revocar = nuevo_trabajo('revocar-1', operacion=OPERACION_REVOCAR)
    assert ejecutar_trabajo(revocar) == ESTADO_EXITOSO

    with pytest.raises(EstadoInvalido):
        reabrir(trabajo(otorgar), cargar_configuracion())
    db.session.rollback()

    assert trabajo(otorgar).status == ESTADO_FALLIDO
    assert ejecutar_trabajo(otorgar) is None
    assert [n for n, _ in proveedor_simulado.llamadas] == ['otorgar',
                                                          'revocar']


def test_reabierto_espera_a_un_trabajo_posterior_en_curso(
        nuevo_trabajo, proveedor_simulado, avisos):
    cfg = cargar_configuracion()
    proveedor_simulado.resultados = [permanente('grupo_inexistente')]
    primero = nuevo_trabajo('otorgar-1')
    assert ejecutar_trabajo(primero) == ESTADO_FALLIDO
    posterior = nuevo_trabajo('otorgar-2')
    db.session.execute(sentencia_reserva(posterior, 'worker-b', cfg, ahora()))
    db.session.commit()

    reabrir(trabajo(primero), cfg)
    db.session.commit()

    assert ejecutar_trabajo(primero) is None
    assert len(proveedor_simulado.llamadas) == 1


class Mensaje:
    def __init__(self, **callbacks):
        self.func_name, self.args, self.kwargs = FUNCION_TRABAJO, (7,), {}
        self._success_callback_name = callbacks.get('exito')
        self._failure_callback_name = callbacks.get('fallo')
        self._stopped_callback_name = callbacks.get('detenido')


@pytest.mark.parametrize('callbacks', [{'exito': 'os.system'},
                                       {'fallo': 'os.system'},
                                       {'detenido': 'os.system'}])
def test_mensaje_con_callback_se_rechaza(callbacks):
    assert mensaje_valido(Mensaje()) is True
    assert mensaje_valido(Mensaje(**callbacks)) is False
