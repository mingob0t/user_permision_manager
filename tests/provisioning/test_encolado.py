"""Encolado transaccional, aviso al worker e idempotencia (FNC-049)."""
import pytest

from app import db
from app.modules.platforms.tipos import NIVEL_ADMIN, NIVEL_USUARIO, TIPO_CONECTOR
from app.modules.provisioning import queue
from app.modules.provisioning.ejecucion import ejecutar_trabajo
from app.modules.provisioning.models import ProvisioningJob
from app.modules.provisioning.queue import (FUNCION_TRABAJO,
                                            DatosDeTrabajoInvalidos, encolar)
from app.modules.provisioning.tipos import (ESTADO_EXITOSO, ESTADO_PENDIENTE,
                                            OPERACION_OTORGAR)
from tests import fabricas


def test_encolar_no_hace_commit_y_el_rollback_lo_descarta(datos, cola_falsa):
    _, plataforma, usuario = datos
    encolar(OPERACION_OTORGAR, usuario.id, plataforma, NIVEL_USUARIO, 'k1')
    db.session.rollback()

    assert ProvisioningJob.query.count() == 0
    assert cola_falsa.mensajes == []


def test_tras_el_commit_despierta_al_worker_con_el_id(datos, cola_falsa):
    _, plataforma, usuario = datos
    trabajo = encolar(OPERACION_OTORGAR, usuario.id, plataforma, NIVEL_ADMIN,
                      'k1', access_id=5)
    assert cola_falsa.mensajes == []  # todavía no hay commit
    db.session.commit()

    assert cola_falsa.ids() == [trabajo.id]
    mensaje = cola_falsa.mensajes[0]
    assert mensaje.funcion == FUNCION_TRABAJO
    assert mensaje.kwargs['job_timeout'] == 60
    guardado = db.session.get(ProvisioningJob, trabajo.id)
    assert (guardado.status, guardado.provider, guardado.level) == (
        ESTADO_PENDIENTE, 'ldap', NIVEL_ADMIN)
    assert (guardado.area_id, guardado.platform_id, guardado.access_id) == (
        plataforma.area_id, plataforma.id, 5)
    assert guardado.max_attempts == 5


def test_misma_clave_devuelve_el_mismo_trabajo(datos, cola_falsa):
    _, plataforma, usuario = datos
    primero = encolar(OPERACION_OTORGAR, usuario.id, plataforma,
                      NIVEL_USUARIO, 'k1')
    db.session.commit()
    segundo = encolar(OPERACION_OTORGAR, usuario.id, plataforma,
                      NIVEL_USUARIO, 'k1')
    db.session.commit()

    assert segundo.id == primero.id
    assert ProvisioningJob.query.count() == 1
    assert cola_falsa.ids() == [primero.id]


def test_misma_clave_dos_veces_se_ejecuta_una_vez(nuevo_trabajo, cola_falsa,
                                                  proveedor_simulado):
    nuevo_trabajo('k1')
    nuevo_trabajo('k1')
    queue.despertar(cola_falsa.ids())  # aviso repetido del mismo trabajo

    estados = cola_falsa.procesar()

    assert estados.count(ESTADO_EXITOSO) == 1
    assert len(proveedor_simulado.llamadas) == 1


def test_sin_redis_el_commit_sigue_y_el_trabajo_espera(datos, monkeypatch):
    def _sin_redis(conexion=None, **_):
        raise ConnectionError('redis caído')
    monkeypatch.setattr(queue, 'cola', _sin_redis)
    _, plataforma, usuario = datos

    trabajo = encolar(OPERACION_OTORGAR, usuario.id, plataforma,
                      NIVEL_USUARIO, 'k1')
    db.session.commit()

    assert db.session.get(ProvisioningJob, trabajo.id).status == ESTADO_PENDIENTE


def test_sin_redis_pass_no_avisa_y_no_falla(datos):
    # Sin REDIS_PASS (las pruebas lo quitan), `cola()` real no se conecta.
    _, plataforma, usuario = datos
    encolar(OPERACION_OTORGAR, usuario.id, plataforma, NIVEL_USUARIO, 'k1')
    db.session.commit()

    assert ProvisioningJob.query.count() == 1


def test_proveedor_sale_del_tipo_de_integracion(datos, cola_falsa):
    area, _, usuario = datos
    plataforma = fabricas.crear_plataforma(area, integration_type=TIPO_CONECTOR)
    trabajo = encolar('revocar', usuario.id, plataforma, NIVEL_USUARIO, 'k2')
    db.session.commit()

    assert trabajo.provider == 'conector'


@pytest.mark.parametrize('operacion, nivel, clave', [
    ('borrar', NIVEL_USUARIO, 'k'),
    (OPERACION_OTORGAR, 'superadmin', 'k'),
    (OPERACION_OTORGAR, NIVEL_USUARIO, ''),
    (OPERACION_OTORGAR, NIVEL_USUARIO, 'x' * 101),
])
def test_datos_invalidos_se_rechazan(datos, operacion, nivel, clave):
    _, plataforma, usuario = datos
    with pytest.raises(DatosDeTrabajoInvalidos):
        encolar(operacion, usuario.id, plataforma, nivel, clave)


def test_la_funcion_del_mensaje_es_la_del_ejecutor():
    from rq.utils import import_attribute
    assert import_attribute(FUNCION_TRABAJO) is ejecutar_trabajo


def test_despertar_desde_la_web_usa_un_tiempo_de_espera_corto(monkeypatch):
    """Regresión (revisor, Baja): Redis caído no frena el commit 5 s."""
    from app.modules.provisioning.queue import TIEMPO_ESPERA_REDIS_WEB_SEGUNDOS
    monkeypatch.setenv('REDIS_PASS', 'Ficticia-Redis-1')
    original = queue.cola
    usadas = []

    def _cola(conexion=None, **opciones):
        cola_real = original(conexion, **opciones)
        usadas.append(cola_real.connection.connection_pool.connection_kwargs)
        raise ConnectionError('sin redis')
    monkeypatch.setattr(queue, 'cola', _cola)

    queue.despertar([1])

    assert usadas[0]['socket_timeout'] == TIEMPO_ESPERA_REDIS_WEB_SEGUNDOS
    assert usadas[0]['socket_connect_timeout'] == TIEMPO_ESPERA_REDIS_WEB_SEGUNDOS
    assert TIEMPO_ESPERA_REDIS_WEB_SEGUNDOS <= 1
