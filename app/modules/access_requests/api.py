"""API v1 de solicitudes: catálogo, crear solicitud y mis solicitudes
(FNC-056); bandeja, aprobar y rechazar (FNC-057, reglas en `approvals.py`).

Contrato `docs/contratos/solicitudes.md`. Orden de `POST /access-requests`:
1. Sesión (`401`), petición de otro sitio (`403 csrf_invalido`) y cuerpo no
   JSON (`415 tipo_no_soportado`).
2. Cuerpo objeto (`400 cuerpo_invalido`) y lista blanca (`400
   campo_no_permitido`).
3. Reglas de `services.crear` (`403`, `422`, `404`, `409`).
4. `commit` y, después, el aviso `solicitud_nueva` a los admins del área
   (FNC-048); un fallo del correo no revierte la solicitud.

CSRF: la API v1 sigue exenta de Flask-WTF hasta FNC-008. Mientras, este
endpoint usa `api.csrf_provisional.escritura_del_portal` (JSON obligatorio y
sin `Sec-Fetch-Site: cross-site`; extraído aquí de FNC-056 en FNC-058).
Decisión del orquestador (pendiente de validar en la prueba de concepto).
"""
import logging

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from app import db
from app.authz import any_admin_required
from app.modules.access import errores as errores_acceso
from app.modules.access.errores import ErrorDeAcceso
from app.modules.access_requests import (approvals, catalogo, errores,
                                         serializacion)
from app.modules.access_requests.models import PlatformAccessRequest
from app.modules.access_requests.services import crear
from app.modules.access_requests.tipos import ESTADO_PENDIENTE, ESTADOS
from app.modules.api.csrf_provisional import escritura_del_portal
from app.modules.api.helpers import (CAMPO_NO_PERMITIDO, CUERPO_INVALIDO,
                                     error_response, json_object)
from app.modules.audit.parametros import (ParametroInvalido, leer_filtros,
                                          leer_paginacion)
from app.modules.notifications.access_notifications import (
    notificar_solicitud_aprobada, notificar_solicitud_nueva,
    notificar_solicitud_rechazada)

logger = logging.getLogger(__name__)

access_requests_api_bp = Blueprint('api_access_requests', __name__,
                                   url_prefix='/api/v1')

CAMPOS_PERMITIDOS = frozenset({'platform_id', 'level', 'justification'})
CAMPOS_APROBAR = frozenset()
CAMPOS_RECHAZAR = frozenset({'reason'})
PARAMETRO_INVALIDO = ('Parámetro de consulta inválido.', 400,
                      'parametro_invalido')


def _invalido(campo):
    return error_response(*PARAMETRO_INVALIDO,
                          fields={campo: PARAMETRO_INVALIDO[0]})


# --------------------------------------------------------------------------- #
# Catálogo
# --------------------------------------------------------------------------- #

@access_requests_api_bp.route('/access-requests/catalog')
@login_required
def catalog():
    try:
        # Reusa las reglas de `area_id` (entero) y `q` (≤ 100) de auditoría.
        filtros = leer_filtros({'area_id': request.args.get('area_id'),
                                'q': request.args.get('q')})
    except ParametroInvalido as error:
        return _invalido(error.campo)
    lista = catalogo.plataformas(current_user, filtros.area_id, filtros.q)
    estados = catalogo.estados(current_user.id, [p.id for p in lista])
    return jsonify([serializacion.entrada_catalogo(current_user, p,
                                                   estados[p.id])
                    for p in lista])


# --------------------------------------------------------------------------- #
# Crear
# --------------------------------------------------------------------------- #

@access_requests_api_bp.route('/access-requests', methods=['POST'])
@login_required
@escritura_del_portal
def create_request():
    datos = json_object()
    if datos is None:
        return error_response(*CUERPO_INVALIDO)
    if set(datos) - CAMPOS_PERMITIDOS:
        return error_response(*CAMPO_NO_PERMITIDO)

    try:
        solicitud = crear(current_user, datos.get('platform_id'),
                          datos.get('level'), datos.get('justification'))
        db.session.commit()
    except ErrorDeAcceso as error:
        db.session.rollback()
        return error_response(*error.respuesta)
    except IntegrityError:
        # Otra petición simultánea creó la pendiente (restricción única).
        db.session.rollback()
        return error_response(*errores.solicitud_duplicada().respuesta)

    try:
        notificar_solicitud_nueva(current_user, solicitud.platform,
                                  solicitud.level, solicitud.justification)
    except Exception:  # el aviso nunca revierte la solicitud (FNC-048)
        logger.exception('Aviso solicitud_nueva no enviado (solicitud %s).',
                         solicitud.id)
    return jsonify({'status': 'success',
                    'request': serializacion.solicitud(solicitud)}), 201


# --------------------------------------------------------------------------- #
# Mis solicitudes
# --------------------------------------------------------------------------- #

