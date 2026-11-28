"""Lógica de negocio y validaciones para la importación masiva (Bulk Import).
Permite procesar lotes de usuarios, áreas y plataformas en modo simulación (dry_run)
o ejecución real con auditoría.
"""

import logging
import re
from typing import Any, Dict, List, Tuple

from app import db
from app.modules.access.area_admin_sync import sincronizar_plataforma
from app.modules.areas import validacion as validacion_areas
from app.modules.audit.events import Evento
from app.modules.audit.services import add_audit_log
from app.modules.auth.acceso_local import origen_de_alta
from app.modules.auth.models import User
from app.modules.core.models import Area, Platform
from app.modules.platforms.tipos import TIPO_CONECTOR
from app.modules.platforms.validacion import validar_campos
from app.modules.users.roles import RESERVED_NAMES, rol_asignable
from app.utils.naming import sanitize_display_name

logger = logging.getLogger(__name__)

PATRON_CORREO = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
MAX_REGISTROS_POR_LOTE = 500
# Valores de `is_active` que desactivan la cuenta (el CSV llega como texto).
VALORES_INACTIVO = ('false', '0', 'no', 'inactivo')
MENSAJE_ERROR_INTERNO = 'No se pudo completar la importación. Revisa el registro del servidor.'


def _activo(valor: Any) -> bool:
    """`is_active` del registro: por omisión activa; texto falso la desactiva."""
    if valor is None or valor == '':
        return True
    if isinstance(valor, bool):
        return valor
    return str(valor).strip().lower() not in VALORES_INACTIVO


def _errores_de_campo(errores: Dict[str, str]) -> str:
    return '; '.join(f'{campo}: {mensaje}' for campo, mensaje in errores.items())


def _parse_lista_areas(areas_raw: Any) -> List[str]:
    """Convierte una cadena o lista de nombres/IDs de área en lista limpia de strings."""
    if isinstance(areas_raw, list):
        return [str(a).strip() for a in areas_raw if str(a).strip()]
    if isinstance(areas_raw, str):
        # Separar por coma o punto y coma
        partes = re.split(r'[,;]+', areas_raw)
        return [p.strip() for p in partes if p.strip()]
    return []


