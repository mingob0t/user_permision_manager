"""API v1 del solicitante: catálogo, crear solicitud y mis solicitudes (FNC-056).

Contrato `docs/contratos/solicitudes.md`. Orden de `POST /access-requests`:
1. Sesión (`401`), petición de otro sitio (`403 csrf_invalido`) y cuerpo no
   JSON (`415 tipo_no_soportado`).
2. Cuerpo objeto (`400 cuerpo_invalido`) y lista blanca (`400
   campo_no_permitido`).
3. Reglas de `services.crear` (`403`, `422`, `404`, `409`).
4. `commit` y, después, el aviso `solicitud_nueva` a los admins del área
   (FNC-048); un fallo del correo no revierte la solicitud.

CSRF: la API v1 sigue exenta de Flask-WTF hasta FNC-008. Mientras, este
endpoint exige `Content-Type: application/json` (un formulario de otro sitio
no puede enviarlo sin preflight) y rechaza `Sec-Fetch-Site: cross-site`.
Decisión del orquestador (pendiente de validar en la prueba de concepto).
"""
import logging

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from app import db
from app.modules.access.errores import ErrorDeAcceso
from app.modules.access_requests import catalogo, errores, serializacion
from app.modules.access_requests.models import PlatformAccessRequest
from app.modules.access_requests.services import crear
from app.modules.access_requests.tipos import ESTADOS
from app.modules.api.helpers import (CAMPO_NO_PERMITIDO, CUERPO_INVALIDO,
                                     error_response, json_object)
from app.modules.audit.parametros import (ParametroInvalido, leer_filtros,
                                          leer_paginacion)
from app.modules.notifications.access_notifications import \
    notificar_solicitud_nueva

logger = logging.getLogger(__name__)

access_requests_api_bp = Blueprint('api_access_requests', __name__,
                                   url_prefix='/api/v1')

CAMPOS_PERMITIDOS = frozenset({'platform_id', 'level', 'justification'})
PARAMETRO_INVALIDO = ('Parámetro de consulta inválido.', 400,
                      'parametro_invalido')
CSRF_INVALIDO = ('La petición no viene del portal.', 403, 'csrf_invalido')
TIPO_NO_SOPORTADO = ('El cuerpo debe ser JSON.', 415, 'tipo_no_soportado')
SITIO_AJENO = 'cross-site'


def _invalido(campo):
    return error_response(*PARAMETRO_INVALIDO,
                          fields={campo: PARAMETRO_INVALIDO[0]})


def _rechazo_de_escritura():
    """Respuesta de error si la escritura no viene del portal o no es JSON."""
    if request.headers.get('Sec-Fetch-Site', '').lower() == SITIO_AJENO:
        return error_response(*CSRF_INVALIDO)
    if not request.is_json:
        return error_response(*TIPO_NO_SOPORTADO)
    return None


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
def create_request():
    rechazo = _rechazo_de_escritura()
    if rechazo is not None:
        return rechazo
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
