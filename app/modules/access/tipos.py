"""Valores enumerados de los accesos otorgados (contrato `accesos.md` v1)."""
from app.modules.platforms.tipos import NIVEL_ADMIN, NIVEL_USUARIO

# Estado del acceso.
ESTADO_EN_PROCESO = 'en_proceso'
ESTADO_ACTIVO = 'activo'
ESTADO_FALLIDO = 'fallido'
ESTADO_REVOCANDO = 'revocando'
ESTADO_REVOCADO = 'revocado'
ESTADO_FALLO_REVOCACION = 'fallo_revocacion'
ESTADOS = (ESTADO_EN_PROCESO, ESTADO_ACTIVO, ESTADO_FALLIDO, ESTADO_REVOCANDO,
           ESTADO_REVOCADO, ESTADO_FALLO_REVOCACION)
# Vigente: todo menos `revocado` (contrato).
ESTADOS_VIGENTES = (ESTADO_EN_PROCESO, ESTADO_ACTIVO, ESTADO_FALLIDO,
                    ESTADO_REVOCANDO, ESTADO_FALLO_REVOCACION)
# Ocupa el nivel de la plataforma (P5): los que no están saliendo.
ESTADOS_OCUPANTES = (ESTADO_EN_PROCESO, ESTADO_ACTIVO, ESTADO_FALLIDO)

# Nivel (P5: uno por usuario y plataforma; subir reemplaza).
NIVELES = (NIVEL_USUARIO, NIVEL_ADMIN)
# Orden de los niveles: solo se sube (solicitudes.md, `requestable_levels`).
RANGO_NIVEL = {NIVEL_USUARIO: 1, NIVEL_ADMIN: 2}

# Origen (P4: sin `heredado`; los accesos de NEXUS se descartan).
ORIGEN_SOLICITUD = 'solicitud'
ORIGEN_ADMIN_DE_AREA = 'admin_de_area'
ORIGENES = (ORIGEN_SOLICITUD, ORIGEN_ADMIN_DE_AREA)

# Motivo que el sistema pone al acceso reemplazado al subir de nivel.
MOTIVO_REEMPLAZO = 'reemplazado_por_nivel_superior'
# Motivo del acceso automático que el sistema revoca porque la cuenta ya no
# administra el área de la plataforma (FNC-055, P6).
MOTIVO_RETIRO_ADMIN = 'ya_no_administra_el_area'

# Valor de las columnas de unicidad cuando el acceso ocupa su lugar
# (NULL cuando no: MySQL y SQLite admiten varios NULL en un índice único).
OCUPA = 1

# Largos de columna.
LARGO_NIVEL = 10
LARGO_ORIGEN = 20
LARGO_ESTADO = 20
LARGO_MOTIVO = 500
