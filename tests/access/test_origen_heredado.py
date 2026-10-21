"""Origen `heredado` (FNC-065, contrato `accesos.md` 1.2).

Lo crea solo la migración 0010. Reglas, serialización, inventario y
revocación lo tratan como a cualquier acceso vigente.
"""
import pytest

from app import db
from app.modules.access import rules
from app.modules.access.consultas import plataformas_con_acceso_activo
from app.modules.access.errores import ErrorDeAcceso
from app.modules.access.tipos import ORIGEN_HEREDADO, ORIGENES
from app.modules.provisioning.models import ProvisioningJob
from tests import fabricas
from tests.access.conftest import recargar

A = '/api/v1'


def _heredado(usuario, plataforma, estado='activo'):
    return fabricas.crear_acceso(usuario, plataforma, estado=estado,
                                 origen=ORIGEN_HEREDADO)


def test_el_origen_heredado_es_valido_y_aditivo():
    assert ORIGEN_HEREDADO == 'heredado'
    assert ORIGENES == ('solicitud', 'admin_de_area', 'heredado')


def test_el_servicio_no_otorga_por_origen_heredado(escena):
    """Solo la migración los crea: otorgar con ese origen es una validación."""
    with pytest.raises(ErrorDeAcceso):
        rules.validar_datos('usuario', ORIGEN_HEREDADO, None)


def test_un_heredado_activo_da_visibilidad(escena):
    _heredado(escena['usuario'], escena['plataforma'])

    ids = {fila[0] for fila in
           plataformas_con_acceso_activo(escena['usuario'].id).all()}

    assert ids == {escena['plataforma'].id}


def test_mis_accesos_lo_serializa_con_su_origen(escena, cliente_como):
    acceso = _heredado(escena['usuario'], escena['plataforma'])

    respuesta = cliente_como(escena['usuario']).get(f'{A}/me/access')

    item, = respuesta.get_json()['items']
    assert (item['id'], item['origin'], item['granted_by'],
            item['request_id']) == (acceso.id, 'heredado', None, None)


def test_el_inventario_filtra_por_origen_heredado(escena, cliente_como):
    acceso = _heredado(escena['usuario'], escena['plataforma'])

    respuesta = cliente_como(escena['admin']).get(
        f'{A}/access/inventory?origin=heredado')

    assert respuesta.status_code == 200, respuesta.get_json()
    assert [a['id'] for a in respuesta.get_json()['items']] == [acceso.id]
    otros = cliente_como(escena['admin']).get(
        f'{A}/access/inventory?origin=solicitud')
    assert otros.get_json()['items'] == []


def test_el_admin_de_area_revoca_un_heredado_de_sus_areas(
        escena, cliente_como, cola_falsa):
    acceso = _heredado(escena['usuario'], escena['plataforma'])

    respuesta = cliente_como(escena['admin']).post(
        f'{A}/access/{acceso.id}/revoke', json={'reason': 'ya no aplica'})

    assert respuesta.status_code == 200, respuesta.get_json()
    assert recargar(acceso.id).status == 'revocando'
    assert ProvisioningJob.query.count() == 1


def test_el_admin_de_otra_area_no_revoca_un_heredado_ajeno(
        escena, cliente_como, cola_falsa):
    acceso = _heredado(escena['usuario'], escena['plataforma'])

    respuesta = cliente_como(escena['admin_otra']).post(
        f'{A}/access/{acceso.id}/revoke', json={})

    assert respuesta.status_code == 404
    assert recargar(acceso.id).status == 'activo'


def test_la_cuenta_no_revoca_su_propio_heredado(escena, cliente_como,
                                                cola_falsa):
    acceso = _heredado(escena['usuario'], escena['plataforma'])

    respuesta = cliente_como(escena['usuario']).post(
        f'{A}/access/{acceso.id}/revoke', json={})

    assert respuesta.status_code in (403, 404)
    assert recargar(acceso.id).status == 'activo'
