"""API v1 de auditoría: consulta por rol e historiales (FNC-060).

Contrato `docs/contratos/auditoria.md`. `GET /audit` salió de
`api/routes.py`; sin `page` responde el arreglo de siempre (pantalla
`audit-log.tsx`), con `page` la lista paginada. Solo lectura (SEC-AUD-03).

Campos según rol: `ip`, `before` y `after` solo para admin y superadmin; los
del admin siempre están en su alcance porque `visibles()` ya filtra por área.
"""

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app import db
from app.authz import (any_admin_required, can_manage_platform,
                       can_manage_user, is_admin, is_any_admin, is_area_admin)
from app.modules.api.helpers import NO_ENCONTRADO, error_response
from app.modules.audit import queries
from app.modules.audit.parametros import (ParametroInvalido, leer_filtros,
                                          leer_limite, leer_paginacion)
from app.modules.auth.models import User
from app.modules.core.models import Platform

audit_api_bp = Blueprint('api_audit', __name__, url_prefix='/api/v1')

PARAMETRO_INVALIDO = ('Parámetro de consulta inválido.', 400,
                      'parametro_invalido')
# Campos que el usuario normal recibe en null.
CAMPOS_SOLO_ADMIN = ('ip', 'before', 'after')


def _entrada(registro):
    datos = registro.to_dict()
    if not is_any_admin(current_user):
        datos.update(dict.fromkeys(CAMPOS_SOLO_ADMIN))
    return datos


def _invalido(error):
    return error_response(*PARAMETRO_INVALIDO,
                          fields={error.campo: PARAMETRO_INVALIDO[0]})


def _paginada(consulta, paginacion):
    total = consulta.order_by(None).count()
    registros = (queries.ordenados(consulta).offset(paginacion.offset)
                 .limit(paginacion.per_page).all())
    return jsonify({'items': [_entrada(r) for r in registros],
                    'page': paginacion.page,
                    'per_page': paginacion.per_page, 'total': total})


def _historial(criterio):
    """Respuesta paginada de los eventos visibles que cumplen `criterio`."""
    try:
        filtros = leer_filtros(request.args)
        paginacion = leer_paginacion(request.args)
    except ParametroInvalido as error:
        return _invalido(error)
    consulta = queries.filtrar(queries.visibles(current_user), filtros)
    return _paginada(consulta.filter(criterio), paginacion)


@audit_api_bp.route('/audit')
@login_required
def list_audit():
    """Eventos dentro del alcance del solicitante, con filtros."""
    try:
        filtros = leer_filtros(request.args)
        paginacion = (leer_paginacion(request.args)
                      if 'page' in request.args else None)
    except ParametroInvalido as error:
        return _invalido(error)
    consulta = queries.filtrar(queries.visibles(current_user), filtros)
    if paginacion is not None:
        return _paginada(consulta, paginacion)
    registros = (queries.ordenados(consulta)
                 .limit(leer_limite(request.args)).all())
    return jsonify([_entrada(r) for r in registros])


def _puede_ver_historial_de(cuenta):
    """Superadmin: cualquiera; admin: él mismo o cuentas que administra;
    usuario: solo él mismo."""
    if is_admin():
        return True
    if cuenta.id == current_user.id:
        return True
    return is_area_admin() and can_manage_user(cuenta)


@audit_api_bp.route('/audit/users/<int:user_id>')
@login_required
def user_history(user_id):
    """Historial de una cuenta (actor o afectada); fuera de alcance, 404."""
    cuenta = db.session.get(User, user_id)
    if cuenta is None or not _puede_ver_historial_de(cuenta):
        return error_response(*NO_ENCONTRADO)
    return _historial(queries.de_usuario(cuenta.id, cuenta.email))


@audit_api_bp.route('/audit/platforms/<int:platform_id>')
@login_required
@any_admin_required
def platform_history(platform_id):
    """Historial de una plataforma; de un área ajena, 404 (SEC-AUTHZ-04)."""
    plataforma = db.session.get(Platform, platform_id)
    if plataforma is None or not can_manage_platform(plataforma):
        return error_response(*NO_ENCONTRADO)
    return _historial(queries.de_plataforma(plataforma.id))
