"""Acceso automático de los admins a las plataformas de sus áreas (FNC-055).

P6 (dueño, 2026-10-14): todos los admins del área reciben un acceso origen
`admin_de_area`, nivel `usuario`, que otorga el sistema; el superadmin no
(acceso por defecto, sin grupos LDAP); al quitarle el área a un admin se
revocan sus accesos automáticos de esa área.

Uso desde otros módulos, **dentro de su transacción** (no hace `commit`):
- `sincronizar_plataforma(plataforma)`: alta, cambio de área o grupos.
- `sincronizar_cuenta(cuenta, areas_nuevas)`: áreas administradas o rol.
- `revocar_si_ya_no_administra(acceso)`: manejador del otorgar confirmado.

Reutiliza `services.otorgar`/`services.revocar` (FNC-054): las reglas, la
cola y la auditoría ("sistema dio permisos de acceso a admin X") son esas.

Decisiones del orquestador (pendientes de validar en la prueba de concepto):
- Solo se otorga ante un evento (alta, área agregada, cambio de área o de
  grupos): una revocación manual del superadmin no se deshace sola.
- Solo se revoca un acceso `activo`; uno `en_proceso` se revoca al
  confirmarse (`revocar_si_ya_no_administra`). Uno `fallido` no da acceso y,
  si se reintenta (FNC-062), se revoca al confirmarse.
- Si la cuenta ya tiene un acceso vigente en la plataforma (cualquier nivel u
  origen, o una revocación en curso de nivel `usuario`), no se otorga otro.
- Plataformas `ldap` sin grupo de nivel `usuario` (heredadas) no reciben
  accesos: el trabajo fallaría y el acceso `fallido` bloquearía completar los
  grupos. Al completarlos se sincroniza.
- Un admin inactivo no recibe accesos automáticos.
"""
from app import db
from app.authz import is_area_admin, managed_area_ids
from app.modules.access import services
from app.modules.access.consultas import vigentes_de
from app.modules.access.models import PlatformAccessGrant
from app.modules.access.tipos import (ESTADO_ACTIVO, ESTADOS_OCUPANTES,
                                      ESTADOS_VIGENTES, MOTIVO_RETIRO_ADMIN,
                                      ORIGEN_ADMIN_DE_AREA)
from app.modules.core.models import Area, Platform
from app.modules.platforms.tipos import (CAMPOS_DN, NIVEL_USUARIO,
                                         TIPO_LDAP, TIPOS_INTEGRACION)

NIVEL_AUTOMATICO = NIVEL_USUARIO  # P6


def administra(cuenta, plataforma):
    """`True` si la cuenta activa administra el área de la plataforma."""
    return (cuenta is not None and plataforma is not None
            and bool(cuenta.is_active) and is_area_admin(cuenta)
            and plataforma.area_id in managed_area_ids(cuenta))


def aprovisionable(plataforma):
    """Conector, o `ldap` con grupo de nivel `usuario`."""
    if plataforma.integration_type == TIPO_LDAP:
        return bool(getattr(plataforma, CAMPOS_DN[NIVEL_AUTOMATICO]))
    return plataforma.integration_type in TIPOS_INTEGRACION


def _automaticos_vigentes(**filtros):
    return (PlatformAccessGrant.query
            .filter_by(origin=ORIGEN_ADMIN_DE_AREA, **filtros)
            .filter(PlatformAccessGrant.status.in_(ESTADOS_VIGENTES))
            .order_by(PlatformAccessGrant.id).all())


# --------------------------------------------------------------------------- #
# Una cuenta en una plataforma
# --------------------------------------------------------------------------- #

def otorgar_si_falta(cuenta, plataforma):
    """Otorga el acceso automático si corresponde y no tiene ninguno."""
    if not (administra(cuenta, plataforma) and aprovisionable(plataforma)):
        return None
    vigentes = vigentes_de(cuenta.id, plataforma.id)
    if any(a.status in ESTADOS_OCUPANTES or a.level == NIVEL_AUTOMATICO
           for a in vigentes):
        return None
    return services.otorgar(cuenta, plataforma, NIVEL_AUTOMATICO,
                            ORIGEN_ADMIN_DE_AREA)


def revocar_si_ya_no_administra(acceso):
    """Revoca un acceso automático `activo` de quien ya no administra el área.

    También lo usa el manejador del otorgar confirmado (`manejadores.py`).
    """
    if (acceso is None or acceso.origin != ORIGEN_ADMIN_DE_AREA
            or acceso.status != ESTADO_ACTIVO
            or administra(acceso.user, acceso.platform)):
        return None
    return services.revocar(acceso, motivo=MOTIVO_RETIRO_ADMIN)


# --------------------------------------------------------------------------- #
# Puntos de entrada
# --------------------------------------------------------------------------- #

def sincronizar_plataforma(plataforma):
    """Alta, cambio de área o de grupos: revoca a quien ya no administra su
    área y otorga a los admins de su área que no tienen acceso."""
    for acceso in _automaticos_vigentes(platform_id=plataforma.id):
        revocar_si_ya_no_administra(acceso)
    # Por id: la relación `area` no se refresca si el llamador cambió `area_id`.
    area = db.session.get(Area, plataforma.area_id)
    admins = sorted(getattr(area, 'admins', None) or [],
                    key=lambda cuenta: cuenta.id)
    for cuenta in admins:
        otorgar_si_falta(cuenta, plataforma)


def sincronizar_cuenta(cuenta, areas_nuevas=()):
    """Áreas administradas o rol de una cuenta: revoca sus automáticos de
    áreas que ya no administra y otorga en las plataformas de `areas_nuevas`."""
    for acceso in _automaticos_vigentes(user_id=cuenta.id):
        revocar_si_ya_no_administra(acceso)
    ids = [a.id for a in areas_nuevas or ()]
    if not ids:
        return
    plataformas = (Platform.query.filter(Platform.area_id.in_(ids))
                   .order_by(Platform.id).all())
    for plataforma in plataformas:
        otorgar_si_falta(cuenta, plataforma)
