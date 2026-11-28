"""Motivo de la solicitud y del rechazo configurables (FNC-216, contrato 1.5)."""
import flask
import pytest

from app import create_app, db
from app.modules.access_requests.models import PlatformAccessRequest
from app.modules.audit.models import AuditLog
from tests.access_requests.conftest import RUTA, pedir
from tests.access_requests.test_approvals import (_codigo, avisos,  # noqa: F401
                                                  pendiente, rechazar)
from tests.conftest import VARIABLES_PRUEBA

TEXTO = 'Necesito consultar las pólizas del área.'
MOTIVO = 'Usa el reporte compartido del área.'
CONTEXTO = '/api/v1/auth/context'


def _modo(monkeypatch, solicitud=None, rechazo=None):
    for nombre, valor in (('SOLICITUD_MOTIVO', solicitud),
                          ('RECHAZO_MOTIVO', rechazo)):
        if valor is None:
            monkeypatch.delenv(nombre, raising=False)
        else:
            monkeypatch.setenv(nombre, valor)


def _guardada(respuesta):
    return db.session.get(PlatformAccessRequest,
                          respuesta.get_json()['request']['id']).justification


# --------------------------------------------------------------------------- #
# Solicitud
# --------------------------------------------------------------------------- #

def test_solicitud_por_omision_es_oculto_y_descarta(escena, cliente_como,
                                                    monkeypatch):
    _modo(monkeypatch)
    respuesta = pedir(cliente_como(escena['usuario']), escena['plataforma'],
                      justification=TEXTO)

    assert respuesta.status_code == 201
    assert respuesta.get_json()['request']['justification'] is None
    assert _guardada(respuesta) is None


def test_solicitud_oculto_no_valida_lo_que_llegue(escena, cliente_como,
                                                  monkeypatch):
    _modo(monkeypatch, solicitud='oculto')
    respuesta = pedir(cliente_como(escena['usuario']), escena['plataforma'],
                      justification='x' * 5000)

    assert respuesta.status_code == 201
    assert _guardada(respuesta) is None


def test_solicitud_opcional_guarda_recortada_y_acepta_vacia(
        escena, cliente_como, monkeypatch):
    _modo(monkeypatch, solicitud='opcional')
    respuesta = pedir(cliente_como(escena['usuario']), escena['plataforma'],
                      justification=f'  {TEXTO}  ')
    assert respuesta.status_code == 201
    assert _guardada(respuesta) == TEXTO

    PlatformAccessRequest.query.delete()
    db.session.commit()
    sin_texto = pedir(cliente_como(escena['usuario']), escena['plataforma'])
    assert sin_texto.status_code == 201
    assert _guardada(sin_texto) is None


@pytest.mark.parametrize('cuerpo', [{}, {'justification': None},
                                    {'justification': ''},
                                    {'justification': '   '}])
def test_solicitud_obligatorio_sin_texto_es_422(escena, cliente_como,
                                                monkeypatch, cuerpo):
    _modo(monkeypatch, solicitud='obligatorio')
    respuesta = pedir(cliente_como(escena['usuario']), escena['plataforma'],
                      **cuerpo)

    assert _codigo(respuesta) == (422, 'validacion')
    assert list(respuesta.get_json()['fields']) == ['justification']
    assert PlatformAccessRequest.query.count() == 0


def test_solicitud_obligatorio_largo_es_422_y_valido_se_guarda(
        escena, cliente_como, monkeypatch):
    _modo(monkeypatch, solicitud='obligatorio')
    cliente = cliente_como(escena['usuario'])

    largo = pedir(cliente, escena['plataforma'], justification='x' * 501)
    assert _codigo(largo) == (422, 'validacion')

    bien = pedir(cliente, escena['plataforma'], justification=f' {TEXTO} ')
    assert bien.status_code == 201
    assert _guardada(bien) == TEXTO


# --------------------------------------------------------------------------- #
# Rechazo
# --------------------------------------------------------------------------- #

