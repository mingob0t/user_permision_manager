"""API v1 de áreas: alta, edición y baja (FNC-045).

Contrato: `docs/contratos/areas-y-roles.md`; matriz: Anexo A de
`docs/seguridad/LINEAMIENTOS.md`.

- Alta: superadmin o admin de área; el admin queda en `area_admins` del área
  nueva en la misma transacción.
- Edición y baja: admin (sus áreas) o superadmin; área ajena o inexistente
  → 404 (SEC-AUTHZ-03/04).
- Cada escritura audita en la misma transacción (SEC-AUD-06).

Separado de `api/crud.py` para no hacer crecer ese archivo.
"""

from flask import Blueprint, jsonify
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from app import db
from app.authz import any_admin_required, can_manage_area, is_area_admin
from app.modules.api.helpers import (AREA_DUPLICADA, NO_ENCONTRADO,
                                     error_response, leer_cuerpo,
                                     validation_error)
from app.modules.areas import validacion
from app.modules.areas.baja import conflicto_de_baja, desligar_auditoria
from app.modules.audit.events import Evento
from app.modules.audit.services import add_audit_log
from app.modules.core.models import Area

areas_api_bp = Blueprint('api_areas', __name__, url_prefix='/api/v1')

MODULO_AUDITORIA = 'Áreas'


def _entrada(es_alta, area=None):
    """(valores, None) con la entrada válida, o (None, respuesta de error)."""
    datos, error = leer_cuerpo(validacion.CAMPOS_PERMITIDOS)
    if error is not None:
        return None, error
    if area is not None:
        # Reenviar el valor que ya tiene no es un cambio: el formulario manda
        # todos los campos y un área heredada puede no cumplir el formato.
        datos = {k: v for k, v in datos.items() if getattr(area, k) != v}
    valores, errores = validacion.validar(datos, es_alta)
    if errores:
        return None, validation_error(errores)
    nombre = valores.get('name')
    if nombre and validacion.nombre_duplicado(
            nombre, excepto_id=area.id if area is not None else None):
        return None, error_response(*AREA_DUPLICADA)
    return valores, None


def _area_gestionable(area_id):
    """El área si quien llama la administra; si no, None (→ 404)."""
    area = db.session.get(Area, area_id)
    if area is None or not can_manage_area(area.id):
        return None
    return area


def _guardar():
    """Confirma la transacción; None si se guardó o la respuesta de error.

    Si otra petición ganó la carrera por el mismo nombre, la restricción
    única de `areas.name` falla: se deshace todo y se responde 409.
    """
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error_response(*AREA_DUPLICADA)
    return None


def _auditar(evento, area, status='success', area_id=None, antes=None,
             despues=None):
    add_audit_log(evento, status=status, module=MODULO_AUDITORIA,
                  target=area.name, area_id=area_id, before=antes,
                  after=despues, commit=False)


@areas_api_bp.route('/areas', methods=['POST'])
@login_required
@any_admin_required
def create_area():
    """Alta de un área; el admin de área queda como su administrador."""
    valores, error = _entrada(es_alta=True)
    if error:
        return error

    area = Area(
        name=valores['name'],
        description=valores.get('description'),
        icon=valores.get('icon', validacion.ICONO_POR_OMISION),
        color=valores.get('color', validacion.COLOR_POR_OMISION),
        status=valores.get('status', validacion.ESTADO_POR_OMISION),
    )
    db.session.add(area)
    if is_area_admin():
        current_user.managed_areas.append(area)
    try:
        db.session.flush()
    except IntegrityError:
        db.session.rollback()
        return error_response(*AREA_DUPLICADA)
    _auditar(Evento.AREA_CREADA, area, area_id=area.id,
             despues=area.to_dict())
    error = _guardar()
    if error:
        return error
    return jsonify({'status': 'success', 'area': area.to_dict()}), 201


@areas_api_bp.route('/areas/<int:area_id>', methods=['PUT'])
@login_required
@any_admin_required
def update_area(area_id):
    area = _area_gestionable(area_id)
    if area is None:
        return error_response(*NO_ENCONTRADO)
    valores, error = _entrada(es_alta=False, area=area)
    if error:
        return error

    if not valores:
        return jsonify({'status': 'success', 'area': area.to_dict()})
    antes = area.to_dict()
    for campo, valor in valores.items():
        setattr(area, campo, valor)
    _auditar(Evento.AREA_EDITADA, area, area_id=area.id, antes=antes,
             despues=area.to_dict())
    error = _guardar()
    if error:
        return error
    return jsonify({'status': 'success', 'area': area.to_dict()})


@areas_api_bp.route('/areas/<int:area_id>', methods=['DELETE'])
@login_required
@any_admin_required
def delete_area(area_id):
    """Baja de un área (P11): admin de esa área o superadmin."""
    area = _area_gestionable(area_id)
    if area is None:
        return error_response(*NO_ENCONTRADO)
    conflicto = conflicto_de_baja(area, current_user)
    if conflicto:
        return error_response(*conflicto)

    # Sin `area_id`: la fila del área desaparece y la referencia quedaría en
    # NULL; el nombre y el estado previo quedan en `target` y `before`.
    _auditar(Evento.AREA_ELIMINADA, area, status='warning',
             antes=area.to_dict())
    desligar_auditoria(area)
    db.session.delete(area)
    db.session.commit()
    return jsonify({'status': 'success'})
