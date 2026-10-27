# Puertos de loopback del backend (Gunicorn) y del frontend (Next.js) (FNC-127).
#
# Se carga con `.` desde install.sh y preflight.sh. Precedencia:
# --web-port/--api-port > variable de entorno > .env del prefijo > por defecto.
# El bind es siempre 127.0.0.1: solo cambia el número.

WEB_PORT_POR_DEFECTO=3000
API_PORT_POR_DEFECTO=5001
# Sin puertos privilegiados (< 1024): los servicios no corren como root.
PUERTO_SERVICIO_MIN=1024
PUERTO_SERVICIO_MAX=65535

# ¿$1 es un puerto entero entre PUERTO_SERVICIO_MIN y PUERTO_SERVICIO_MAX?
puerto_servicio_valido() {
    [[ "$1" =~ ^[0-9]{1,5}$ ]] \
        && (( 10#$1 >= PUERTO_SERVICIO_MIN && 10#$1 <= PUERTO_SERVICIO_MAX ))
}

# Valor de la clave $2 en el .env $1, sin cargarlo (nunca `source`): solo esa
# línea, sin comillas ni espacios. Vacío si no está, si falta el fichero o si
# es un enlace (no se sigue). No imprime nada más del .env.
puerto_de_env() {
    local fichero=$1 clave=$2
    [[ -f "$fichero" && ! -L "$fichero" ]] || return 0
    { grep -E "^${clave}=" "$fichero" 2>/dev/null || true; } \
        | tail -n 1 | cut -d= -f2- | tr -d "\"' \r"
}

# Puerto resuelto: $1 (opción o entorno) si tiene valor; si no, la clave $3
# del .env $2; si no, $4. Falla (sin imprimir) si el resultado no es válido.
resolver_puerto() {
    local valor=$1
    [[ -n "$valor" ]] || valor="$(puerto_de_env "$2" "$3")"
    [[ -n "$valor" ]] || valor=$4
    puerto_servicio_valido "$valor" || return 1
    printf '%s' "$((10#$valor))"
}

# Filtro para render(): sustituye @WEB_PORT@ ($1) y @API_PORT@ ($2).
aplicar_puertos() {
    sed -e "s|@WEB_PORT@|$1|g" -e "s|@API_PORT@|$2|g"
}