def procesar_usuarios(
    registros: List[Dict[str, Any]], dry_run: bool = False,
    auth_source: str | None = None, actor: Any = None,
) -> Dict[str, Any]:
    """Valida e importa una lista de usuarios.

    `auth_source` fuerza el origen de las cuentas nuevas (la CLI `flask alta`
    importa personas del directorio como `sso`); sin él rige `origen_de_alta()`.
    `actor` decide qué roles se pueden asignar; sin él, el de la sesión.
    """
    errores = []
    items_procesados = []
    creados = 0

    # Cache de áreas existentes para búsquedas rápidas (por nombre en minúsculas y por ID)
    todas_areas = Area.query.all()
    areas_por_nombre = {a.name.strip().lower(): a for a in todas_areas}
    areas_por_id = {str(a.id): a for a in todas_areas}

    # Cache de correos existentes
    correos_existentes = {
        u.email.lower() for u in User.query.with_entities(User.email).all()
    }
    correos_en_lote = set()

    for idx, reg in enumerate(registros):
        fila = idx + 1
        email_raw = str(reg.get('email') or reg.get('correo') or '').strip().lower()
        nombre_raw = str(reg.get('name') or reg.get('nombre') or '').strip()
        rol_raw = str(reg.get('role') or reg.get('rol') or 'usuario').strip().lower()
        areas_raw = reg.get('areas') or reg.get('areas_ids') or ''

        item_resumen = {
            'row': fila,
            'email': email_raw,
            'name': nombre_raw,
            'role': rol_raw,
            'status': 'valid',
            'error': None,
        }

        # 1. Validación de correo
        if not email_raw:
            msg = 'El correo electrónico es obligatorio.'
            errores.append({'row': fila, 'item': email_raw or f'Fila {fila}', 'error': msg})
            item_resumen['status'] = 'error'
            item_resumen['error'] = msg
            items_procesados.append(item_resumen)
            continue

        if not PATRON_CORREO.match(email_raw):
            msg = 'El formato del correo electrónico no es válido.'
            errores.append({'row': fila, 'item': email_raw, 'error': msg})
            item_resumen['status'] = 'error'
            item_resumen['error'] = msg
            items_procesados.append(item_resumen)
            continue

        if email_raw in RESERVED_NAMES:
            msg = 'Ese identificador está reservado por el sistema.'
            errores.append({'row': fila, 'item': email_raw, 'error': msg})
            item_resumen['status'] = 'error'
            item_resumen['error'] = msg
            items_procesados.append(item_resumen)
            continue

        if email_raw in correos_existentes or email_raw in correos_en_lote:
            msg = 'Ya existe una cuenta registrada con este correo electrónico.'
            errores.append({'row': fila, 'item': email_raw, 'error': msg})
            item_resumen['status'] = 'error'
            item_resumen['error'] = msg
            items_procesados.append(item_resumen)
            continue

        # 2. Validación de rol (Seguridad: jamás administrador vía bulk import)
        if rol_raw in ('administrador', 'admin', 'superadmin'):
            msg = 'No se permite asignar el rol de administrador en la importación masiva.'
            errores.append({'row': fila, 'item': email_raw, 'error': msg})
            item_resumen['status'] = 'error'
            item_resumen['error'] = msg
            items_procesados.append(item_resumen)
            continue

        if not rol_asignable(rol_raw, actor):
            msg = f'El rol "{rol_raw}" no es válido. Usa "usuario" o "admin_area".'
            errores.append({'row': fila, 'item': email_raw, 'error': msg})
            item_resumen['status'] = 'error'
            item_resumen['error'] = msg
            items_procesados.append(item_resumen)
            continue

        # 3. Validación y saneamiento de nombre
        nombre_final = sanitize_display_name(nombre_raw, fallback=email_raw)

        # 4. Asignación de áreas
        nombres_o_ids = _parse_lista_areas(areas_raw)
        areas_asignadas = []
        areas_no_encontradas = []
        for a_ident in nombres_o_ids:
            ident_clean = a_ident.lower()
            if ident_clean in areas_por_nombre:
                areas_asignadas.append(areas_por_nombre[ident_clean])
            elif a_ident in areas_por_id:
                areas_asignadas.append(areas_por_id[a_ident])
            else:
                areas_no_encontradas.append(a_ident)

        if areas_no_encontradas:
            msg = f"Las siguientes áreas no existen: {', '.join(areas_no_encontradas)}"
            errores.append({'row': fila, 'item': email_raw, 'error': msg})
            item_resumen['status'] = 'error'
            item_resumen['error'] = msg
            items_procesados.append(item_resumen)
            continue

        correos_en_lote.add(email_raw)
        creados += 1
        item_resumen['areas'] = [a.name for a in areas_asignadas]
        items_procesados.append(item_resumen)

        if not dry_run:
            nuevo_usuario = User(
                email=email_raw,
                nombre=nombre_final,
                role=rol_raw,
                auth_source=auth_source or origen_de_alta(),
                is_active=_activo(reg.get('is_active')),
            )
            nuevo_usuario.areas = areas_asignadas
            db.session.add(nuevo_usuario)
            add_audit_log(f'CREAR USUARIO: {email_raw}', module='Usuarios',
                          target=email_raw, status='success',
                          detail='Importación masiva', commit=False)

    if not dry_run and creados > 0:
        db.session.commit()

    return {
        'status': 'success',
        'entity': 'users',
        'dry_run': dry_run,
        'total': len(registros),
        'valid': creados,
        'created': 0 if dry_run else creados,
        'errors': errores,
        'items': items_procesados,
    }


