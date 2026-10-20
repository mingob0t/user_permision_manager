"""Tabla `platform_connectors`: solo referencias, nunca secretos (FNC-050)."""
from app import db
from app.modules.connectors.models import PlatformConnector
from app.modules.connectors.tipos import (CREDENCIAL_OK,
                                          CREDENCIAL_SIN_VERIFICAR)
from tests.connectors.conftest import crear_conector

# Columnas permitidas: ninguna guarda el valor de una credencial.
COLUMNAS_ESPERADAS = {'id', 'platform_id', 'type', 'host', 'port', 'params',
                      'credential_ref', 'credential_status', 'active',
                      'created_at', 'updated_at'}
FRAGMENTOS_DE_SECRETO = ('password', 'pass', 'secret', 'secreto', 'token',
                         'key', 'clave', 'contrasena')


def test_la_tabla_solo_tiene_referencias_y_ninguna_columna_de_secreto():
    columnas = {c.name for c in PlatformConnector.__table__.columns}
    assert columnas == COLUMNAS_ESPERADAS
    for columna in columnas:
        assert not any(f in columna for f in FRAGMENTOS_DE_SECRETO), columna


def test_una_configuracion_por_plataforma(conector_noop):
    plataforma, _, _ = conector_noop
    duplicado = PlatformConnector(platform_id=plataforma.id, type='noop',
                                  host='otro.pruebas.local', port=22,
                                  params={}, credential_ref='pokemon/otra')
    db.session.add(duplicado)
    try:
        db.session.commit()
        repetida = True
    except Exception:
        db.session.rollback()
        repetida = False
    assert repetida is False


def test_cambiar_host_o_referencia_invalida_la_verificacion(conector_noop):
    _, configuracion, _ = conector_noop
    assert configuracion.credential_status == CREDENCIAL_SIN_VERIFICAR
    configuracion.credential_status = CREDENCIAL_OK
    configuracion.host = configuracion.host  # mismo valor: no cambia
    assert configuracion.credential_status == CREDENCIAL_OK

    configuracion.host = 'otro.pruebas.local'
    assert configuracion.credential_status == CREDENCIAL_SIN_VERIFICAR

    configuracion.credential_status = CREDENCIAL_OK
    configuracion.credential_ref = 'pokemon/otra'
    assert configuracion.credential_status == CREDENCIAL_SIN_VERIFICAR


def test_el_diccionario_no_trae_valores_de_credencial(conector_noop):
    _, configuracion, _ = conector_noop
    datos = configuracion.to_dict()
    assert set(datos) == {'platform_id', 'type', 'host', 'port', 'params',
                          'credential_ref', 'credential_status', 'active',
                          'updated_at'}
