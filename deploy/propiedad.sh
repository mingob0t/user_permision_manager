# shellcheck shell=bash
#
# Lo que es de la cuenta de servicio (FNC-129, SEG-1). La carga install.sh
# con `.`; no se ejecuta sola.
#
# El código del prefijo es de root (install.sh lo comprueba antes de cargar
# nada). La cuenta solo es dueña de lo que escribe: los directorios de datos
# que existan en el prefijo y el directorio de registros. El .env lo trata
# env_seguro.sh (root:<grupo>, 640).

_prop_error() { printf 'ERROR: %s\n' "$1" >&2; return 1; }

# entregar_datos_a_servicio PREFIJO LOGDIR USUARIO GRUPO DIR...
# DIR son relativos al prefijo; solo se entregan los que existen. Un enlace
# detiene todo antes de cambiar nada. chown -R -h no sigue enlaces internos.
entregar_datos_a_servicio() {
    local prefijo="$1" logdir="$2" usuario="$3" grupo="$4" d ruta
    shift 4
    local entregar=()
    for d in "$@"; do
        ruta="$prefijo/$d"
        if [[ -L "$ruta" ]]; then
            _prop_error "$ruta es un enlace simbólico; debe ser un directorio real"
            return 1
        fi
        if [[ -d "$ruta" ]]; then entregar+=("$ruta"); fi
    done
    if [[ -L "$logdir" ]]; then
        _prop_error "$logdir es un enlace simbólico; debe ser un directorio real"
        return 1
    fi
    mkdir -p "$logdir"
    entregar+=("$logdir")
    for ruta in "${entregar[@]}"; do
        chown -R -h "$usuario:$grupo" "$ruta"
    done
}
