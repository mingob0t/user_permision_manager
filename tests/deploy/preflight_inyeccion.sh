#!/usr/bin/env bash
#
# Prueba de regresión de deploy/preflight.sh (FNC-067, hallazgo Media de
# auditor-seguridad): los valores de host y puerto del .env no deben poder
# ejecutar comandos, y REDIS_PASS con comillas vacías no cuenta como valor.
#
#   bash tests/deploy/preflight_inyeccion.sh
#
# Usa un .env SINTÉTICO en un directorio temporal; nunca lee el .env real.
# No es una prueba de pytest (preflight hace sondeos de red y tarda): se
# ejecuta a mano. Salida 0 si todo pasa.

set -uo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PREFLIGHT="$RAIZ/deploy/preflight.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fallos=0
pasa()  { printf '  PASA  %s\n' "$1"; }
falla() { printf '  FALLA %s\n' "$1"; fallos=$((fallos+1)); }

# preflight hace `tr -d ' '`, así que la carga usa ${IFS} en lugar de espacios.
carga() { printf 'localhost/1;touch${IFS}%s;#' "$1"; }

correr_preflight() {
    # $1: directorio con el .env sintético. Sin proxy para no depender de él.
    (cd "$1" && env -u PROXY_URL -u https_proxy -u HTTPS_PROXY -u http_proxy \
        -u HTTP_PROXY bash "$PREFLIGHT" 2>&1)
}

# --- 0. Control: la carga sí ejecuta con el patrón anterior -----------------
marca0="$TMP/control"
h="$(carga "$marca0")"
timeout 5 bash -c "</dev/tcp/${h}/1" 2>/dev/null
if [[ -e "$marca0" ]]; then
    pasa "control: con interpolación en bash -c la carga crea el archivo"
else
    falla "control: la carga no ejecutó con el patrón vulnerable (prueba inválida)"
fi

# --- 1. DB_HOST y REDIS_HOST con carga ---------------------------------------
d1="$TMP/carga"; mkdir -p "$d1"
marca_db="$TMP/pwned_db"; marca_redis="$TMP/pwned_redis"
{
    printf 'DB_HOST=%s\n' "$(carga "$marca_db")"
    printf 'DB_PORT=3306\n'
    printf 'REDIS_HOST=%s\n' "$(carga "$marca_redis")"
    printf 'REDIS_PORT=6379\n'
    printf 'REDIS_PASS=sintetica\n'
    printf 'SECRET_KEY=sintetica\n'
} > "$d1/.env"
salida1="$(correr_preflight "$d1")"
[[ ! -e "$marca_db" ]] && pasa "DB_HOST con carga no crea el archivo" \
                       || falla "DB_HOST con carga creó $marca_db"
[[ ! -e "$marca_redis" ]] && pasa "REDIS_HOST con carga no crea el archivo" \
                          || falla "REDIS_HOST con carga creó $marca_redis"
grep -q "FALTA DB_HOST/DB_PORT con formato no válido" <<< "$salida1" \
    && pasa "DB_HOST no válido → FALTA" || falla "DB_HOST no válido sin FALTA"
grep -q "FALTA REDIS_HOST/REDIS_PORT con formato no válido" <<< "$salida1" \
    && pasa "REDIS_HOST no válido → FALTA" || falla "REDIS_HOST no válido sin FALTA"

# --- 2. Puertos con carga o fuera de rango -----------------------------------
d2="$TMP/puertos"; mkdir -p "$d2"
marca_puerto="$TMP/pwned_port"
{
    printf 'DB_HOST=localhost\n'
    printf 'DB_PORT=1;touch${IFS}%s\n' "$marca_puerto"
    printf 'REDIS_HOST=localhost\n'
    printf 'REDIS_PORT=70000\n'
    printf 'REDIS_PASS=sintetica\n'
    printf 'SECRET_KEY=sintetica\n'
} > "$d2/.env"
salida2="$(correr_preflight "$d2")"
[[ ! -e "$marca_puerto" ]] && pasa "DB_PORT con carga no crea el archivo" \
                           || falla "DB_PORT con carga creó $marca_puerto"
grep -q "FALTA DB_HOST/DB_PORT con formato no válido" <<< "$salida2" \
    && pasa "DB_PORT no válido → FALTA" || falla "DB_PORT no válido sin FALTA"
grep -q "FALTA REDIS_HOST/REDIS_PORT con formato no válido" <<< "$salida2" \
    && pasa "REDIS_PORT 70000 → FALTA" || falla "REDIS_PORT fuera de rango sin FALTA"

# --- 3. REDIS_PASS vacía con comillas ----------------------------------------
for valor in '""' "''" ''; do
    d3="$TMP/pass_$RANDOM"; mkdir -p "$d3"
    printf 'REDIS_HOST=localhost\nREDIS_PORT=1\nREDIS_PASS=%s\nSECRET_KEY=s\n' \
        "$valor" > "$d3/.env"
    grep -q "FALTA REDIS_PASS sin definir" <<< "$(correr_preflight "$d3")" \
        && pasa "REDIS_PASS=${valor} → FALTA" \
        || falla "REDIS_PASS=${valor} aceptada como valor"
done
d4="$TMP/pass_ok"; mkdir -p "$d4"
printf 'REDIS_HOST=localhost\nREDIS_PORT=1\nREDIS_PASS="sintetica"\nSECRET_KEY=s\n' \
    > "$d4/.env"
grep -q "OK    REDIS_PASS definida" <<< "$(correr_preflight "$d4")" \
    && pasa 'REDIS_PASS="sintetica" → OK' || falla 'REDIS_PASS entre comillas rechazada'

printf '\nFallos: %d\n' "$fallos"
(( fallos == 0 ))
