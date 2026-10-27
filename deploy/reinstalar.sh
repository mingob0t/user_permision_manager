# shellcheck shell=bash
#
# Reinstalación limpia con --force / --reinstall (FNC-129). La carga
# install.sh con `.`; no se ejecuta sola.
#
# Quita SOLO lo de la instalación <nombre>, después de mostrar la lista y de
# que una persona escriba el nombre en una terminal:
#   - unidades <nombre>-backend, -frontend y -worker (se detienen, deshabilitan
#     y se borran sus archivos; luego daemon-reload)
#   - <nginx>/<nombre>.conf
#   - en el prefijo: venv/, frontend/node_modules/ y frontend/.next/
#   - el directorio de registros
# Nunca toca el .env, el código, .git, la BD, Redis, la cuenta de servicio ni
# los datos locales (instance/, backups/, uploads/, storage/). Cada ruta se
# valida antes de borrar: nada vacío, relativo, con '..' ni '/'.

# shellcheck source=deploy/nombre_despliegue.sh
. "$(dirname "${BASH_SOURCE[0]}")/nombre_despliegue.sh"

# Lo que se regenera en el prefijo (relativo a él).
GENERADOS_PREFIJO=(venv frontend/node_modules frontend/.next)

_reinst_error() { printf 'ERROR: %s\n' "$1" >&2; return 1; }

# ¿Ruta absoluta, normalizada y distinta de '/'?
_ruta_segura() {
    local r="$1"
    [[ -n "$r" && "$r" == /* && "$r" != / && "$r" != */ && "$r" != *//* ]] \
        && ! [[ "$r" =~ (^|/)\.\.?(/|$) ]]
}

# ¿La ruta existente no pasa por ningún enlace (ella incluida)?
_sin_enlaces() {
    [[ "$(realpath -- "$1" 2>/dev/null)" == "$1" ]]
}

# reinstalar_limpio NOMBRE PREFIJO LOGDIR SYSTEMD_DIR NGINX_DIR
reinstalar_limpio() {
    local nombre="$1" prefijo="$2" logdir="$3" systemd_dir="$4" nginx_dir="$5"
    local u rel ruta respuesta
    local unidades=() archivos=() directorios=()

    # --- Validación: si algo no es lo esperado, no se borra nada -------------
    nombre_despliegue_valido "$nombre" \
        || { _reinst_error "nombre de instalación no válido: '$nombre'"; return 1; }
    _ruta_segura "$prefijo" && [[ -d "$prefijo" ]] && _sin_enlaces "$prefijo" \
        && [[ -f "$prefijo/run.py" ]] \
        || { _reinst_error "el prefijo '$prefijo' no es la carpeta del código"; return 1; }
    _ruta_segura "$logdir" && [[ "${logdir##*/}" == "$nombre" ]] \
        || { _reinst_error "con --force, el directorio de registros debe terminar en /$nombre (es '$logdir')"; return 1; }
    [[ "$logdir" != "$prefijo" && "$prefijo/" != "$logdir/"* && "$logdir/" != "$prefijo/"* ]] \
        || { _reinst_error "el directorio de registros '$logdir' se cruza con el prefijo"; return 1; }
    if [[ -e "$logdir" || -L "$logdir" ]]; then
        _sin_enlaces "$logdir" \
            || { _reinst_error "'$logdir' es o pasa por un enlace; borrarlo a mano"; return 1; }
    fi
    for ruta in "$systemd_dir" "$nginx_dir"; do
        _ruta_segura "$ruta" && [[ -d "$ruta" ]] \
            || { _reinst_error "directorio del sistema inesperado: '$ruta'"; return 1; }
    done
    if [[ -e "$prefijo/frontend" ]]; then
        _sin_enlaces "$prefijo/frontend" \
            || { _reinst_error "'$prefijo/frontend' es un enlace; no se limpia"; return 1; }
    fi

    # --- Lista exacta ---------------------------------------------------------
    for u in backend frontend worker; do
        unidades+=("${nombre}-${u}")
        ruta="$systemd_dir/${nombre}-${u}.service"
        if [[ -e "$ruta" || -L "$ruta" ]]; then archivos+=("$ruta"); fi
    done
    ruta="$nginx_dir/${nombre}.conf"
    if [[ -e "$ruta" || -L "$ruta" ]]; then archivos+=("$ruta"); fi
    for rel in "${GENERADOS_PREFIJO[@]}"; do
        ruta="$prefijo/$rel"
        if [[ -e "$ruta" || -L "$ruta" ]]; then directorios+=("$ruta"); fi
    done
    if [[ -e "$logdir" ]]; then directorios+=("$logdir"); fi

    printf '\n--force: se limpiará la instalación "%s".\n' "$nombre"
    printf '  Detener y deshabilitar:\n'
    printf '    %s\n' "${unidades[@]}"
    if (( ${#archivos[@]} + ${#directorios[@]} )); then
        printf '  Borrar:\n'
        if (( ${#archivos[@]} )); then printf '    %s\n' "${archivos[@]}"; fi
        if (( ${#directorios[@]} )); then printf '    %s/\n' "${directorios[@]}"; fi
    fi
    printf '  No se toca: .env, código, .git, base de datos, Redis, cuenta de servicio,\n'
    printf '  instance/, backups/, uploads/ ni storage/.\n\n'

    # --- Confirmación ---------------------------------------------------------
    [[ -t 0 ]] \
        || { _reinst_error "--force necesita una terminal para confirmar; no se borró nada"; return 1; }
    if ! IFS= read -r -p "Escribe el nombre de la instalación ($nombre) para confirmar: " respuesta; then
        respuesta=""
    fi
    [[ "$respuesta" == "$nombre" ]] \
        || { _reinst_error "la confirmación no coincide; no se borró nada"; return 1; }

    # --- Limpieza -------------------------------------------------------------
    for u in "${unidades[@]}"; do
        systemctl disable --now "${u}.service" >/dev/null 2>&1 || true
    done
    # rm sin -r para archivos; -- y rutas ya validadas. Un enlace se quita a
    # sí mismo, nunca su destino (rm no sigue enlaces).
    if (( ${#archivos[@]} )); then rm -f -- "${archivos[@]}"; fi
    systemctl daemon-reload
    for u in "${unidades[@]}"; do
        systemctl reset-failed "${u}.service" >/dev/null 2>&1 || true
    done
    if (( ${#directorios[@]} )); then rm -rf -- "${directorios[@]}"; fi
    printf '    instalación anterior de "%s" limpiada\n' "$nombre"
}