@access_requests_api_bp.route('/access-requests/mine')
@login_required
def my_requests():
    estado = request.args.get('status') or None
    if estado is not None and estado not in ESTADOS:
        return _invalido('status')
    try:
        filtros = leer_filtros(
            {'platform_id': request.args.get('platform_id')})
        paginacion = leer_paginacion(request.args)
    except ParametroInvalido as error:
        return _invalido(error.campo)

    consulta = PlatformAccessRequest.query.filter(
        PlatformAccessRequest.user_id == current_user.id)
    if estado is not None:
        consulta = consulta.filter(PlatformAccessRequest.status == estado)
    if filtros.platform_id is not None:
        consulta = consulta.filter(
            PlatformAccessRequest.platform_id == filtros.platform_id)
    total = consulta.count()
    registros = (consulta.order_by(PlatformAccessRequest.created_at.desc(),
                                   PlatformAccessRequest.id.desc())
                 .offset(paginacion.offset).limit(paginacion.per_page).all())
    accesos = serializacion.accesos_de(registros)
    return jsonify({
        'items': [serializacion.solicitud(r, accesos.get(r.id))
                  for r in registros],
        'page': paginacion.page, 'per_page': paginacion.per_page,
        'total': total})


# --------------------------------------------------------------------------- #
# Bandeja de aprobación (FNC-057)
# --------------------------------------------------------------------------- #

@access_requests_api_bp.route('/access-requests/inbox')
@login_required
@any_admin_required
def inbox():
    estado = request.args.get('status') or ESTADO_PENDIENTE
    if estado not in ESTADOS:
        return _invalido('status')
    try:
        filtros = leer_filtros(
            {'area_id': request.args.get('area_id'),
             'platform_id': request.args.get('platform_id')})
        paginacion = leer_paginacion(request.args)
    except ParametroInvalido as error:
        return _invalido(error.campo)

    consulta = approvals.bandeja(current_user).filter(
        PlatformAccessRequest.status == estado)
    if filtros.area_id is not None:
        consulta = consulta.filter(
            PlatformAccessRequest.platform.has(area_id=filtros.area_id))
    if filtros.platform_id is not None:
        consulta = consulta.filter(
            PlatformAccessRequest.platform_id == filtros.platform_id)
    total = consulta.order_by(None).count()
    # Pendientes: la más antigua primero (contrato); decididas: la más reciente.
    if estado == ESTADO_PENDIENTE:
        orden = (PlatformAccessRequest.created_at.asc(),
                 PlatformAccessRequest.id.asc())
    else:
        orden = (PlatformAccessRequest.created_at.desc(),
                 PlatformAccessRequest.id.desc())
    registros = (consulta.order_by(*orden).offset(paginacion.offset)
                 .limit(paginacion.per_page).all())
    accesos = serializacion.accesos_de(registros)
    return jsonify({
        'items': [serializacion.solicitud(r, accesos.get(r.id))
                  for r in registros],
        'page': paginacion.page, 'per_page': paginacion.per_page,
        'total': total})


def _solicitud_a_decidir(solicitud_id, campos):
    """(solicitud, datos, None) o (None, None, respuesta de error).

    Alcance antes que el cuerpo: fuera de alcance no se distingue (404).
    """
    solicitud = db.session.get(PlatformAccessRequest, solicitud_id)
    try:
        approvals.validar_decisor(current_user, solicitud)
    except ErrorDeAcceso as error:
        return None, None, error_response(*error.respuesta)
    datos = json_object()
    if datos is None:
        return None, None, error_response(*CUERPO_INVALIDO)
    if set(datos) - campos:
        return None, None, error_response(*CAMPO_NO_PERMITIDO)
    return solicitud, datos, None


def _confirmar(operacion):
    """Ejecuta la decisión y confirma; `None` o la respuesta de error."""
    try:
        resultado = operacion()
        db.session.commit()
    except ErrorDeAcceso as error:
        db.session.rollback()
        return None, error_response(*error.respuesta)
    except IntegrityError:
        # Otro acceso del solicitante se creó a la vez (únicos de accesos).
        db.session.rollback()
        return None, error_response(*errores_acceso.estado_invalido(
            'El acceso cambió mientras se decidía; vuelve a intentarlo.'
        ).respuesta)
    return resultado, None


def _avisar(funcion, solicitud, *extra):
    try:
        funcion(solicitud.requester, solicitud.platform, solicitud.level,
                *extra)
    except Exception:  # el aviso nunca revierte la decisión (FNC-048)
        logger.exception('Aviso de decisión no enviado (solicitud %s).',
                         solicitud.id)


@access_requests_api_bp.route('/access-requests/<int:request_id>/approve',
                              methods=['POST'])
@login_required
@any_admin_required
@escritura_del_portal
def approve_request(request_id):
    solicitud, _, rechazo = _solicitud_a_decidir(request_id, CAMPOS_APROBAR)
    if rechazo is not None:
        return rechazo
    acceso, rechazo = _confirmar(
        lambda: approvals.aprobar(solicitud, current_user))
    if rechazo is not None:
        return rechazo
    _avisar(notificar_solicitud_aprobada, solicitud)
    return jsonify({'status': 'success',
                    'request': serializacion.solicitud(solicitud, acceso)})


@access_requests_api_bp.route('/access-requests/<int:request_id>/reject',
                              methods=['POST'])
@login_required
@any_admin_required
@escritura_del_portal
def reject_request(request_id):
    solicitud, datos, rechazo = _solicitud_a_decidir(request_id,
                                                     CAMPOS_RECHAZAR)
    if rechazo is not None:
        return rechazo
    _, rechazo = _confirmar(lambda: approvals.rechazar(
        solicitud, current_user, datos.get('reason')))
    if rechazo is not None:
        return rechazo
    _avisar(notificar_solicitud_rechazada, solicitud,
            solicitud.rejection_reason)
    return jsonify({'status': 'success',
                    'request': serializacion.solicitud(solicitud)})
