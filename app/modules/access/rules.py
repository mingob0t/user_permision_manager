"""Reglas de los accesos otorgados: transiciones, alcance y niveles (FNC-054).

Funciones puras sobre los objetos; no consultan ni escriben la BD salvo las
relaciones ya cargadas. Lanzan `ErrorDeAcceso` (`errores.py`).

Decisiones del orquestador (pendientes de validar en la prueba de concepto):
- Otorgar por solicitud: quien aprueba administra la plataforma y a la cuenta
  (`can_manage_user`: un admin nunca otorga a otro admin ni al superadmin,
  SEC-AUTHZ-06), y la cuenta pertenece al área de la plataforma (P1).
- Solo se sube de nivel (P5, `requestable_levels`); el acceso que se reemplaza
  debe estar `activo`.
- El superadmin no recibe accesos: tiene acceso por defecto y no entra a los
  grupos LDAP (P6). `409 acceso_por_defecto` solo lo ve un superadmin; a un
  admin de área le da 404 (no revela quién es el superadmin).
- No se otorga a una cuenta inactiva: `409 cuenta_inactiva` (defensa en
  profundidad; el contrato no lo define).
"""
from app.authz import (can_manage_platform, can_manage_user, is_admin,
                       is_area_admin, managed_area_ids)
from app.modules.access import errores
from app.modules.access.tipos import (ESTADO_ACTIVO, ESTADO_EN_PROCESO,
                                      ESTADO_FALLIDO, ESTADO_FALLO_REVOCACION,
                                      ESTADO_REVOCADO, ESTADO_REVOCANDO,
                                      ESTADOS_OCUPANTES, LARGO_MOTIVO,
                                      NIVEL_USUARIO, NIVELES,
                                      ORIGEN_ADMIN_DE_AREA, ORIGEN_SOLICITUD,
                                      ORIGENES, RANGO_NIVEL)

# Máquina de estados del contrato `accesos.md`.
TRANSICIONES = {
    ESTADO_EN_PROCESO: frozenset({ESTADO_ACTIVO, ESTADO_FALLIDO}),
    ESTADO_ACTIVO: frozenset({ESTADO_REVOCANDO}),
    ESTADO_FALLIDO: frozenset({ESTADO_EN_PROCESO}),
    ESTADO_REVOCANDO: frozenset({ESTADO_REVOCADO, ESTADO_FALLO_REVOCACION}),
    ESTADO_REVOCADO: frozenset(),
    ESTADO_FALLO_REVOCACION: frozenset({ESTADO_REVOCANDO}),
}


def puede_pasar(origen, destino):
    return destino in TRANSICIONES.get(origen, frozenset())


# --------------------------------------------------------------------------- #
# Datos
# --------------------------------------------------------------------------- #

def validar_datos(nivel, origen, request_id):
    if nivel not in NIVELES:
        raise errores.validacion('level', 'Nivel desconocido.')
    if origen not in ORIGENES:
        raise errores.validacion('origin', 'Origen desconocido.')
    if origen == ORIGEN_SOLICITUD and not isinstance(request_id, int):
        # F-AUD-02: todo acceso por solicitud dice qué solicitud lo originó.
        raise errores.validacion('request_id', 'Falta la solicitud.')
    if origen == ORIGEN_ADMIN_DE_AREA and nivel != NIVEL_USUARIO:
        raise errores.validacion('level', 'El acceso automático es de nivel '
                                          'usuario.')  # P6


def limpiar_motivo(motivo):
    """P7: opcional y sin mínimo; ≤ 500 si llega."""
    if motivo is None:
        return None
    if not isinstance(motivo, str):
        raise errores.validacion('reason', 'Debe ser texto.')
    motivo = motivo.strip()
    if len(motivo) > LARGO_MOTIVO:
        raise errores.validacion('reason',
                                 f'Máximo {LARGO_MOTIVO} caracteres.')
    return motivo or None


# --------------------------------------------------------------------------- #
# Alcance
# --------------------------------------------------------------------------- #

def _mismo(uno, otro):
    return uno is not None and otro is not None and uno.id == otro.id


def _administra_area(usuario, area_id):
    return is_area_admin(usuario) and area_id in managed_area_ids(usuario)


def validar_otorgamiento(actor, usuario, plataforma, origen):
    """Quién puede otorgar qué a quién (SEC-AUTHZ-03/06/07/08)."""
    if usuario is None or plataforma is None:
        raise errores.fuera_de_alcance()
    if origen == ORIGEN_ADMIN_DE_AREA:
        # Lo otorga el sistema (FNC-055) a un admin del área de la plataforma.
        # Sin actor humano no hay nada que ocultar: la cuenta inactiva se
        # dice antes (`authz` trata a una cuenta inactiva como sin rol).
        if actor is None and not usuario.is_active:
            raise errores.cuenta_inactiva()
        if actor is not None or not _administra_area(usuario,
                                                     plataforma.area_id):
            raise errores.fuera_de_alcance()
    else:
        _validar_alcance_del_actor(actor, usuario, plataforma)
    if is_admin(usuario):
        # Solo llega aquí un superadmin como actor: un admin de área ya
        # recibió 404 y no distingue la cuenta del superadmin.
        raise errores.acceso_por_defecto()
    if not usuario.is_active:
        raise errores.cuenta_inactiva()


def _validar_alcance_del_actor(actor, usuario, plataforma):
    """Antes de mirar a la cuenta destino: fuera de alcance → 404."""
    if actor is None:
        raise errores.fuera_de_alcance()
    if _mismo(actor, usuario):
        raise errores.operacion_propia(revocar=False)
    if not is_admin(actor) and not (can_manage_platform(plataforma, actor)
                                    and can_manage_user(usuario, actor)):
        raise errores.fuera_de_alcance()
    if plataforma.area_id not in {a.id for a in (usuario.areas or [])}:
        raise errores.fuera_de_alcance()  # P1


def validar_revocacion(actor, acceso):
    """SEC-AUTHZ-06/07/08; `actor=None` es el sistema (FNC-055)."""
    if actor is None:
        return
    if _mismo(actor, acceso.user):
        raise errores.operacion_propia()
    if is_admin(actor):
        return
    if (acceso.origin == ORIGEN_ADMIN_DE_AREA
            or not can_manage_platform(acceso.platform, actor)
            or not can_manage_user(acceso.user, actor)):
        raise errores.fuera_de_alcance()


# --------------------------------------------------------------------------- #
# Niveles (P5)
# --------------------------------------------------------------------------- #

def acceso_a_reemplazar(vigentes, nivel):
    """Acceso que el nuevo nivel reemplaza, o `None` si no hay.

    - `vigentes`: accesos vigentes del usuario en la plataforma.
    - Mismo nivel vigente (incluso saliendo) o uno superior → error.
    - Nivel inferior ocupante: se reemplaza si está `activo`.
    """
    mismo = next((a for a in vigentes if a.level == nivel), None)
    if mismo is not None:
        if mismo.status in ESTADOS_OCUPANTES:
            raise errores.nivel_vigente()
        raise errores.estado_invalido('Hay una revocación en curso de ese '
                                      'nivel.')
    ocupante = next((a for a in vigentes if a.status in ESTADOS_OCUPANTES),
                    None)
    if ocupante is None:
        return None
    if RANGO_NIVEL[ocupante.level] > RANGO_NIVEL[nivel]:
        raise errores.nivel_vigente()
    if ocupante.status != ESTADO_ACTIVO:
        raise errores.estado_invalido('El acceso actual aún no está activo.')
    return ocupante