def procesar_areas(
    registros: List[Dict[str, Any]], dry_run: bool = False
) -> Dict[str, Any]:
    """Valida e importa una lista de áreas."""
    errores = []
    items_procesados = []
    creados = 0

    nombres_existentes = {
        a.name.strip().casefold() for a in Area.query.with_entities(Area.name).all()
    }
    nombres_en_lote = set()

    for idx, reg in enumerate(registros):
        fila = idx + 1
        nombre_raw = str(reg.get('name') or reg.get('nombre') or '').strip()
        item_resumen = {
            'row': fila,
            'name': nombre_raw,
            'description': str(reg.get('description') or reg.get('descripcion') or '').strip(),
            'status': 'valid',
            'error': None,
        }

        # Mismas reglas que `POST /areas` (lista blanca de ícono y color #rrggbb).
        datos = {'name': nombre_raw}
        for campo, claves in (('description', ('description', 'descripcion')),
                              ('color', ('color',)), ('icon', ('icon', 'icono'))):
            valor = next((reg.get(c) for c in claves if reg.get(c) not in (None, '')), None)
            if valor is not None:
                datos[campo] = str(valor).strip()
        valores, errores_campo = validacion_areas.validar(datos, es_alta=True)
        if errores_campo:
            msg = _errores_de_campo(errores_campo)
            errores.append({'row': fila, 'item': nombre_raw or f'Fila {fila}', 'error': msg})
            item_resumen['status'] = 'error'
            item_resumen['error'] = msg
            items_procesados.append(item_resumen)
            continue

        nombre_saneado = valores['name']
        clave_nombre = nombre_saneado.casefold()
        if clave_nombre in nombres_existentes or clave_nombre in nombres_en_lote:
            msg = f'Ya existe un área con el nombre "{nombre_saneado}".'
            errores.append({'row': fila, 'item': nombre_raw, 'error': msg})
            item_resumen['status'] = 'error'
            item_resumen['error'] = msg
            items_procesados.append(item_resumen)
            continue

        nombres_en_lote.add(clave_nombre)
        creados += 1
        item_resumen['name'] = nombre_saneado
        items_procesados.append(item_resumen)

        if not dry_run:
            nueva_area = Area(
                name=nombre_saneado,
                description=valores.get('description'),
                color=valores.get('color', validacion_areas.COLOR_POR_OMISION),
                icon=valores.get('icon', validacion_areas.ICONO_POR_OMISION),
                # FNC-220: sin admin no se puede activar; se activa después.
                status=validacion_areas.ESTADO_INACTIVO,
            )
            db.session.add(nueva_area)
            add_audit_log(f'CREAR ÁREA: {nombre_saneado}', module='Áreas',
                          target=nombre_saneado, status='success',
                          detail='Importación masiva', commit=False)

    if not dry_run and creados > 0:
        db.session.commit()

    return {
        'status': 'success',
        'entity': 'areas',
        'dry_run': dry_run,
        'total': len(registros),
        'valid': creados,
        'created': 0 if dry_run else creados,
        'errors': errores,
        'items': items_procesados,
    }


def procesar_plataformas(
    registros: List[Dict[str, Any]], dry_run: bool = False
) -> Dict[str, Any]:
    """Valida e importa una lista de plataformas."""
    errores = []
    items_procesados = []
    creados = 0

    todas_areas = Area.query.all()
    areas_por_nombre = {a.name.strip().lower(): a for a in todas_areas}
    areas_por_id = {str(a.id): a for a in todas_areas}

    plataformas_existentes = {
        (p.area_id, p.name.strip().lower())
        for p in Platform.query.with_entities(Platform.area_id, Platform.name).all()
    }
    plataformas_en_lote = set()

    for idx, reg in enumerate(registros):
        fila = idx + 1
        nombre_raw = str(reg.get('name') or reg.get('nombre') or '').strip()
        descripcion_raw = str(reg.get('description') or reg.get('descripcion') or '').strip()
        area_raw = str(reg.get('area') or reg.get('area_name') or reg.get('area_id') or '').strip()
        enlace_raw = str(reg.get('direct_link') or reg.get('enlace') or reg.get('url') or '').strip()
        icon_raw = str(reg.get('icon') or reg.get('icono') or 'plataformas').strip()

        item_resumen = {
            'row': fila,
            'name': nombre_raw,
            'area': area_raw,
            'status': 'valid',
            'error': None,
        }

        if not nombre_raw:
            msg = 'El nombre de la plataforma es obligatorio.'
            errores.append({'row': fila, 'item': f'Fila {fila}', 'error': msg})
            item_resumen['status'] = 'error'
            item_resumen['error'] = msg
            items_procesados.append(item_resumen)
            continue

        if not descripcion_raw:
            msg = 'La descripción de la plataforma es obligatoria.'
            errores.append({'row': fila, 'item': nombre_raw, 'error': msg})
            item_resumen['status'] = 'error'
            item_resumen['error'] = msg
            items_procesados.append(item_resumen)
            continue

        # Resolver el área
        area_obj = None
        if area_raw.lower() in areas_por_nombre:
            area_obj = areas_por_nombre[area_raw.lower()]
        elif area_raw in areas_por_id:
            area_obj = areas_por_id[area_raw]

        if area_obj is None:
            msg = f'El área "{area_raw}" no existe en el sistema.'
            errores.append({'row': fila, 'item': nombre_raw, 'error': msg})
            item_resumen['status'] = 'error'
            item_resumen['error'] = msg
            items_procesados.append(item_resumen)
            continue

        # Mismas reglas que `POST /platforms`: enlace solo https, largos y texto visual.
        datos = {'name': nombre_raw, 'description': descripcion_raw, 'area_id': area_obj.id,
                 'integration_type': TIPO_CONECTOR, 'icon': icon_raw}
        if enlace_raw:
            datos['direct_link'] = enlace_raw
        limpios, errores_campo = validar_campos(datos, alta=True)
        if errores_campo:
            msg = _errores_de_campo(errores_campo)
            errores.append({'row': fila, 'item': nombre_raw, 'error': msg})
            item_resumen['status'] = 'error'
            item_resumen['error'] = msg
            items_procesados.append(item_resumen)
            continue

        nombre_saneado = limpios['name']
        par_clave = (area_obj.id, nombre_saneado.lower())

        if par_clave in plataformas_existentes or par_clave in plataformas_en_lote:
            msg = f'Ya existe una plataforma con el nombre "{nombre_saneado}" en el área "{area_obj.name}".'
            errores.append({'row': fila, 'item': nombre_raw, 'error': msg})
            item_resumen['status'] = 'error'
            item_resumen['error'] = msg
            items_procesados.append(item_resumen)
            continue

        plataformas_en_lote.add(par_clave)
        creados += 1
        item_resumen['name'] = nombre_saneado
        item_resumen['area'] = area_obj.name
        items_procesados.append(item_resumen)

        if not dry_run:
            nueva_plataforma = Platform(
                name=nombre_saneado,
                description=limpios['description'],
                area_id=area_obj.id,
                direct_link=limpios.get('direct_link'),
                icon=limpios.get('icon') or 'plataformas',
                status='Activo',
                integration_type=TIPO_CONECTOR,
            )
            db.session.add(nueva_plataforma)
            db.session.flush()
            add_audit_log(Evento.PLATAFORMA_CREADA, status='success', module='Plataformas',
                          target=nueva_plataforma.name, platform_id=nueva_plataforma.id,
                          area_id=area_obj.id, detail='Importación masiva', commit=False)
            # Como el alta normal: los admins del área reciben su acceso automático (P6).
            sincronizar_plataforma(nueva_plataforma)

    if not dry_run and creados > 0:
        db.session.commit()

    return {
        'status': 'success',
        'entity': 'platforms',
        'dry_run': dry_run,
        'total': len(registros),
        'valid': creados,
        'created': 0 if dry_run else creados,
        'errors': errores,
        'items': items_procesados,
    }


