"""API v1 de configuración de conectores (FNC-061, contrato
`docs/contratos/conectores-y-ejecuciones.md`).

| Ruta | Usuario | Admin de área | Superadmin |
|---|---|---|---|
| `GET /platforms/<id>/connector` | 403 | 403 | 200 |
| `PUT /platforms/<id>/connector` | 403 | 403 | 200 |
| `DELETE /platforms/<id>/connector` | 403 | 403 | 200 |
| `POST /platforms/<id>/connector/test` | 403 | 403 | 200 |

Solo el superadmin (SEC-CON-11, `admin_required`). Escrituras con
`escritura_del_portal` (JSON obligatorio mientras no esté FNC-008, P13);
`DELETE` y `test` llevan cuerpo `{}` y cualquier campo → `400
campo_no_permitido`, como el reintento de FNC-062.

Orden en `PUT`:
1. Plataforma existente (`404`).
2. Cuerpo JSON objeto y lista blanca (`400`).
3. Plataforma `conector` (`409 plataforma_sin_conector`).
4. `connectors.validacion.validar_configuracion` con las referencias de las
   demás plataformas (`422 validacion`; host fuera de
   `CONNECTOR_ALLOWED_HOSTS`, SEC-CON-07).
5. Cambiar el `type` con accesos vigentes → `409 plataforma_con_accesos`.
6. Guardado y auditoría (`conector_configurado`, antes y después de lo que
   cambió) en la misma transacción; después, `limpiar_cache()` (B4). Si otra
   petición creó la configuración a la vez (restricción única) →
   `409 conector_concurrente`.

Nunca se guarda ni devuelve el valor de una credencial: solo `credential_ref`
(y en la auditoría el saneo la omite).
"""
from flask import Blueprint, jsonify
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from app import db
from app.authz import admin_required
from app.modules.api.csrf_provisional import escritura_del_portal
from app.modules.api.helpers import (CAMPO_NO_PERMITIDO, CUERPO_INVALIDO,
                                     NO_ENCONTRADO, error_response,
                                     json_object, validation_error)
from app.modules.audit.events import Evento
from app.modules.audit.services import add_audit_log
from app.modules.connectors.credenciales import limpiar_cache
from app.modules.connectors.consultas import (configuracion_de,
                                              referencias_de_otras)
from app.modules.connectors.models import PlatformConnector
from app.modules.connectors.prueba import probar_conexion
from app.modules.connectors.validacion import validar_configuracion
from app.modules.core.models import Platform
from app.modules.platforms.estado import accesos_vigentes
from app.modules.platforms.tipos import TIPO_CONECTOR

connectors_api_bp = Blueprint('api_connectors', __name__, url_prefix='/api/v1')

MODULO_AUDITORIA = 'Conectores'

PLATAFORMA_SIN_CONECTOR = ('La plataforma no usa conector.', 409,
                           'plataforma_sin_conector')
PLATAFORMA_CON_ACCESOS = ('Hay accesos vigentes con este conector.', 409,
                          'plataforma_con_accesos')

CONECTOR_CONCURRENTE = ('Otra petición configuró este conector a la vez; '
                        'vuelve a intentarlo.', 409, 'conector_concurrente')

RESULTADO_OK = 'ok'
RESULTADO_ERROR = 'error'
MENSAJE_PRUEBA_OK = 'Conexión correcta.'
MENSAJE_PRUEBA_ERROR = 'No se pudo conectar con la plataforma.'

# Lista blanca del cuerpo del `PUT` y campos auditados (antes y después).
CAMPOS_PERMITIDOS = frozenset(('type', 'host', 'port', 'params',
                               'credential_ref', 'active'))
CAMPOS_AUDITADOS = ('type', 'host', 'port', 'params', 'credential_ref',
                    'active')


def _plataforma(platform_id):
    return db.session.get(Platform, platform_id)


def _estado(configuracion):
    if configuracion is None:
        return {}
    return {campo: getattr(configuracion, campo) for campo in CAMPOS_AUDITADOS}


def _respuesta(configuracion):
    return jsonify({'status': 'success', 'connector': configuracion.to_dict()})


def _cuerpo_vacio():
    """Error si el cuerpo no es `{}` (las acciones sin datos); si no, None."""
    datos = json_object()
    if datos is None:
        return error_response(*CUERPO_INVALIDO)
    if datos:
        return error_response(*CAMPO_NO_PERMITIDO)
    return None


def _configuracion_existente(platform_id):
    """(plataforma, configuración) o la respuesta `404`."""
    plataforma = _plataforma(platform_id)
    configuracion = configuracion_de(plataforma.id) if plataforma else None
    if configuracion is None:
        return None, None, error_response(*NO_ENCONTRADO)
    return plataforma, configuracion, None


