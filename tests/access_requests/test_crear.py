"""`POST /access-requests` (FNC-056): reglas, auditoría y protección."""
import pytest
from sqlalchemy.exc import IntegrityError

from app import db
from app.modules.access_requests.models import PlatformAccessRequest
from app.modules.access_requests.tipos import ESTADO_APROBADA, PENDIENTE
from app.modules.audit.events import Evento
from app.modules.audit.models import AuditLog
from tests.access_requests.conftest import RUTA, dar_acceso, pedir

JUSTIFICACION = 'Cierre mensual'


def _codigo(respuesta):
    return respuesta.status_code, respuesta.get_json().get('code')


def test_usuario_crea_solicitud_pendiente(escena, cliente_como):
    respuesta = pedir(cliente_como(escena['usuario']), escena['plataforma'],
                      justification=f'  {JUSTIFICACION}  ')

    assert respuesta.status_code == 201
    cuerpo = respuesta.get_json()
    assert cuerpo['status'] == 'success'
    solicitud = cuerpo['request']
    assert solicitud['status'] == 'pendiente'
    assert solicitud['level'] == 'usuario'
    assert solicitud['justification'] == JUSTIFICACION
    assert solicitud['requester']['email'] == 'ana@pruebas.local'
    assert solicitud['platform']['name'] == 'Contabilidad'
    assert solicitud['area']['name'] == 'Finanzas'
    assert solicitud['current_level'] is None
    assert solicitud['created_at'].endswith('Z')
    assert solicitud['decided_by'] is None and solicitud['access'] is None


def test_sin_justificacion_se_acepta(escena, cliente_como):
    """Decisión del dueño (2026-10-20): no se pide justificación."""
    respuesta = pedir(cliente_como(escena['usuario']), escena['plataforma'])

    assert respuesta.status_code == 201
    assert respuesta.get_json()['request']['justification'] is None


def test_justificacion_demasiado_larga_es_422(escena, cliente_como):
    respuesta = pedir(cliente_como(escena['usuario']), escena['plataforma'],
                      justification='x' * 501)

    assert _codigo(respuesta) == (422, 'validacion')
    assert 'justification' in respuesta.get_json()['fields']


@pytest.mark.parametrize('cuerpo,campo', [
    ({'level': 'usuario'}, 'platform_id'),
    ({'platform_id': True, 'level': 'usuario'}, 'platform_id'),
    ({'platform_id': '1', 'level': 'usuario'}, 'platform_id'),
    ({'platform_id': 1, 'level': 'dueño'}, 'level'),
    ({'platform_id': 1, 'level': 'usuario', 'justification': 5},
     'justification'),
])
def test_datos_invalidos_son_422(escena, cliente_como, cuerpo, campo):
    respuesta = cliente_como(escena['usuario']).post(RUTA, json=cuerpo)

    assert _codigo(respuesta) == (422, 'validacion')
    assert campo in respuesta.get_json()['fields']


def test_campo_fuera_de_lista_blanca_es_400(escena, cliente_como):
    respuesta = pedir(cliente_como(escena['usuario']), escena['plataforma'],
                      user_id=escena['admin'].id)

    assert _codigo(respuesta) == (400, 'campo_no_permitido')
    assert PlatformAccessRequest.query.count() == 0


def test_cuerpo_que_no_es_objeto_es_400(escena, cliente_como):
    respuesta = cliente_como(escena['usuario']).post(RUTA, json=[1])

    assert _codigo(respuesta) == (400, 'cuerpo_invalido')


def test_cuerpo_no_json_es_415(escena, cliente_como):
    respuesta = cliente_como(escena['usuario']).post(
        RUTA, data={'platform_id': escena['plataforma'].id, 'level': 'usuario'})

    assert _codigo(respuesta) == (415, 'tipo_no_soportado')
    assert PlatformAccessRequest.query.count() == 0


def test_peticion_de_otro_sitio_es_403_csrf(escena, cliente_como):
    respuesta = cliente_como(escena['usuario']).post(
        RUTA, json={'platform_id': escena['plataforma'].id, 'level': 'usuario'},
        headers={'Sec-Fetch-Site': 'cross-site'})

    assert _codigo(respuesta) == (403, 'csrf_invalido')
    assert PlatformAccessRequest.query.count() == 0


def test_superadmin_no_solicita(escena, cliente_como):
    respuesta = pedir(cliente_como(escena['super']), escena['plataforma'])

    assert _codigo(respuesta) == (403, 'sin_permiso')


def test_admin_no_solicita_en_el_area_que_administra(escena, cliente_como):
    respuesta = pedir(cliente_como(escena['admin']), escena['plataforma'],
                      'admin')

    assert _codigo(respuesta) == (409, 'ya_administra_area')
    assert PlatformAccessRequest.query.count() == 0


def test_admin_solicita_como_usuario_en_area_ajena(escena, cliente_como):
    """RF-03: el admin de Ventas pertenece a Finanzas y pide ahí."""
    respuesta = pedir(cliente_como(escena['admin_otra']),
                      escena['plataforma'], 'admin')

    assert respuesta.status_code == 201


def test_plataforma_fuera_de_sus_areas_es_404(escena, cliente_como):
    respuesta = pedir(cliente_como(escena['usuario']), escena['de_otra'])

    assert _codigo(respuesta) == (404, 'no_encontrado')


def test_plataforma_inexistente_es_404(escena, cliente_como):
    respuesta = cliente_como(escena['usuario']).post(
        RUTA, json={'platform_id': 99999, 'level': 'usuario'})

    assert _codigo(respuesta) == (404, 'no_encontrado')


