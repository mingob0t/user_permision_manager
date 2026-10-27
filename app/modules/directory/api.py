"""API v1 del directorio OpenLDAP (FNC-043).

- `GET /auth-config`: configuración efectiva (variables `LDAP_*`), su origen
  y si está activa; sin la contraseña de bind (SEC-LDAP-11).
- `PUT /auth-config`: ADR-004 deja toda la configuración en el entorno; la
  lista blanca está vacía y cualquier campo da `400 campo_no_permitido`.
- `POST /auth-config/test`: prueba la conexión con la configuración efectiva;
  no acepta host ni credenciales en el cuerpo (SEG-22) y responde un mensaje
  genérico (SEG-21).
- `GET /directory/search`: búsqueda de personas para el alta, con el cliente
  centralizado (`uid`, filtro escapado, TLS validado).

Todo es exclusivo del superadmin (`admin_required`), como antes en `admin.py`.
"""
import logging

from flask import Blueprint, jsonify, request
from flask_login import login_required

from app.authz import admin_required
from app.modules.api.helpers import error_response, leer_cuerpo
from app.modules.audit.services import add_audit_log
from app.modules.directory.configuracion import (ErrorConfiguracionDirectorio,
                                                 directorio_activo)
from app.modules.directory.ldap_client import ClienteDirectorio, ErrorDirectorio
from app.modules.directory.resumen import configuracion_publica
from app.modules.users.correos import correos_registrados

logger = logging.getLogger(__name__)

directory_api_bp = Blueprint('api_directory', __name__, url_prefix='/api/v1')

# Longitud del texto de búsqueda (caracteres, tras quitar espacios).
MIN_BUSQUEDA = 2
MAX_BUSQUEDA = 64

NO_CONFIGURADO = ('El directorio no está configurado: se definen las '
                  'variables LDAP_* del entorno.', 409,
                  'directorio_no_configurado')
NO_DISPONIBLE = ('No se pudo conectar con el directorio; intenta más tarde.',
                 503, 'directorio_no_disponible')
BUSQUEDA_INVALIDA = (f'Indica entre {MIN_BUSQUEDA} y {MAX_BUSQUEDA} '
                     'caracteres.', 400, 'parametro_invalido')
MENSAJE_CONEXION_OK = 'Conexión establecida con el directorio.'

ACCION_PRUEBA = 'PRUEBA LDAP'
MODULO_AUDITORIA = 'Seguridad'


@directory_api_bp.route('/auth-config')
@login_required
@admin_required
def get_auth_config():
    return jsonify(configuracion_publica())


@directory_api_bp.route('/auth-config', methods=['PUT'])
@login_required
@admin_required
def save_auth_config():
    """Sin campos editables: la configuración y la credencial van en el entorno."""
    _, error = leer_cuerpo()
    if error:
        return error
    return jsonify({'status': 'success', 'config': configuracion_publica()})


@directory_api_bp.route('/auth-config/test', methods=['POST'])
@login_required
@admin_required
def test_auth_config():
    """Bind de la cuenta de servicio con la configuración efectiva."""
    _, error = leer_cuerpo()
    if error:
        return error
    if not directorio_activo():
        return error_response(*NO_CONFIGURADO)
    try:
        cliente = ClienteDirectorio()
        with cliente.conexion_servicio():
            pass
    except (ErrorDirectorio, ErrorConfiguracionDirectorio) as exc:
        if isinstance(exc, ErrorConfiguracionDirectorio):
            logger.error('Directorio: configuración inválida: %s', exc)
        add_audit_log(ACCION_PRUEBA, module=MODULO_AUDITORIA, status='error',
                      detail=NO_DISPONIBLE[2])
        return error_response(*NO_DISPONIBLE)
    add_audit_log(ACCION_PRUEBA, module=MODULO_AUDITORIA, status='success')
    return jsonify({'status': 'success', 'message': MENSAJE_CONEXION_OK})


@directory_api_bp.route('/directory/search')
@login_required
@admin_required
def directory_search():
    """Personas del directorio para darlas de alta; marca las que ya existen."""
    texto = (request.args.get('q') or '').strip()
    if not MIN_BUSQUEDA <= len(texto) <= MAX_BUSQUEDA:
        return error_response(*BUSQUEDA_INVALIDA)
    if not directorio_activo():
        return error_response(*NO_CONFIGURADO)
    try:
        personas = ClienteDirectorio().buscar_personas(texto)
    except (ErrorDirectorio, ErrorConfiguracionDirectorio) as exc:
        if isinstance(exc, ErrorConfiguracionDirectorio):
            logger.error('Directorio: configuración inválida: %s', exc)
        return error_response(*NO_DISPONIBLE)

    existentes = correos_registrados(
        {(p.atributos.get('mail') or '').lower() for p in personas} - {''})
    resultados = [{
        'name': p.atributos.get('displayName') or p.atributos.get('cn') or '',
        'email': p.atributos.get('mail') or '',
        'account': p.identificador,
        'exists': (p.atributos.get('mail') or '').lower() in existentes,
    } for p in personas]
    return jsonify({'count': len(resultados), 'users': resultados})

