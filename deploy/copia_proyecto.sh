# shellcheck shell=bash
#
# Copia del proyecto al prefijo de instalación (FNC-125). La carga install.sh
# con `.`; no se ejecuta sola.
#
# Regla: el .env vive en el prefijo y el instalador nunca lo sobrescribe ni lo
# borra. Solo si el prefijo no tiene uno y el origen sí, se copia una vez.

# Lo que no viene del repo y puede existir en el prefijo: rsync --delete lo
# borraría. Un patrón excluido queda también protegido del borrado. Anclados
# a la raíz (/) para no excluir carpetas versionadas como docs/logs/.
EXCLUIDOS_COPIA=(
    # No portables: se recrean en el destino.
    'venv/' 'frontend/node_modules/' 'frontend/.next/' '__pycache__/' '*.pyc'
    '.git/' 'scratch/'
    # Locales del prefijo (ver .gitignore): configuración con secretos, BD
    # SQLite de Flask, respaldos, archivos subidos y registros.
    '/.env' '/.env.*' '/instance/' '/backups/' '/uploads/' '/storage/' '/logs/'
)

# copiar_proyecto ORIGEN PREFIJO
copiar_proyecto() {
    local src="$1" prefix="$2" patron
    local args=(-a --delete --include '/.env.example')
    for patron in "${EXCLUIDOS_COPIA[@]}"; do
        args+=(--exclude "$patron")
    done
    rsync "${args[@]}" "$src/" "$prefix/"

    # Primer despliegue con el .env junto al código clonado: se copia una sola
    # vez, solo legible por el dueño. Si el prefijo ya tiene uno, no se toca.
    # Un .env de origen que es enlace no se copia (podría apuntar a cualquier
    # archivo del sistema). `install` borra el destino antes de crearlo, así
    # que un enlace puesto en el prefijo entretanto no se sigue.
    if [[ ! -e "$prefix/.env" && ! -L "$prefix/.env" ]]; then
        if [[ -L "$src/.env" ]]; then
            printf 'ERROR: %s/.env es un enlace simbólico; no se copia\n' "$src" >&2
            return 1
        fi
        if [[ -f "$src/.env" ]]; then
            install -m 600 "$src/.env" "$prefix/.env"
            printf '    .env copiado del origen (el prefijo no tenía uno)\n'
        fi
    fi
}

# asegurar_env_prefijo PREFIJO USUARIO GRUPO PYTHON
# Deja <prefijo>/.env con dueño USUARIO:GRUPO y permisos 600, sin seguir
# enlaces. El prefijo es de la cuenta de servicio, que podría cambiar el .env
# por un enlace a /etc/shadow: un chown/chmod de root lo seguiría.
# - Comprobación previa con mensaje claro: enlace, no regular o ausente.
# - Cierre de la carrera entre comprobar y usar: Python abre el archivo con
#   O_NOFOLLOW (falla si el último componente es un enlace), comprueba con
#   fstat que el descriptor es un archivo regular con un solo enlace duro y
#   aplica fchown/fchmod a ESE descriptor. Lo que se cambie en la ruta después
#   de abrir no afecta. O_NONBLOCK evita quedarse colgado en un FIFO.
asegurar_env_prefijo() {
    local env="$1/.env" usuario="$2" grupo="$3" py="$4" uid gid
    if [[ -L "$env" ]]; then
        printf 'ERROR: %s es un enlace simbólico; debe ser un archivo regular. Sustituirlo por el archivo real.\n' "$env" >&2
        return 1
    fi
    if [[ ! -e "$env" ]]; then
        printf 'ERROR: %s no existe. Copiarlo y rellenar las credenciales antes de seguir.\n' "$env" >&2
        return 1
    fi
    if [[ ! -f "$env" ]]; then
        printf 'ERROR: %s no es un archivo regular.\n' "$env" >&2
        return 1
    fi
    uid="$(id -u "$usuario")" && gid="$(getent group "$grupo" | cut -d: -f3)"
    [[ "$uid" =~ ^[0-9]+$ && "$gid" =~ ^[0-9]+$ ]] || {
        printf 'ERROR: no se pudo resolver %s:%s\n' "$usuario" "$grupo" >&2
        return 1
    }
    "$py" -I - "$env" "$uid" "$gid" <<'PYEOF'
import os, stat, sys
ruta, uid, gid = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
try:
    fd = os.open(ruta, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
except OSError as e:
    sys.exit(f'ERROR: no se pudo abrir {ruta} sin seguir enlaces ({e.strerror})')
try:
    st = os.fstat(fd)
    if not stat.S_ISREG(st.st_mode):
        sys.exit(f'ERROR: {ruta} no es un archivo regular')
    if st.st_nlink != 1:
        sys.exit(f'ERROR: {ruta} tiene otro enlace duro; debe ser un archivo propio')
    os.fchown(fd, uid, gid)
    os.fchmod(fd, 0o600)
finally:
    os.close(fd)
PYEOF
}
