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
    if [[ ! -e "$prefix/.env" && ! -L "$prefix/.env" && -f "$src/.env" ]]; then
        install -m 600 "$src/.env" "$prefix/.env"
        printf '    .env copiado del origen (el prefijo no tenía uno)\n'
    fi
}
