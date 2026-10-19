"""Valores enumerados de una plataforma (contrato `plataformas-integracion.md`)."""

# Tipo de integración: grupos del directorio o conector (FNC-050).
TIPO_LDAP = 'ldap'
TIPO_CONECTOR = 'conector'
TIPOS_INTEGRACION = (TIPO_LDAP, TIPO_CONECTOR)

# Niveles de acceso: un nivel por plataforma (P5).
NIVEL_USUARIO = 'usuario'
NIVEL_ADMIN = 'admin'

# Resultado de comprobar los grupos en el directorio.
GRUPOS_OK = 'ok'
GRUPOS_NO_EXISTE = 'no_existe'
GRUPOS_SIN_VERIFICAR = 'sin_verificar'

# Campo del DN de grupo de cada nivel.
CAMPO_DN_USUARIO = 'ldap_group_user_dn'
CAMPO_DN_ADMIN = 'ldap_group_admin_dn'
CAMPOS_DN = {NIVEL_USUARIO: CAMPO_DN_USUARIO, NIVEL_ADMIN: CAMPO_DN_ADMIN}

# Largo de las columnas nuevas de `platforms`.
LARGO_TIPO = 20
LARGO_DN = 512
LARGO_ESTADO_GRUPOS = 20
