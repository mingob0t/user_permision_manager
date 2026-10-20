"""API v1 de accesos: mis accesos, accesos de una cuenta y revocación manual
(FNC-058, contrato `docs/contratos/accesos.md` v1.1).

- Las reglas de revocar son las del servicio (`services.revocar`,
  `rules.validar_revocacion`); aquí solo se traducen a HTTP.
- Fuera de alcance = inexistente: `404 no_encontrado` (SEC-AUTHZ-03/04/06),
  antes de mirar el cuerpo, para no revelar que el acceso existe.
- Revocar: cuerpo con lista blanca (`reason`), cambio, trabajo y auditoría en
  una transacción; un choque simultáneo revierte y responde `409`.

Decisiones del orquestador (pendientes de validar en la prueba de concepto):
- `GET /users/<id>/access`: el admin consulta las cuentas que administra
  (`can_manage_user`) y la suya; otra cuenta (otro admin, el superadmin, de
  un área ajena) → 404. Solo ve los accesos de plataformas de sus áreas.
- `last_job_id` se omite para el rol usuario (contrato) y se envía a los
  administradores.
- CSRF: la API v1 sigue exenta como el resto hasta FNC-008 (P13); la prueba
  `xfail(strict=True)` lo deja visible.
"""
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from app import db
from app.authz import (any_admin_required, can_manage_user, is_admin,
                       is_any_admin, managed_area_ids)
from app.modules.access import consultas, errores, rules, services
from app.modules.access.errores import ErrorDeAcceso
from app.modules.access.models import PlatformAccessGrant
from app.modules.access.serializacion import accesos_publicos
from app.modules.access.tipos import ESTADOS, ESTADOS_VIGENTES
from app.modules.api.helpers import (CAMPO_NO_PERMITIDO, CUERPO_INVALIDO,
                                     NO_ENCONTRADO, error_response,
                                     json_object)
from app.modules.audit.parametros import ParametroInvalido, leer_paginacion
from app.modules.auth.models import User

access_api_bp = Blueprint('api_access', __name__, url_prefix='/api/v1')

PARAMETRO_INVALIDO = ('Parámetro de consulta inválido.', 400,
                      'parametro_invalido')
FILTRO_VIGENTE = 'vigente'
CAMPOS_REVOCAR = frozenset({'reason'})


def _estados(args):
    """`status`: un estado del contrato o `vigente` (por defecto)."""
    valor = args.get('status') or FILTRO_VIGENTE
    if valor == FILTRO_VIGENTE:
        return ESTADOS_VIGENTES
    if valor not in ESTADOS:
        raise ParametroInvalido('status')
    return (valor,)


def _lista(usuario_id, area_ids=None):
    try:
        estados = _estados(request.args)
        paginacion = leer_paginacion(request.args)
    except ParametroInvalido as error:
        return error_response(*PARAMETRO_INVALIDO,
                              fields={error.campo: PARAMETRO_INVALIDO[0]})
    consulta = consultas.de_usuario(usuario_id, estados, area_ids)
    total = consulta.order_by(None).count()
    accesos = consulta.offset(paginacion.offset).limit(
        paginacion.per_page).all()
    return jsonify({
        'items': accesos_publicos(accesos, con_trabajo=is_any_admin()),
        'page': paginacion.page, 'per_page': paginacion.per_page,
        'total': total})


@access_api_bp.route('/me/access')
@login_required
def my_access():
    """Accesos propios; el superadmin no tiene registros (acceso por defecto)."""
    return _lista(current_user.id)


def _puede_consultar(cuenta):
    return cuenta.id == current_user.id or can_manage_user(cuenta)


@access_api_bp.route('/users/<int:user_id>/access')
@login_required
@any_admin_required
def user_access(user_id):
    cuenta = db.session.get(User, user_id)
    if cuenta is None or not _puede_consultar(cuenta):
        return error_response(*NO_ENCONTRADO)
    return _lista(cuenta.id, None if is_admin() else managed_area_ids())


def _motivo():
    datos = json_object()
    if datos is None:
        return None, error_response(*CUERPO_INVALIDO)
    if set(datos) - CAMPOS_REVOCAR:
        return None, error_response(*CAMPO_NO_PERMITIDO)
    return datos.get('reason'), None


@access_api_bp.route('/access/<int:access_id>/revoke', methods=['POST'])
@login_required
@any_admin_required
def revoke_access(access_id):
    acceso = db.session.get(PlatformAccessGrant, access_id)
    if acceso is None:
        return error_response(*NO_ENCONTRADO)
    try:
        # Alcance antes que el cuerpo: fuera de alcance no se distingue.
        rules.validar_revocacion(current_user, acceso)
    except ErrorDeAcceso as error:
        return error_response(*error.respuesta)
    motivo, rechazo = _motivo()
    if rechazo is not None:
        return rechazo
    try:
        services.revocar(acceso, actor=current_user, motivo=motivo)
        db.session.commit()
    except ErrorDeAcceso as error:
        db.session.rollback()
        return error_response(*error.respuesta)
    except IntegrityError:
        # Otra petición revocó el mismo acceso a la vez.
        db.session.rollback()
        return error_response(*errores.estado_invalido().respuesta)
    acceso_json, = accesos_publicos([acceso])
    return jsonify({'status': 'success', 'access': acceso_json})
