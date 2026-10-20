"""API v1 de ejecuciones: bitácora y reintento manual (FNC-062, contrato
`docs/contratos/conectores-y-ejecuciones.md`).

| Ruta | Usuario | Admin | Superadmin |
|---|---|---|---|
| `GET /provisioning/jobs` | 403 | sus áreas | todo |
| `GET /provisioning/jobs/<id>` | 403 | sus áreas; ajena → 404 | todo |
| `POST /provisioning/jobs/<id>/retry` | 403 | 403 (P10) | 200 |

- Parámetros: `area_id`, `platform_id`, `user_id`, `from`, `to`, `page`,
  `per_page` con las reglas de `audit.parametros`; `access_id` entero;
  `status`, `operation`, `provider` con lista blanca de `provisioning.tipos`.
  Un valor inválido → `400 parametro_invalido`.
- `from`/`to` sin zona se leen en la hora local del proceso, como en la
  auditoría, y se comparan en UTC (los trabajos se guardan en UTC).
- Reintento: `escritura_del_portal` (cuerpo JSON `{}` obligatorio mientras
  no esté FNC-008, P13); cualquier campo → `400 campo_no_permitido`.
"""
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app import db
from app.authz import admin_required, any_admin_required
from app.modules.api.csrf_provisional import escritura_del_portal
from app.modules.api.helpers import (CAMPO_NO_PERMITIDO, CUERPO_INVALIDO,
                                     NO_ENCONTRADO, error_response,
                                     json_object)
from app.modules.audit.parametros import (ParametroInvalido, leer_entero,
                                          leer_filtros, leer_paginacion)
from app.modules.provisioning import consultas, reintento
from app.modules.provisioning.models import ProvisioningJob
from app.modules.provisioning.serializacion import (trabajo_con_intentos,
                                                    trabajos_publicos)
from app.modules.provisioning.tipos import ESTADOS, OPERACIONES, PROVEEDORES

provisioning_api_bp = Blueprint('api_provisioning', __name__,
                                url_prefix='/api/v1/provisioning')

PARAMETRO_INVALIDO = ('Parámetro de consulta inválido.', 400,
                      'parametro_invalido')
CAMPOS_COMUNES = ('area_id', 'platform_id', 'user_id', 'from', 'to')
ESTADO_INVALIDO = 409, 'estado_invalido'


def _enumerado(campo, permitidos):
    valor = request.args.get(campo) or None
    if valor is not None and valor not in permitidos:
        raise ParametroInvalido(campo)
    return valor


def _leer_filtros():
    comunes = leer_filtros({c: request.args.get(c) for c in CAMPOS_COMUNES})
    return consultas.FiltrosTrabajos(
        status=_enumerado('status', ESTADOS),
        operation=_enumerado('operation', OPERACIONES),
        provider=_enumerado('provider', PROVEEDORES),
        area_id=comunes.area_id, platform_id=comunes.platform_id,
        user_id=comunes.user_id,
        access_id=leer_entero(request.args, 'access_id'),
        desde=consultas.a_utc(comunes.desde),
        hasta=consultas.a_utc(comunes.hasta))


@provisioning_api_bp.route('/jobs')
@login_required
@any_admin_required
def list_jobs():
    try:
        filtros = _leer_filtros()
        paginacion = leer_paginacion(request.args)
    except ParametroInvalido as error:
        return error_response(*PARAMETRO_INVALIDO,
                              fields={error.campo: PARAMETRO_INVALIDO[0]})
    consulta = consultas.filtrar(consultas.visibles(current_user), filtros)
    total = consulta.order_by(None).count()
    trabajos = (consultas.ordenados(consulta).offset(paginacion.offset)
                .limit(paginacion.per_page).all())
    return jsonify({'items': trabajos_publicos(trabajos),
                    'page': paginacion.page,
                    'per_page': paginacion.per_page, 'total': total})


@provisioning_api_bp.route('/jobs/<int:job_id>')
@login_required
@any_admin_required
def get_job(job_id):
    # Fuera de alcance = inexistente (SEC-AUTHZ-03/04).
    trabajo = consultas.visibles(current_user).filter(
        ProvisioningJob.id == job_id).first()
    if trabajo is None:
        return error_response(*NO_ENCONTRADO)
    return jsonify(trabajo_con_intentos(trabajo))


@provisioning_api_bp.route('/jobs/<int:job_id>/retry', methods=['POST'])
@login_required
@admin_required
@escritura_del_portal
def retry_job(job_id):
    datos = json_object()
    if datos is None:
        return error_response(*CUERPO_INVALIDO)
    if datos:
        return error_response(*CAMPO_NO_PERMITIDO)
    trabajo = db.session.get(ProvisioningJob, job_id)
    if trabajo is None:
        return error_response(*NO_ENCONTRADO)
    try:
        reintento.reintentar(trabajo)
        db.session.commit()
    except reintento.ReintentoInvalido as error:
        db.session.rollback()
        return error_response(str(error), *ESTADO_INVALIDO)
    return jsonify({'status': 'success', 'job': trabajo_con_intentos(trabajo)})
