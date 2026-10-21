"""Valores enumerados de los conectores (contrato `conectores-y-ejecuciones.md`)."""

# Tipo de conector. `noop` solo en dev y pruebas; `api`, `ssh` y `bd` los
# registran FNC-051 a FNC-053 (P9). Un tipo sin registrar no se acepta ni se
# ejecuta.
TIPO_NOOP = 'noop'
TIPO_API = 'api'
TIPO_SSH = 'ssh'
TIPO_BD = 'bd'

# Estado de la credencial (`credential_status`). Cambiar host o referencia la
# deja sin verificar (SEC-CON-07).
CREDENCIAL_OK = 'ok'
CREDENCIAL_NO_ENCONTRADA = 'no_encontrada'
CREDENCIAL_SIN_VERIFICAR = 'sin_verificar'
ESTADOS_CREDENCIAL = (CREDENCIAL_OK, CREDENCIAL_NO_ENCONTRADA,
                      CREDENCIAL_SIN_VERIFICAR)

# Largos de columna de `platform_connectors`.
LARGO_TIPO = 20
LARGO_HOST = 253  # nombre de host completo (RFC 1035)
LARGO_REFERENCIA = 200
LARGO_ESTADO_CREDENCIAL = 20

PUERTO_MINIMO = 1
PUERTO_MAXIMO = 65535
