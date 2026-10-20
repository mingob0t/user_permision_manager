"""`accesos_vigentes` (plataformas) y `tiene_accesos_vigentes` (áreas)
conectados a los accesos reales (FNC-054). Regresiones: antes valían 0 y la
membresía en `user_areas`."""
import pytest

from app import db
from app.authz import ROLE_ADMIN
from app.modules.access import services
from app.modules.access.tipos import (ESTADO_ACTIVO, ESTADO_REVOCADO,
                                      ESTADOS_VIGENTES, ORIGEN_SOLICITUD)
from app.modules.areas.baja import tiene_accesos_vigentes
from app.modules.platforms.estado import accesos_vigentes
from app.modules.platforms.tipos import NIVEL_USUARIO
from tests import fabricas

A = '/api/v1'


@pytest.fixture
def acceso(escena, cola_falsa):
    acceso = services.otorgar(escena['usuario'], escena['plataforma'],
                              NIVEL_USUARIO, ORIGEN_SOLICITUD,
                              actor=escena['admin'], request_id=1)
    db.session.commit()
    return acceso


def _poner(acceso, estado):
    acceso.status = estado
    acceso.sincronizar_slots()
    db.session.commit()


@pytest.mark.parametrize('estado', ESTADOS_VIGENTES)
def test_cuenta_los_accesos_vigentes(escena, acceso, estado):
    _poner(acceso, estado)

    assert accesos_vigentes(escena['plataforma']) == 1
    assert escena['plataforma'].to_dict()['active_grants'] == 1
    assert tiene_accesos_vigentes(escena['area']) is True


def test_un_revocado_no_cuenta(escena, acceso):
    _poner(acceso, ESTADO_REVOCADO)

    assert accesos_vigentes(escena['plataforma']) == 0
    assert tiene_accesos_vigentes(escena['area']) is False
    assert tiene_accesos_vigentes(escena['otra']) is False


def test_cambiar_area_con_accesos_vigentes_da_409(escena, acceso,
                                                  cliente_como):
    _poner(acceso, ESTADO_ACTIVO)
    cliente = cliente_como(escena['super'])

    respuesta = cliente.put(f"{A}/platforms/{escena['plataforma'].id}",
                            json={'area_id': escena['otra'].id})

    assert respuesta.status_code == 409, respuesta.get_json()
    assert respuesta.get_json()['code'] == 'plataforma_con_accesos'


def test_cambiar_area_sin_accesos_vigentes_se_permite(escena, acceso,
                                                      cliente_como):
    _poner(acceso, ESTADO_REVOCADO)
    cliente = cliente_como(escena['super'])

    respuesta = cliente.put(f"{A}/platforms/{escena['plataforma'].id}",
                            json={'area_id': escena['otra'].id})

    assert respuesta.status_code == 200, respuesta.get_json()


def test_area_con_miembros_y_sin_accesos_se_puede_dar_de_baja(app,
                                                             cliente_como):
    """Regresión: la membresía en `user_areas` ya no es un acceso vigente."""
    area = fabricas.crear_area('Con miembros')
    fabricas.crear_usuario(areas=[area])
    super_ = fabricas.crear_usuario(ROLE_ADMIN)

    respuesta = cliente_como(super_).delete(f'{A}/areas/{area.id}')

    assert respuesta.status_code == 200, respuesta.get_json()