def test_plataforma_inactiva_es_409(escena, cliente_como):
    escena['plataforma'].status = 'Inactivo'
    db.session.commit()

    respuesta = pedir(cliente_como(escena['usuario']), escena['plataforma'])

    assert _codigo(respuesta) == (409, 'plataforma_no_disponible')


def test_nivel_sin_grupo_es_409(escena, cliente_como):
    escena['plataforma'].ldap_group_admin_dn = None
    db.session.commit()
    cliente = cliente_como(escena['usuario'])

    assert _codigo(pedir(cliente, escena['plataforma'], 'admin')) == \
        (409, 'plataforma_no_disponible')
    assert pedir(cliente, escena['plataforma'], 'usuario').status_code == 201


def test_plataforma_con_conector_sin_configurar_es_409(escena, cliente_como):
    escena['plataforma'].integration_type = 'conector'
    db.session.commit()

    respuesta = pedir(cliente_como(escena['usuario']), escena['plataforma'])

    assert _codigo(respuesta) == (409, 'plataforma_no_disponible')


def test_duplicado_pendiente_es_409(escena, cliente_como):
    cliente = cliente_como(escena['usuario'])
    assert pedir(cliente, escena['plataforma']).status_code == 201

    respuesta = pedir(cliente, escena['plataforma'], 'admin')

    assert _codigo(respuesta) == (409, 'solicitud_duplicada')
    assert PlatformAccessRequest.query.count() == 1


def test_tras_decidirse_puede_volver_a_solicitar(escena, cliente_como):
    cliente = cliente_como(escena['usuario'])
    pedir(cliente, escena['plataforma'])
    solicitud = PlatformAccessRequest.query.one()
    solicitud.status = 'rechazada'
    solicitud.sincronizar_slot()
    db.session.commit()

    assert pedir(cliente, escena['plataforma']).status_code == 201


def test_la_bd_impide_dos_pendientes(escena):
    """La restricción única no depende del código (peticiones simultáneas)."""
    for _ in range(2):
        solicitud = PlatformAccessRequest(
            user_id=escena['usuario'].id,
            platform_id=escena['plataforma'].id, level='usuario',
            status='pendiente')
        solicitud.sincronizar_slot()
        db.session.add(solicitud)
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_la_bd_admite_varias_decididas(escena):
    for _ in range(2):
        solicitud = PlatformAccessRequest(
            user_id=escena['usuario'].id,
            platform_id=escena['plataforma'].id, level='usuario',
            status=ESTADO_APROBADA)
        solicitud.sincronizar_slot()
        db.session.add(solicitud)
    db.session.commit()

    assert PlatformAccessRequest.query.count() == 2


def test_carrera_responde_409_y_no_500(escena, cliente_como, monkeypatch):
    """Si otra petición gana entre la regla y el `flush`: 409."""
    cliente = cliente_como(escena['usuario'])
    otra = PlatformAccessRequest(user_id=escena['usuario'].id,
                                 platform_id=escena['plataforma'].id,
                                 level='usuario', status='pendiente',
                                 slot_pendiente=PENDIENTE)
    db.session.add(otra)
    db.session.commit()
    from app.modules.access_requests import catalogo
    original = catalogo.estado

    def sin_pendiente(usuario_id, plataforma_id):
        estado = original(usuario_id, plataforma_id)
        estado.pendiente = None  # la regla no la ve: solo queda la BD
        return estado

    monkeypatch.setattr(catalogo, 'estado', sin_pendiente)

    respuesta = pedir(cliente, escena['plataforma'])

    assert _codigo(respuesta) == (409, 'solicitud_duplicada')
    assert PlatformAccessRequest.query.count() == 1


def test_mismo_nivel_vigente_es_409(escena, cliente_como):
    dar_acceso(escena['usuario'], escena['plataforma'], 'usuario')

    respuesta = pedir(cliente_como(escena['usuario']), escena['plataforma'])

    assert _codigo(respuesta) == (409, 'nivel_vigente')


def test_nivel_inferior_al_vigente_es_409(escena, cliente_como):
    dar_acceso(escena['usuario'], escena['plataforma'], 'admin')

    respuesta = pedir(cliente_como(escena['usuario']), escena['plataforma'])

    assert _codigo(respuesta) == (409, 'nivel_vigente')


def test_subir_de_nivel_guarda_el_nivel_actual(escena, cliente_como):
    dar_acceso(escena['usuario'], escena['plataforma'], 'usuario')

    respuesta = pedir(cliente_como(escena['usuario']), escena['plataforma'],
                      'admin')

    assert respuesta.status_code == 201
    assert respuesta.get_json()['request']['current_level'] == 'usuario'


def test_subir_con_acceso_aun_en_proceso_es_409(escena, cliente_como):
    dar_acceso(escena['usuario'], escena['plataforma'], 'usuario',
               'en_proceso')

    respuesta = pedir(cliente_como(escena['usuario']), escena['plataforma'],
                      'admin')

    assert _codigo(respuesta) == (409, 'estado_invalido')


def test_audita_en_la_misma_transaccion(escena, cliente_como):
    respuesta = pedir(cliente_como(escena['usuario']), escena['plataforma'],
                      justification=JUSTIFICACION)

    registro = AuditLog.query.filter_by(
        action=Evento.SOLICITUD_CREADA.value).one()
    assert registro.request_id == respuesta.get_json()['request']['id']
    assert registro.actor_id == escena['usuario'].id
    assert registro.target_user_id == escena['usuario'].id
    assert registro.platform_id == escena['plataforma'].id
    assert registro.area_id == escena['area'].id
    assert registro.to_dict()['after']['status'] == 'pendiente'
    assert registro.to_dict()['before'] is None