def ejecutar_importacion_masiva(
    entidad: str, registros: List[Dict[str, Any]], dry_run: bool = False
) -> Tuple[Dict[str, Any], int]:
    """Punto de entrada principal para la importación masiva."""
    entidades_permitidas = {
        'users': procesar_usuarios,
        'usuarios': procesar_usuarios,
        'areas': procesar_areas,
        'platforms': procesar_plataformas,
        'plataformas': procesar_plataformas,
    }

    entidad_normalizada = (entidad or '').strip().lower()
    if entidad_normalizada not in entidades_permitidas:
        return {
            'status': 'error',
            'message': 'Entidad no soportada. Opciones válidas: users, areas, platforms.',
            'code': 'entidad_invalida',
        }, 400

    if not isinstance(registros, list):
        return {
            'status': 'error',
            'message': 'Los registros deben proporcionarse como una lista.',
            'code': 'cuerpo_invalido',
        }, 400

    if not all(isinstance(reg, dict) for reg in registros):
        return {
            'status': 'error',
            'message': 'Cada registro debe ser un objeto con sus campos.',
            'code': 'cuerpo_invalido',
        }, 400

    if len(registros) > MAX_REGISTROS_POR_LOTE:
        return {
            'status': 'error',
            'message': f'El lote no puede superar {MAX_REGISTROS_POR_LOTE} registros por operación.',
            'code': 'lote_excedido',
        }, 400

    if len(registros) == 0:
        return {
            'status': 'success',
            'entity': entidad_normalizada,
            'dry_run': dry_run,
            'total': 0,
            'valid': 0,
            'created': 0,
            'errors': [],
            'items': [],
        }, 200

    try:
        procesador = entidades_permitidas[entidad_normalizada]
        resultado = procesador(registros, dry_run=dry_run)
        return resultado, 200
    except Exception:  # el detalle va al registro, nunca al cliente
        db.session.rollback()
        logger.exception('Importación masiva de %s fallida', entidad_normalizada)
        return {
            'status': 'error',
            'message': MENSAJE_ERROR_INTERNO,
            'code': 'error_interno',
        }, 500

