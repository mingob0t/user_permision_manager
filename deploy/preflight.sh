#!/usr/bin/env bash
#
# Evaluación previa a la instalación de Nexus en Rocky/RHEL 8 o 9.
#
# No instala ni modifica nada: solo informa de qué hay, qué falta y qué
# decisiones habrá que tomar. Ejecutarlo antes de install.sh.
#
#   sudo ./deploy/preflight.sh
#
# Salida: 0 si se puede instalar, 1 si hay algo que resolver antes.

set -uo pipefail

# --- Requisitos del proyecto -------------------------------------------------
# El proyecto funciona con Python 3.11 o superior; no exige 3.12. Se usa el
# intérprete ya instalado y solo se instala uno si no hay ninguno válido.
PY_MIN_MINOR=11
PY_BIN=""                      # se resuelve más abajo
NODE_MAJOR="22"                # Node LTS que se instala
# Mínimo de Node: el mismo rango que "engines" de frontend/package.json
# (^22.13.0 || >=24.0.0). Lo fijan vitest 4 y jsdom 29; Next 15 pide menos.
# Node 23 (impar, sin LTS) queda fuera porque vitest no lo admite.
NODE_MIN_MINOR=13              # menor mínima dentro de NODE_MAJOR
NODE_NEXT_MAJOR=24             # primera mayor posterior que se acepta completa
NODE_RANGO="^${NODE_MAJOR}.${NODE_MIN_MINOR}.0 || >=${NODE_NEXT_MAJOR}.0.0"
MIN_DISK_MB=2048               # node_modules + venv + build
MIN_RAM_MB=1024                # `next build` es lo que más consume
# Puertos de loopback (FNC-127): entorno > .env > por defecto (3000/5001),
# igual que install.sh; se resuelven en la sección de puertos.
API_PORT="${API_PORT:-}"
WEB_PORT="${WEB_PORT:-}"
# Carpeta del código: install.sh instala en sitio, sobre ella (FNC-129).
RAIZ_CODIGO="$(realpath "$(dirname "${BASH_SOURCE[0]}")/..")"
# Nombre del despliegue (nombre_despliegue.sh): define las unidades systemd y
# las rutas que se comprobarán. Debe coincidir con el --name del instalador;
# por defecto, el de la carpeta, como en install.sh.
# shellcheck source=deploy/nombre_despliegue.sh
. "$(dirname "${BASH_SOURCE[0]}")/nombre_despliegue.sh"
APP_NAME="${APP_NAME:-$(nombre_por_defecto "$RAIZ_CODIGO")}"

problems=0
warnings=0

# Revisión de VAULTWARDEN_* y del bind LDAP (FNC-068).
# shellcheck source=deploy/secretos.sh
. "$(dirname "${BASH_SOURCE[0]}")/secretos.sh"
# Servicio systemd de la BD local (FNC-125).
# shellcheck source=deploy/servicio_bd.sh
. "$(dirname "${BASH_SOURCE[0]}")/servicio_bd.sh"
# Puertos de backend y frontend (FNC-127).
# shellcheck source=deploy/puertos.sh
. "$(dirname "${BASH_SOURCE[0]}")/puertos.sh"

# Color solo en terminal: al redirigir a un fichero o a un pipe, texto plano.
if [[ -t 1 ]]; then
    c_ok=$'\033[32m'; c_warn=$'\033[33m'; c_bad=$'\033[31m'
    c_bold=$'\033[1m'; c_off=$'\033[0m'
else
    c_ok=''; c_warn=''; c_bad=''; c_bold=''; c_off=''
fi
ok()   { printf "  %sOK%s    %s\n" "$c_ok" "$c_off" "$1"; }
warn() { printf "  %sAVISO%s %s\n" "$c_warn" "$c_off" "$1"; warnings=$((warnings+1)); }
bad()  { printf "  %sFALTA%s %s\n" "$c_bad" "$c_off" "$1"; problems=$((problems+1)); }

