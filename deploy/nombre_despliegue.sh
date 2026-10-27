# shellcheck shell=bash
#
# Nombre del despliegue (FNC-129). Lo cargan install.sh y preflight.sh con `.`.
#
# El nombre acaba en rutas, unidades systemd y upstreams de nginx: se restringe
# a lo que es válido en todos esos sitios. Por defecto es el de la carpeta
# donde se clonó el código (antes, `nexus`).

NOMBRE_DESPLIEGUE_REGEX='^[a-z][a-z0-9_-]{0,31}$'

# nombre_despliegue_valido NOMBRE
nombre_despliegue_valido() {
    [[ "$1" =~ $NOMBRE_DESPLIEGUE_REGEX ]]
}

# nombre_por_defecto RAIZ: último componente de la carpeta del código.
nombre_por_defecto() {
    local raiz="${1%/}"
    printf '%s' "${raiz##*/}"
}