def test_rechazo_por_omision_es_obligatorio(escena, cliente_como, monkeypatch):
    _modo(monkeypatch)
    solicitud = pendiente(escena['usuario'], escena['plataforma'])

    respuesta = rechazar(cliente_como(escena['admin']), solicitud.id,
                         json={})

    assert _codigo(respuesta) == (422, 'validacion')
    assert 'reason' in respuesta.get_json()['fields']


@pytest.mark.parametrize('cuerpo', [{}, {'reason': None}, {'reason': ''},
                                    {'reason': '    '}])
def test_rechazo_opcional_sin_motivo_guarda_null_y_audita(
        escena, cliente_como, monkeypatch, avisos, cuerpo):  # noqa: F811
    _modo(monkeypatch, rechazo='opcional')
    solicitud = pendiente(escena['usuario'], escena['plataforma'])

    respuesta = rechazar(cliente_como(escena['admin']), solicitud.id,
                         json=cuerpo)

    assert respuesta.status_code == 200, respuesta.get_json()
    assert respuesta.get_json()['request']['status'] == 'rechazada'
    assert respuesta.get_json()['request']['rejection_reason'] is None
    log = AuditLog.query.filter_by(action='solicitud_rechazada').one()
    assert log.request_id == solicitud.id
    assert log.after_state['rejection_reason'] is None
    assert avisos[0][1][3] is None


def test_rechazo_opcional_con_motivo_aplica_10_a_500(escena, cliente_como,
                                                     monkeypatch):
    _modo(monkeypatch, rechazo='opcional')
    cliente = cliente_como(escena['admin'])
    solicitud = pendiente(escena['usuario'], escena['plataforma'])

    for invalido in ('corto', 'x' * 501):
        respuesta = rechazar(cliente, solicitud.id, invalido)
        assert _codigo(respuesta) == (422, 'validacion')
    bien = rechazar(cliente, solicitud.id, f' {MOTIVO} ')
    assert bien.status_code == 200
    assert bien.get_json()['request']['rejection_reason'] == MOTIVO


def test_rechazo_oculto_descarta_el_motivo_y_audita(escena, cliente_como,
                                                    monkeypatch):
    _modo(monkeypatch, rechazo='oculto')
    solicitud = pendiente(escena['usuario'], escena['plataforma'])

    respuesta = rechazar(cliente_como(escena['admin']), solicitud.id, MOTIVO)

    assert respuesta.status_code == 200
    assert respuesta.get_json()['request']['rejection_reason'] is None
    assert AuditLog.query.filter_by(action='solicitud_rechazada').count() == 1


# --------------------------------------------------------------------------- #
# Arranque y campo expuesto
# --------------------------------------------------------------------------- #

@pytest.fixture
def instancia(tmp_path, monkeypatch):
    monkeypatch.setattr(flask.Flask, 'auto_find_instance_path',
                        lambda self: str(tmp_path))
    creadas = []

    def _crear():
        aplicacion = create_app()
        creadas.append(aplicacion)
        return aplicacion

    yield _crear
    for aplicacion in creadas:
        with aplicacion.app_context():
            db.session.remove()
            db.engine.dispose()


@pytest.mark.parametrize('variable', ['SOLICITUD_MOTIVO', 'RECHAZO_MOTIVO'])
def test_valor_invalido_no_arranca_y_no_repite_el_valor(instancia, monkeypatch,
                                                        variable):
    for clave, valor in VARIABLES_PRUEBA.items():
        monkeypatch.setenv(clave, valor)
    monkeypatch.setenv(variable, 'talvez')

    with pytest.raises(Exception) as info:
        instancia()

    assert variable in str(info.value)
    assert 'talvez' not in str(info.value)


def test_contexto_expone_los_modos(client, monkeypatch):
    _modo(monkeypatch)
    assert client.get(CONTEXTO).get_json()['motivos'] == {
        'solicitud': 'oculto', 'rechazo': 'obligatorio'}

    _modo(monkeypatch, solicitud='Obligatorio', rechazo='oculto')
    assert client.get(CONTEXTO).get_json()['motivos'] == {
        'solicitud': 'obligatorio', 'rechazo': 'oculto'}