# ¿La versión de Node ($1, salida de `node --version`) cumple NODE_RANGO?
node_cumple_minimo() {
    local v=${1#v} mayor menor
    mayor=${v%%.*}; v=${v#*.}; menor=${v%%.*}
    [[ "$mayor" =~ ^[0-9]+$ && "$menor" =~ ^[0-9]+$ ]] || return 1
    (( 10#$mayor == NODE_MAJOR && 10#$menor >= NODE_MIN_MINOR )) \
        || (( 10#$mayor >= NODE_NEXT_MAJOR ))
}
head2(){ printf "\n%s%s%s\n" "$c_bold" "$1" "$c_off"; }

# --- 1. Sistema operativo ----------------------------------------------------
head2 "Sistema"

if [[ -r /etc/os-release ]]; then
    . /etc/os-release
    printf "  %s\n" "${PRETTY_NAME:-desconocido}"
    major="${VERSION_ID%%.*}"
    case "${ID}:${major}" in
        rocky:8|rhel:8|centos:8|almalinux:8)
            ok "distribución compatible (familia RHEL 8)" ;;
        rocky:9|rhel:9|almalinux:9)
            ok "distribución compatible (familia RHEL 9)"
            printf "  en el9, Python 3.12 y Node vienen de repos distintos (ver deploy/README.md)\n" ;;
        *)
            warn "distribución no probada; el script asume dnf y familia RHEL" ;;
    esac
else
    bad "no se pudo identificar la distribución (/etc/os-release ausente)"
fi

printf "  arquitectura: %s\n" "$(uname -m)"
[[ "$(uname -m)" == "x86_64" || "$(uname -m)" == "aarch64" ]] \
    || warn "arquitectura poco habitual; Node puede no tener binario oficial"

# --- 2. Privilegios ----------------------------------------------------------
head2 "Privilegios"
if [[ $EUID -eq 0 ]]; then
    ok "ejecutando como root"
elif sudo -n true 2>/dev/null; then
    ok "sudo disponible sin contraseña"
else
    warn "hará falta contraseña de sudo durante la instalación"
fi

# --- 3. Recursos -------------------------------------------------------------
head2 "Recursos"

disk_mb=$(df -Pm . | awk 'NR==2 {print $4}')
if (( disk_mb >= MIN_DISK_MB )); then
    ok "espacio libre: ${disk_mb} MB"
else
    bad "espacio libre: ${disk_mb} MB (se necesitan ${MIN_DISK_MB} MB para venv, node_modules y el build)"
fi

ram_mb=$(free -m | awk '/^Mem:/ {print $2}')
if (( ram_mb >= MIN_RAM_MB )); then
    ok "memoria: ${ram_mb} MB"
else
    warn "memoria: ${ram_mb} MB — 'next build' puede quedarse sin memoria; considera swap"
fi

# --- 4. Python ---------------------------------------------------------------
head2 "Python"

# Se aprovecha el intérprete que ya haya, de mayor a menor versión, para no
# acumular instalaciones de Python en el servidor.
# Rutas del sistema explícitas: si un venv está activo, `command -v` daría su
# intérprete y el venv se crearía anidado sobre otro venv.
for candidate in /usr/bin/python3.13 /usr/bin/python3.12 /usr/bin/python3.11 \
                 /usr/local/bin/python3.12 /usr/local/bin/python3.11 /usr/bin/python3; do
    [[ -x "$candidate" ]] || continue
    minor=$("$candidate" -c 'import sys; print(sys.version_info[1])' 2>/dev/null) || continue
    if [[ -n "$minor" ]] && (( minor >= PY_MIN_MINOR )); then
        PY_BIN="$candidate"
        break
    fi
done

if [[ -n "$PY_BIN" ]]; then
    ok "$($PY_BIN --version) en $PY_BIN"
    "$PY_BIN" -c "import venv" >/dev/null 2>&1 \
        && ok "módulo venv disponible" \
        || bad "falta el módulo venv (instalar el paquete -devel del intérprete)"
    printf "  se usará este intérprete; no hace falta instalar otro\n"
else
    sys_ver=$(python3 --version 2>&1 || echo 'ausente')
    bad "no hay Python >= 3.${PY_MIN_MINOR} (el del sistema es ${sys_ver})"
    printf "  opciones en Rocky/RHEL 8: dnf module enable python311  (o python312)\n"
    printf "  en Rocky/RHEL 9: dnf install python3.12 python3.12-devel\n"
fi

# --- 5. Node -----------------------------------------------------------------
head2 "Node.js"

if command -v node >/dev/null 2>&1; then
    node_v=$(node --version)
    if node_cumple_minimo "$node_v"; then
        ok "Node ${node_v} (el proyecto pide ${NODE_RANGO})"
    else
        bad "Node ${node_v} no cumple el mínimo del proyecto (${NODE_RANGO}); instalar Node ${NODE_MAJOR} LTS"
    fi
    command -v npm >/dev/null 2>&1 && ok "npm $(npm --version)" || bad "npm no está instalado"
else
    bad "Node.js no está instalado (se instalará el módulo nodejs:${NODE_MAJOR})"
    dnf module list nodejs 2>/dev/null | grep -q "^nodejs *${NODE_MAJOR}" \
        && ok "el módulo nodejs:${NODE_MAJOR} está disponible" \
        || warn "el módulo nodejs:${NODE_MAJOR} no aparece; se usará el repo de NodeSource"
fi

# --- 6. Cabeceras de compilación --------------------------------------------
head2 "Dependencias de compilación"
# cryptography, cffi, bcrypt y PyNaCl compilan si no hay rueda binaria.
# PyMySQL y ldap3 son puro Python (FNC-125): sin mariadb-devel ni openldap-devel.
for pkg in gcc openssl-devel libffi-devel; do
    rpm -q "$pkg" >/dev/null 2>&1 && ok "$pkg" || warn "$pkg ausente (lo instala el script)"
done

# --- 6b. Salida a Internet ---------------------------------------------------
head2 "Salida a Internet"

# Se acepta el proxy por variable de entorno o por --proxy en el instalador.
PROXY_URL="${PROXY_URL:-${https_proxy:-${HTTPS_PROXY:-${http_proxy:-${HTTP_PROXY:-}}}}}"

if [[ -n "$PROXY_URL" ]]; then
    # No se imprime la URL completa: puede llevar usuario y contraseña.
    printf "  proxy configurado: %s\n" "$(sed -E 's#(://).*@#\1***@#' <<< "$PROXY_URL")"
    ok "se usará ese proxy para dnf, pip y npm"
    [[ -n "${no_proxy:-${NO_PROXY:-}}" ]] \
        && printf "  no_proxy: %s\n" "${no_proxy:-$NO_PROXY}" \
        || warn "no_proxy sin definir: conviene excluir localhost y la red interna"
else
    printf "  sin proxy definido (conexión directa)\n"
fi

probe_url() {
    # --proxy vacío fuerza conexión directa cuando no hay proxy configurado.
    if [[ -n "$PROXY_URL" ]]; then
        curl -fsS --max-time 12 --proxy "$PROXY_URL" -o /dev/null "$1" 2>/dev/null
    else
        curl -fsS --max-time 12 -o /dev/null "$1" 2>/dev/null
    fi
}

if ! command -v curl >/dev/null 2>&1; then
    warn "curl no está instalado; no se puede comprobar la salida a Internet"
else
    reachable=0
    for target in "https://registry.npmjs.org/-/ping" "https://pypi.org/simple/" ; do
        if probe_url "$target"; then
            ok "alcanzable: ${target%%/-/*}"
            reachable=$((reachable+1))
        else
            bad "no se alcanza $target"
        fi
    done
    if (( reachable == 0 )); then
        printf "  sin salida no se pueden descargar dependencias.\n"
        printf "  si hay proxy corporativo: PROXY_URL=http://proxy:3128 ./deploy/preflight.sh\n"
    fi
fi

# dnf lee su propio proxy de /etc/dnf/dnf.conf, no del entorno.
if [[ -f /etc/dnf/dnf.conf ]]; then
    if grep -qE '^\s*proxy\s*=' /etc/dnf/dnf.conf; then
        ok "dnf ya tiene proxy en /etc/dnf/dnf.conf"
    elif [[ -n "$PROXY_URL" ]]; then
        warn "dnf no tiene proxy configurado; el instalador lo añadirá a dnf.conf"
    fi
fi

# npm lo lee de su propia configuración.
if command -v npm >/dev/null 2>&1; then
    npm_proxy="$(npm config get https-proxy 2>/dev/null)"
    if [[ -n "$npm_proxy" && "$npm_proxy" != "null" ]]; then
        ok "npm ya tiene proxy configurado"
    elif [[ -n "$PROXY_URL" ]]; then
        warn "npm no tiene proxy; el instalador lo configurará"
    fi
fi

# --- 7. Servicios de datos ---------------------------------------------------
head2 "Base de datos y Redis"

if command -v mysql >/dev/null 2>&1; then
    ok "cliente mysql presente"
else
    warn "cliente mysql ausente; útil para respaldar la base antes de migrar (el instalador intenta instalarlo: paquete mariadb o mysql según el servidor)"
fi

# Los valores del .env no son de confianza (el script corre como root): host y
# puerto se validan con lista blanca y se pasan como argumentos posicionales,
# nunca interpolados dentro de `bash -c` (inyección de comandos, FNC-067).
host_valido()   { [[ "$1" =~ ^[A-Za-z0-9.-]+$ ]]; }
puerto_valido() { [[ "$1" =~ ^[0-9]{1,5}$ ]] && (( 10#$1 >= 1 && 10#$1 <= 65535 )); }
probe_tcp()     { timeout 5 bash -c '</dev/tcp/$1/$2' _ "$1" "$2" 2>/dev/null; }

if [[ -f .env ]]; then
    ok ".env presente"
    db_host=$(grep -E '^DB_HOST=' .env | cut -d= -f2- | tr -d '"'"'"' ')
    db_port=$(grep -E '^DB_PORT=' .env | cut -d= -f2- | tr -d '"'"'"' ')
    db_name=$(grep -E '^DB_NAME=' .env | cut -d= -f2- | tr -d '"'"'"' ')
    : "${db_host:=localhost}"; : "${db_port:=3306}"
    if ! host_valido "$db_host" || ! puerto_valido "$db_port"; then
        bad "DB_HOST/DB_PORT con formato no válido (host: letras, dígitos, '.' y '-'; puerto 1-65535)"
    elif probe_tcp "$db_host" "$db_port"; then
        ok "base de datos accesible en ${db_host}:${db_port} (${db_name:-sin nombre})"
    else
        bad "no se pudo conectar a la base de datos en ${db_host}:${db_port}"
    fi
    redis_host=$(grep -E '^REDIS_HOST=' .env | cut -d= -f2- | tr -d '"'"'"' ')
    redis_port=$(grep -E '^REDIS_PORT=' .env | cut -d= -f2- | tr -d '"'"'"' ')
    : "${redis_host:=localhost}"; : "${redis_port:=6379}"
    # Redis es obligatorio para el worker de aprovisionamiento (ADR-003,
    # FNC-067): sin él, la unidad NOMBRE-worker no arranca.
    # Solo nombre de host: el worker rechaza una IP literal.
    if [[ "$redis_host" =~ ^[0-9.]+$ || "$redis_host" == *:* ]]; then
        bad "REDIS_HOST debe ser un nombre de host, no una IP (el worker no arrancaría)"
    fi
    if ! host_valido "$redis_host" || ! puerto_valido "$redis_port"; then
        bad "REDIS_HOST/REDIS_PORT con formato no válido (host: letras, dígitos, '.' y '-'; puerto 1-65535)"
    elif probe_tcp "$redis_host" "$redis_port"; then
        ok "Redis accesible en ${redis_host}:${redis_port}"
    else
        bad "Redis no responde en ${redis_host}:${redis_port} (obligatorio para el worker de aprovisionamiento)"
    fi
    # Solo se comprueba que tenga valor; nunca se imprime (SEG-29). Unas
    # comillas vacías ("" o '') no cuentan como valor.
    grep -qE "^REDIS_PASS=([^\"'[:space:]].*|\"[^\"]+\".*|'[^']+'.*)$" .env \
        && ok "REDIS_PASS definida" \
        || bad "REDIS_PASS sin definir: el worker exige Redis con contraseña (SEG-29)"
    grep -qE '^SECRET_KEY=.+' .env \
        && ok "SECRET_KEY definida" \
        || bad "SECRET_KEY sin definir: las sesiones no serían seguras"
    # Vaultwarden (ADR-005): solo nombres y formato, nunca valores.
    while read -r nivel texto; do
        case "$nivel" in
            OK) ok "$texto" ;;
            AVISO) warn "$texto" ;;
            *) bad "$texto" ;;
        esac
    done < <(revisar_vaultwarden .env)
else
    bad ".env ausente — copiar de .env.example y rellenar credenciales"
fi

# Las unidades arrancan después de este servicio (install.sh lo detecta igual;
# --db-service lo fuerza).
if servicio_bd="$(detectar_servicio_bd)"; then
    ok "servicio de BD local: $servicio_bd (las unidades arrancarán después)"
else
    printf "  sin servicio de BD local (mysqld, mariadb ni mysql): BD remota; las unidades no dependerán de ella\n"
fi

# --- 8. Puertos --------------------------------------------------------------
head2 "Puertos"
# Del .env solo se leen estas dos claves, sin cargarlo (como REDIS_HOST).
puertos_ok=1
API_PORT="$(resolver_puerto "$API_PORT" .env API_PORT "$API_PORT_POR_DEFECTO")" \
    || { bad "API_PORT no válido (entero de ${PUERTO_SERVICIO_MIN} a ${PUERTO_SERVICIO_MAX})"; puertos_ok=0; }
WEB_PORT="$(resolver_puerto "$WEB_PORT" .env WEB_PORT "$WEB_PORT_POR_DEFECTO")" \
    || { bad "WEB_PORT no válido (entero de ${PUERTO_SERVICIO_MIN} a ${PUERTO_SERVICIO_MAX})"; puertos_ok=0; }
if (( puertos_ok )) && (( API_PORT == WEB_PORT )); then
    bad "WEB_PORT y API_PORT no pueden ser iguales (${WEB_PORT})"
    puertos_ok=0
fi
(( puertos_ok )) && ok "puertos elegidos: frontend ${WEB_PORT}, backend ${API_PORT}"
for p in "$API_PORT" "$WEB_PORT"; do
    [[ -n "$p" ]] || continue
    if ss -ltn 2>/dev/null | grep -q ":${p}\b"; then
        who=$(ss -ltnp 2>/dev/null | grep ":${p}\b" | grep -oP 'users:\(\("\K[^"]+' | head -1)
        bad "puerto ${p} ocupado por ${who:-otro proceso}"
    else
        ok "puerto ${p} libre"
    fi
done

# --- 9. Reverse proxy --------------------------------------------------------
head2 "Reverse proxy"
if command -v nginx >/dev/null 2>&1; then
    ok "$(nginx -v 2>&1)"
    nginx -t >/dev/null 2>&1 && ok "configuración actual válida" \
        || warn "'nginx -t' falla ya antes de instalar; revisar la config existente"
    [[ -d /etc/nginx/conf.d ]] && ok "/etc/nginx/conf.d disponible" \
        || warn "no existe /etc/nginx/conf.d"
else
    warn "nginx no está instalado (lo instala el script)"
fi

# --- 10. SELinux y cortafuegos ----------------------------------------------
head2 "SELinux y cortafuegos"
if command -v getenforce >/dev/null 2>&1; then
    mode=$(getenforce)
    printf "  SELinux: %s\n" "$mode"
    if [[ "$mode" == "Enforcing" ]]; then
        # Sin este booleano, nginx recibe 502 al llamar a los upstream locales.
        if command -v getsebool >/dev/null 2>&1 && \
           [[ "$(getsebool httpd_can_network_connect 2>/dev/null)" == *"--> on" ]]; then
            ok "httpd_can_network_connect activo (nginx puede llamar a los servicios)"
        else
            warn "httpd_can_network_connect desactivado: nginx daría 502 al proxy (el script lo activa)"
        fi
    fi
else
    printf "  SELinux: no disponible\n"
fi

if systemctl is-active --quiet firewalld 2>/dev/null; then
    ok "firewalld activo"
    firewall-cmd --list-services 2>/dev/null | grep -qw https \
        && ok "https permitido" \
        || warn "https no está permitido en la zona activa (el script lo añade)"
else
    printf "  firewalld: inactivo\n"
fi

# --- 10a. Nombre del despliegue ----------------------------------------------
head2 "Nombre del despliegue"
if nombre_despliegue_valido "$APP_NAME"; then
    ok "APP_NAME=$APP_NAME"
else
    bad "APP_NAME='$APP_NAME' no es válido (minúsculas, dígitos, '-' o '_'); indicar otro con APP_NAME=… y --name"
fi
printf "  unidades:  %s-backend, %s-frontend, %s-worker\n" "$APP_NAME" "$APP_NAME" "$APP_NAME"
printf "  prefijo:   %s (en sitio)\n" "$RAIZ_CODIGO"
printf "  registros: /var/log/%s\n" "$APP_NAME"
printf "  nginx:     /etc/nginx/conf.d/%s.conf\n" "$APP_NAME"
for u in "${APP_NAME}-backend" "${APP_NAME}-frontend" "${APP_NAME}-worker"; do
    if systemctl list-unit-files "$u.service" 2>/dev/null | grep -q "$u"; then
        warn "$u.service ya existe; la instalación lo sobrescribirá"
    fi
done
printf "  cambiar con: APP_NAME=otro ./deploy/preflight.sh\n"

# --- 10b. Usuario de servicio ------------------------------------------------
head2 "Usuario de servicio"
SVC_USER="${SVC_USER:-${SUDO_USER:-$(id -un)}}"
if id "$SVC_USER" >/dev/null 2>&1; then
    ok "$SVC_USER existe (grupo $(id -gn "$SVC_USER"))"
    printf "  los servicios correrán con esta cuenta\n"
else
    warn "$SVC_USER no existe: indicar otra con --user, o --create-user al instalar"
fi
printf "  cambiar con: SVC_USER=otro ./deploy/preflight.sh\n"

# --- 11. Estado del proyecto -------------------------------------------------
head2 "Proyecto"
[[ -f run.py && -d app ]] && ok "backend presente" || bad "no parece la raíz del proyecto"
[[ -f frontend/package.json ]] && ok "frontend presente" || bad "falta frontend/package.json"
[[ -d venv ]] && warn "existe un venv; se recreará (el de desarrollo no es portable)" \
              || printf "  venv: se creará\n"
[[ -d frontend/node_modules ]] && warn "existe node_modules; 'npm ci' lo reemplazará" \
                              || printf "  node_modules: se instalará\n"

# --- Resumen -----------------------------------------------------------------
printf "\n%sResumen%s\n" "$c_bold" "$c_off"
printf "  bloqueantes: %d   avisos: %d\n" "$problems" "$warnings"
if (( problems > 0 )); then
    printf "\n  %sResolver los puntos marcados FALTA antes de instalar.%s\n" "$c_bad" "$c_off"
    exit 1
fi
printf "\n  %sSe puede continuar:%s sudo ./deploy/install.sh\n" "$c_ok" "$c_off"
exit 0