@connectors_api_bp.route('/platforms/<int:platform_id>/connector')
@login_required
@admin_required
def get_connector(platform_id):
    _, configuracion, error = _configuracion_existente(platform_id)
    if error is not None:
        return error
    return _respuesta(configuracion)


def _guardar(plataforma, configuracion, limpio):
    """Crea o reemplaza la configuración y audita, en una transacción."""
    antes = _estado(configuracion)
    if configuracion is None:
        configuracion = PlatformConnector(platform_id=plataforma.id)
        db.session.add(configuracion)
    for campo, valor in limpio.items():
        setattr(configuracion, campo, valor)
    despues = _estado(configuracion)
    # Sin cambios no hay evento (como en plataformas, FNC-046).
    if antes != despues:
        add_audit_log(Evento.CONECTOR_CONFIGURADO, status='success',
                      module=MODULO_AUDITORIA, target=plataforma.name,
                      platform_id=plataforma.id, area_id=plataforma.area_id,
                      before={k: v for k, v in antes.items()
                              if despues.get(k) != v} or None,
                      after={k: v for k, v in despues.items()
                             if antes.get(k) != v},
                      commit=False)
    db.session.commit()
    return configuracion


@connectors_api_bp.route('/platforms/<int:platform_id>/connector',
                         methods=['PUT'])
@login_required
@admin_required
@escritura_del_portal
def put_connector(platform_id):
    plataforma = _plataforma(platform_id)
    if plataforma is None:
        return error_response(*NO_ENCONTRADO)
    datos = json_object()
    if datos is None:
        return error_response(*CUERPO_INVALIDO)
    if set(datos) - CAMPOS_PERMITIDOS:
        return error_response(*CAMPO_NO_PERMITIDO)
    if plataforma.integration_type != TIPO_CONECTOR:
        return error_response(*PLATAFORMA_SIN_CONECTOR)
    limpio, errores = validar_configuracion(
        datos, referencias_en_uso=referencias_de_otras(plataforma.id))
    if errores:
        return validation_error(errores)

    configuracion = configuracion_de(plataforma.id)
    if (configuracion is not None and configuracion.type != limpio['type']
            and accesos_vigentes(plataforma) > 0):
        return error_response(*PLATAFORMA_CON_ACCESOS)

    try:
        configuracion = _guardar(plataforma, configuracion, limpio)
    except IntegrityError:
        # Otra petición creó la configuración entre la lectura y el guardado
        # (`uq_platform_connectors_platform_id`).
        db.session.rollback()
        if not PlatformConnector.query.filter_by(
                platform_id=platform_id).count():
            raise
        return error_response(*CONECTOR_CONCURRENTE)
    limpiar_cache()
    return _respuesta(configuracion)


@connectors_api_bp.route('/platforms/<int:platform_id>/connector',
                         methods=['DELETE'])
@login_required
@admin_required
@escritura_del_portal
def delete_connector(platform_id):
    plataforma, configuracion, error = _configuracion_existente(platform_id)
    if error is not None:
        return error
    error = _cuerpo_vacio()
    if error is not None:
        return error
    if accesos_vigentes(plataforma) > 0:
        return error_response(*PLATAFORMA_CON_ACCESOS)
    add_audit_log(Evento.CONECTOR_ELIMINADO, status='warning',
                  module=MODULO_AUDITORIA, target=plataforma.name,
                  platform_id=plataforma.id, area_id=plataforma.area_id,
                  before=_estado(configuracion), commit=False)
    db.session.delete(configuracion)
    db.session.commit()
    limpiar_cache()
    return jsonify({'status': 'success'})


@connectors_api_bp.route('/platforms/<int:platform_id>/connector/test',
                         methods=['POST'])
@login_required
@admin_required
@escritura_del_portal
def test_connector(platform_id):
    plataforma, configuracion, error = _configuracion_existente(platform_id)
    if error is not None:
        return error
    error = _cuerpo_vacio()
    if error is not None:
        return error
    exito, motivo = probar_conexion(configuracion, current_user.id)
    add_audit_log(Evento.CONECTOR_PROBADO,
                  status='success' if exito else 'error',
                  module=MODULO_AUDITORIA, target=plataforma.name,
                  platform_id=plataforma.id, area_id=plataforma.area_id,
                  after={'result': RESULTADO_OK if exito else RESULTADO_ERROR,
                         'motivo': motivo},
                  commit=False)
    db.session.commit()
    if exito:
        return jsonify({'status': 'success', 'result': RESULTADO_OK,
                        'message': MENSAJE_PRUEBA_OK})
    return jsonify({'status': 'success', 'result': RESULTADO_ERROR,
                    'message': MENSAJE_PRUEBA_ERROR})
