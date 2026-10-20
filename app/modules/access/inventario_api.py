"""API v1 del inventario de permisos: `GET /access/inventory` (FNC-059).

Contrato `accesos.md`. Solo lectura; usuario `403`, admin sus áreas y
superadmin todo (`inventario.visibles`). Parámetros:
- `area_id`, `platform_id`, `user_id`, `q`, `page`, `per_page`: reglas de
  `audit.parametros` (convenciones de `docs/contratos/README.md`);
- `level`, `origin`, `status` (por defecto `vigente`): lista blanca de
  `access.tipos`.
Un valor inválido responde `400 parametro_invalido`.

Forma `Access`: `access.serializacion.accesos_publicos` (FNC-058), con
`last_job_id` (solo admins). Blueprint propio, separado de `access/api.py`.
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from app.authz import any_admin_required
from app.modules.access import inventario
from app.modules.access.serializacion import accesos_publicos
from app.modules.access.tipos import ESTADOS, NIVELES, ORIGENES
from app.modules.api.helpers import error_response
from app.modules.audit.parametros import (POR_PAGINA_MAX, ParametroInvalido,
                                          leer_filtros, leer_paginacion)

access_inventory_api_bp = Blueprint('api_access_inventory', __name__,
                                    url_prefix='/api/v1')

PARAMETRO_INVALIDO = ('Parámetro de consulta inválido.', 400,
                      'parametro_invalido')
# Tope de `per_page` del inventario; no supera el de las convenciones.
ACCESS_INVENTORY_PAGE_SIZE_MAX = POR_PAGINA_MAX
CAMPOS_COMUNES = ('area_id', 'platform_id', 'user_id', 'q')
ESTADOS_FILTRO = frozenset(ESTADOS) | {inventario.ESTADO_VIGENTE}


def _invalido(campo):
    return error_response(*PARAMETRO_INVALIDO,
                          fields={campo: PARAMETRO_INVALIDO[0]})


def _enumerado(campo, permitidos):
    valor = request.args.get(campo) or None
    if valor is not None and valor not in permitidos:
        raise ParametroInvalido(campo)
    return valor


def _leer_filtros():
    comunes = leer_filtros({c: request.args.get(c) for c in CAMPOS_COMUNES})
    return inventario.FiltrosInventario(
        area_id=comunes.area_id, platform_id=comunes.platform_id,
        user_id=comunes.user_id, q=comunes.q,
        level=_enumerado('level', NIVELES),
        origin=_enumerado('origin', ORIGENES),
        status=(_enumerado('status', ESTADOS_FILTRO)
                or inventario.ESTADO_VIGENTE))


@access_inventory_api_bp.route('/access/inventory')
@login_required
@any_admin_required
def access_inventory():
    try:
        filtros = _leer_filtros()
        paginacion = leer_paginacion(request.args)
        if paginacion.per_page > ACCESS_INVENTORY_PAGE_SIZE_MAX:
            raise ParametroInvalido('per_page')
    except ParametroInvalido as error:
        return _invalido(error.campo)

    consulta = inventario.filtrar(inventario.visibles(current_user), filtros)
    total = consulta.order_by(None).count()
    accesos = (inventario.ordenados(consulta).offset(paginacion.offset)
               .limit(paginacion.per_page).all())
    return jsonify({'items': accesos_publicos(accesos),
                    'page': paginacion.page,
                    'per_page': paginacion.per_page, 'total': total})
