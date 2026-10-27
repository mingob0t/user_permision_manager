#!/usr/bin/env bash
#
# Instalación de Nexus en Rocky/RHEL 8 o 9.
#
#   sudo ./deploy/install.sh [--name miapp] [--prefix /opt/miapp] [--user cuenta]
#                            [--domain nexus.example.com] [--python /usr/bin/python3.11]
#                            [--proxy http://proxy:3128] [--no-proxy localhost,.intranet.example]
#                            [--db-service mariadb]
#
# --name define el nombre del despliegue: unidades NOMBRE-backend,
# NOMBRE-frontend y NOMBRE-worker, prefijo /opt/NOMBRE, registros /var/log/NOMBRE y
# /etc/nginx/conf.d/NOMBRE.conf. Se puede ajustar cada uno por separado con
# --prefix y --logdir. --title cambia solo el texto descriptivo.
#
# --user debe ser una cuenta existente (por defecto, quien invoca sudo); con
# --create-user el script la crea si no está.
#
# Usa el Python del sistema si es 3.11 o superior; solo instala uno si no hay.
#
# Las unidades arrancan después del servicio de la BD local, que se detecta
# (mysqld, mariadb o mysql); --db-service lo fuerza. Sin BD local no dependen
# de ninguno.
#
# Ejecutar antes ./deploy/preflight.sh: este script asume que la evaluación pasó.
# Es idempotente: se puede repetir para actualizar una instalación existente.
#
# Qué hace, en orden:
#   1. Paquetes del sistema (Python, Node, nginx, cabeceras de compilación)
#   2. Comprobación del usuario de servicio (solo lo crea con --create-user)
#   3. Copia del proyecto al prefijo y permisos
#   4. venv del backend y build del frontend
#   5. Unidades systemd (backend, frontend y worker de aprovisionamiento)
#   6. nginx como reverse proxy, con SELinux y firewalld
#
# No toca la base de datos: las migraciones (Alembic) se aplican aparte.

set -Eeuo pipefail

# Nombre del despliegue. De él se derivan las unidades systemd, el prefijo, el
# directorio de registros y el fichero de nginx, salvo que se indiquen aparte.
APP_NAME="nexus"
APP_TITLE=""                   # por defecto, APP_NAME capitalizado
PREFIX=""                      # por defecto, /opt/$APP_NAME
LOGDIR=""                      # por defecto, /var/log/$APP_NAME
# Usuario con el que corren los servicios. Debe existir ya: el script no crea
# cuentas. Por defecto, el que invoca sudo.
SVC_USER="${SUDO_USER:-$(id -un)}"
# Crear la cuenta solo si se pide explícitamente, con --create-user o
# CREATE_USER=1. Sin ello, el usuario indicado tiene que existir ya.
CREATE_USER="${CREATE_USER:-0}"
DOMAIN=""
# El proyecto funciona con Python 3.11 o superior. Se usa el intérprete que ya
# haya en el sistema; --python fuerza uno concreto.
PY_MIN_MINOR=11
PY_BIN=""
NODE_MAJOR="22"                # Node LTS que se instala
# Mínimo de Node: el mismo rango que "engines" de frontend/package.json
# (^22.13.0 || >=24.0.0). Lo fijan vitest 4 y jsdom 29; Next 15 pide menos.
# Node 23 (impar, sin LTS) queda fuera porque vitest no lo admite.
NODE_MIN_MINOR=13              # menor mínima dentro de NODE_MAJOR
NODE_NEXT_MAJOR=24             # primera mayor posterior que se acepta completa
NODE_RANGO="^${NODE_MAJOR}.${NODE_MIN_MINOR}.0 || >=${NODE_NEXT_MAJOR}.0.0"
SKIP_PKGS=0
# Servicio systemd de la BD local para After=/Wants= (FNC-125). Vacío: se
# detecta; --db-service o DB_SERVICE lo fuerzan.
DB_SERVICE="${DB_SERVICE:-}"
# Proxy de salida. Se toma de --proxy o del entorno; vacío = conexión directa.
PROXY_URL="${PROXY_URL:-${https_proxy:-${HTTPS_PROXY:-${http_proxy:-${HTTP_PROXY:-}}}}}"
NO_PROXY_LIST="${no_proxy:-${NO_PROXY:-localhost,127.0.0.1,::1}}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --name)   APP_NAME="$2"; shift 2 ;;
        --title)  APP_TITLE="$2"; shift 2 ;;
        --logdir) LOGDIR="$2"; shift 2 ;;
        --prefix) PREFIX="$2"; shift 2 ;;
        --user)   SVC_USER="$2"; shift 2 ;;
        --domain) DOMAIN="$2"; shift 2 ;;
        --python) PY_BIN="$2"; shift 2 ;;
        --proxy)  PROXY_URL="$2"; shift 2 ;;
        --create-user) CREATE_USER=1; shift ;;
        --no-proxy) NO_PROXY_LIST="$2"; shift 2 ;;
        --db-service) DB_SERVICE="$2"; shift 2 ;;
        --skip-packages) SKIP_PKGS=1; shift ;;
        -h|--help) sed -n '2,27p' "$0"; exit 0 ;;
        *) echo "Opción desconocida: $1" >&2; exit 2 ;;
    esac
done

# El nombre acaba en rutas, unidades systemd y nginx: se restringe a lo que es
# válido en todos esos sitios.
[[ "$APP_NAME" =~ ^[a-z][a-z0-9_-]{0,31}$ ]] \
    || { echo "ERROR: --name debe ser minúsculas, dígitos, '-' o '_' (máx. 32)" >&2; exit 2; }

: "${PREFIX:=/opt/$APP_NAME}"
: "${LOGDIR:=/var/log/$APP_NAME}"
: "${APP_TITLE:=$(tr '[:lower:]' '[:upper:]' <<< "${APP_NAME:0:1}")${APP_NAME:1}}"
BACKEND_UNIT="${APP_NAME}-backend"
FRONTEND_UNIT="${APP_NAME}-frontend"
# Worker de aprovisionamiento (FNC-049, FNC-067): exige Redis con contraseña.
WORKER_UNIT="${APP_NAME}-worker"

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# shellcheck source=deploy/servicio_bd.sh
. "$SRC/deploy/servicio_bd.sh"
# shellcheck source=deploy/copia_proyecto.sh
. "$SRC/deploy/copia_proyecto.sh"
if [[ -n "$DB_SERVICE" ]]; then
    DB_SERVICE="$(servicio_bd_valido "$DB_SERVICE")" \
        || { echo "ERROR: --db-service debe ser un nombre de unidad (letras, dígitos, ':', '_', '.', '@' o '-'), p. ej. mariadb" >&2; exit 2; }
fi

log()  { printf "\n==> %s\n" "$1"; }
note() { printf "    %s\n" "$1"; }
die()  { printf "\nERROR: %s\n" "$1" >&2; exit 1; }

# ¿La versión de Node ($1, salida de `node --version`) cumple NODE_RANGO?
node_cumple_minimo() {
    local v=${1#v} mayor menor
    mayor=${v%%.*}; v=${v#*.}; menor=${v%%.*}
    [[ "$mayor" =~ ^[0-9]+$ && "$menor" =~ ^[0-9]+$ ]] || return 1
    (( 10#$mayor == NODE_MAJOR && 10#$menor >= NODE_MIN_MINOR )) \
        || (( 10#$mayor >= NODE_NEXT_MAJOR ))
}

trap 'die "falló en la línea $LINENO. Nada más se ha modificado."' ERR

resolve_python() {
    # Rutas del sistema explícitas: con un venv activo, `command -v python3`
    # devolvería su intérprete y el venv nuevo quedaría anidado.
    local candidate minor
    for candidate in /usr/bin/python3.13 /usr/bin/python3.12 /usr/bin/python3.11 \
                     /usr/local/bin/python3.12 /usr/local/bin/python3.11 \
                     /usr/bin/python3; do
        [[ -x "$candidate" ]] || continue
        minor=$("$candidate" -c 'import sys; print(sys.version_info[1])' 2>/dev/null) || continue
        if [[ -n "$minor" ]] && (( minor >= PY_MIN_MINOR )); then
            printf '%s' "$candidate"
            return 0
        fi
    done
    return 1
}

[[ $EUID -eq 0 ]] || die "hay que ejecutarlo como root (sudo)."
[[ -f "$SRC/run.py" && -f "$SRC/frontend/package.json" ]] \
    || die "no encuentro el proyecto en $SRC"

# --- 0. Proxy de salida ------------------------------------------------------
# Cada herramienta lo lee de un sitio distinto: dnf de su propio fichero, pip y
# npm del entorno o de su configuración. Se cubren los tres.
# El separador de credenciales es el último @: una contraseña puede contener
# ese carácter, y con el primero quedaría parte visible.
mask_proxy() { sed -E 's#(://).*@#\1***@#' <<< "$1"; }

if [[ -n "$PROXY_URL" ]]; then
    log "Proxy de salida"
    note "usando $(mask_proxy "$PROXY_URL")"

    export http_proxy="$PROXY_URL"  HTTP_PROXY="$PROXY_URL"
    export https_proxy="$PROXY_URL" HTTPS_PROXY="$PROXY_URL"
    export no_proxy="$NO_PROXY_LIST" NO_PROXY="$NO_PROXY_LIST"

    # dnf ignora las variables de entorno: hay que dejarlo en su configuración.
    if [[ -f /etc/dnf/dnf.conf ]] && ! grep -qE '^\s*proxy\s*=' /etc/dnf/dnf.conf; then
        cp /etc/dnf/dnf.conf "/etc/dnf/dnf.conf.bak-$(date +%s 2>/dev/null || echo prev)"
        printf 'proxy=%s\n' "$PROXY_URL" >> /etc/dnf/dnf.conf
        note "proxy añadido a /etc/dnf/dnf.conf (copia previa guardada)"
    fi

    if ! curl -fsS --max-time 15 --proxy "$PROXY_URL" -o /dev/null \
              https://pypi.org/simple/ 2>/dev/null; then
        die "el proxy no da salida a pypi.org; revisar la URL y las credenciales"
    fi
    note "salida a Internet comprobada"
else
    log "Proxy de salida"
    note "no configurado; se asume conexión directa"
fi

# --- 0b. Servicio de la base de datos ----------------------------------------
# Antes de los paquetes: decide el cliente mysql y las unidades systemd.
log "Servicio de la base de datos"
if [[ -n "$DB_SERVICE" ]]; then
    note "servicio de BD: $DB_SERVICE (indicado)"
elif DB_SERVICE="$(detectar_servicio_bd)"; then
    note "servicio de BD local: $DB_SERVICE (las unidades arrancan después)"
else
    DB_SERVICE=""
    note "sin servicio de BD local (BD remota): las unidades no dependen de ella"
fi

# --- 1. Paquetes -------------------------------------------------------------
if (( SKIP_PKGS )); then
    log "Paquetes del sistema (omitido por --skip-packages)"
    [[ -z "$PY_BIN" ]] && PY_BIN="$(resolve_python || true)"
    [[ -n "$PY_BIN" && -x "$PY_BIN" ]] \
        || die "no hay Python >= 3.${PY_MIN_MINOR}; ejecutar sin --skip-packages"
    note "usando $PY_BIN"
    node_cumple_minimo "$(node --version 2>/dev/null || true)" \
        || die "no hay Node ${NODE_RANGO}; ejecutar sin --skip-packages"
    note "usando Node $(node --version)"
else
    log "Paquetes del sistema"

    # Se reutiliza el Python del sistema si sirve, para no acumular versiones.
    if [[ -z "$PY_BIN" ]]; then
        PY_BIN="$(resolve_python || true)"
    fi
    if [[ -n "$PY_BIN" && -x "$PY_BIN" ]]; then
        note "$($PY_BIN --version) ya presente en $PY_BIN; no se instala otro"
        "$PY_BIN" -c 'import venv' 2>/dev/null || \
            die "$PY_BIN no tiene el módulo venv; instalar su paquete -devel"
    else
        # Rocky/RHEL 8 trae 3.6: hace falta un módulo de AppStream. Se prefiere 3.11
        # por ser el mínimo que el proyecto necesita.
        note "no hay Python >= 3.${PY_MIN_MINOR}; instalando python311"
        dnf -y module reset python311 >/dev/null 2>&1 || true
        dnf -y module enable python311 >/dev/null 2>&1 || true
        dnf -y install python311 python311-devel || \
            die "no se pudo instalar Python; revisar los repositorios AppStream"
        PY_BIN="$(resolve_python)" || die "Python instalado pero no localizado"
    fi

    if ! node_cumple_minimo "$(node --version 2>/dev/null || true)"; then
        note "instalando Node ${NODE_MAJOR}"
        if dnf -y module list "nodejs:${NODE_MAJOR}" >/dev/null 2>&1; then
            dnf -y module reset nodejs >/dev/null 2>&1 || true
            dnf -y module enable "nodejs:${NODE_MAJOR}"
            dnf -y install nodejs npm
        else
            # AppStream de Rocky/RHEL 8 o 9 puede no llegar a Node 22; NodeSource sí.
            note "el módulo nodejs:${NODE_MAJOR} no está; usando NodeSource"
            # curl y el script de NodeSource ya ven el proxy por el entorno.
            curl -fsSL "https://rpm.nodesource.com/setup_${NODE_MAJOR}.x" | bash -
            dnf -y install nodejs
        fi
        # Si ya había otro Node de dnf, `install` no lo cambia de versión.
        node_cumple_minimo "$(node --version 2>/dev/null || true)" \
            || die "Node $(node --version 2>/dev/null || echo ausente) no cumple ${NODE_RANGO}; cambiar con 'dnf module switch-to nodejs:${NODE_MAJOR}' o quitar el Node anterior"
    else
        note "Node $(node --version) ya presente"
    fi

    # cryptography, cffi, bcrypt y PyNaCl compilan si no hay rueda para la
    # plataforma. PyMySQL y ldap3 son puro Python: no hacen falta
    # mariadb-devel ni openldap-devel (FNC-125).
    note "cabeceras de compilación y nginx"
    dnf -y install gcc make openssl-devel libffi-devel nginx \
        || die "no se pudieron instalar los paquetes; revisar los repositorios"
    # Cliente mysql: opcional y acorde al servidor (FNC-125).
    instalar_cliente_bd "$DB_SERVICE"
fi

# --- 2. Usuario de servicio --------------------------------------------------
log "Usuario de servicio"
if id "$SVC_USER" >/dev/null 2>&1; then
    note "$SVC_USER ya existe; no se modifica"
elif [[ "$CREATE_USER" == "1" ]]; then
    # Cuenta de servicio: sin shell y sin directorio propio, solo ejecuta los
    # servicios. Se crea únicamente porque se ha pedido.
    useradd --system --no-create-home --shell /sbin/nologin "$SVC_USER" \
        || die "no se pudo crear el usuario '$SVC_USER'"
    note "creado $SVC_USER (cuenta de sistema, sin shell)"
else
    die "el usuario '$SVC_USER' no existe.
    Indicar una cuenta existente con --user NOMBRE, o añadir --create-user
    para que el script la cree."
fi
SVC_GROUP="$(id -gn "$SVC_USER")"
note "los servicios correrán como $SVC_USER:$SVC_GROUP"

# --- 3. Copia del proyecto ---------------------------------------------------
log "Copiando el proyecto a $PREFIX"
mkdir -p "$PREFIX" "$LOGDIR"

if [[ "$(realpath "$SRC")" == "$(realpath "$PREFIX")" ]]; then
    note "el origen ya es $PREFIX; no se copia"
else
    # Sin venv, node_modules, .next ni scratch, y sin tocar lo local del
    # prefijo (.env, instance/, backups/, uploads/, storage/, logs/): FNC-125.
    copiar_proyecto "$SRC" "$PREFIX" || die "no se pudo copiar el proyecto; ver el mensaje anterior."
    note "copiado (sin venv, node_modules, .next ni scratch; .env y datos locales del prefijo intactos)"
fi

# Contiene credenciales de base de datos: solo el usuario del servicio. Nunca
# a través de un enlace (FNC-125): ver asegurar_env_prefijo.
asegurar_env_prefijo "$PREFIX" "$SVC_USER" "$SVC_GROUP" "$PY_BIN" \
    || die "el .env del prefijo no es seguro; ver el mensaje anterior."
# Vaultwarden y bind LDAP (FNC-068): mismas reglas que preflight; los valores
# los pone una persona en el .env, nunca el instalador.
# shellcheck source=deploy/secretos.sh
. "$SRC/deploy/secretos.sh"
if ! salida_vw="$(revisar_vaultwarden "$PREFIX/.env")"; then
    printf '%s\n' "$salida_vw" | sed 's/^/    /'
    die "Corregir las variables de Vaultwarden del .env (ver deploy/README.md)."
fi
printf '%s\n' "$salida_vw" | sed 's/^/    /'
# -h: cambia el enlace, no su destino (FNC-125). Sin -L: no entra en enlaces.
chown -R -h "$SVC_USER:$SVC_GROUP" "$PREFIX" "$LOGDIR"

# --- 4. Backend --------------------------------------------------------------
log "Backend (venv y dependencias)"
sudo -u "$SVC_USER" "$PY_BIN" -m venv "$PREFIX/venv"
# sudo -u no hereda el entorno, así que el proxy se pasa a pip explícitamente.
PIP_PROXY_ARG=()
[[ -n "$PROXY_URL" ]] && PIP_PROXY_ARG=(--proxy "$PROXY_URL")
sudo -u "$SVC_USER" "$PREFIX/venv/bin/pip" install --quiet "${PIP_PROXY_ARG[@]}" \
    --upgrade pip wheel
sudo -u "$SVC_USER" "$PREFIX/venv/bin/pip" install --quiet "${PIP_PROXY_ARG[@]}" \
    -r "$PREFIX/requirements.txt" \
    || die "fallo instalando dependencias de Python"
note "venv listo en $PREFIX/venv"

# --- 5. Frontend -------------------------------------------------------------
log "Frontend (dependencias y build)"
pushd "$PREFIX/frontend" >/dev/null
# npm tampoco hereda el entorno con sudo -u: se le pasa por línea de órdenes.
NPM_PROXY_ARG=()
if [[ -n "$PROXY_URL" ]]; then
    NPM_PROXY_ARG=(--proxy "$PROXY_URL" --https-proxy "$PROXY_URL"
                   --noproxy "$NO_PROXY_LIST")
    note "npm usará el proxy"
fi
sudo -u "$SVC_USER" npm ci --no-audit --no-fund "${NPM_PROXY_ARG[@]}" \
    || die "fallo en npm ci"
sudo -u "$SVC_USER" npm run build \
    || die "fallo en 'next build' (si es por memoria, añadir swap)"

# El build standalone no copia los estáticos ni public/: hay que ponerlos donde
# server.js los espera, o la página carga sin CSS ni imágenes.
sudo -u "$SVC_USER" cp -r .next/static .next/standalone/.next/static
[[ -d public ]] && sudo -u "$SVC_USER" cp -r public .next/standalone/public
popd >/dev/null
note "build en $PREFIX/frontend/.next/standalone"

# --- 6. Servicios ------------------------------------------------------------
log "Servicios systemd"
render() {
    # Sustituye los marcadores de una plantilla. '|' como separador, así que los
    # valores no pueden contenerlo (las rutas no lo hacen).
    sed -e "s|@APP_NAME@|${APP_NAME}|g" \
        -e "s|@APP_TITLE@|${APP_TITLE}|g" \
        -e "s|@PREFIX@|${PREFIX}|g" \
        -e "s|@LOGDIR@|${LOGDIR}|g" \
        -e "s|@SVC_USER@|${SVC_USER}|g" \
        -e "s|@SVC_GROUP@|${SVC_GROUP}|g" \
        -e "s|@DOMAIN@|${DOMAIN:-_}|g" \
        "$1" | aplicar_servicio_bd "$DB_SERVICE"
}

render "$PREFIX/deploy/backend.service.tmpl"  > "/etc/systemd/system/${BACKEND_UNIT}.service"
render "$PREFIX/deploy/frontend.service.tmpl" > "/etc/systemd/system/${FRONTEND_UNIT}.service"
render "$PREFIX/deploy/worker.service.tmpl"   > "/etc/systemd/system/${WORKER_UNIT}.service"
note "instaladas ${BACKEND_UNIT}.service, ${FRONTEND_UNIT}.service y ${WORKER_UNIT}.service"

# Un marcador sin sustituir dejaría la unidad inservible.
if grep -l "@[A-Z_]*@" "/etc/systemd/system/${BACKEND_UNIT}.service" \
        "/etc/systemd/system/${FRONTEND_UNIT}.service" \
        "/etc/systemd/system/${WORKER_UNIT}.service" 2>/dev/null; then
    die "quedaron marcadores sin sustituir en las unidades"
fi

systemctl daemon-reload
# Si una instalación previa agotó los reinicios del worker (StartLimitBurst),
# se limpia ese estado para que vuelva a arrancar; sin efecto si no lo hay.
systemctl reset-failed "$WORKER_UNIT" >/dev/null 2>&1 || true
systemctl enable --now "$BACKEND_UNIT" "$FRONTEND_UNIT" "$WORKER_UNIT"
sleep 3
for unit in "$BACKEND_UNIT" "$FRONTEND_UNIT" "$WORKER_UNIT"; do
    systemctl is-active --quiet "$unit" \
        && note "$unit activo" \
        || { journalctl -u "$unit" -n 20 --no-pager; die "$unit no arrancó"; }
done

# --- 7. Reverse proxy --------------------------------------------------------
log "nginx"
conf="/etc/nginx/conf.d/${APP_NAME}.conf"
render "$PREFIX/deploy/nginx.conf.tmpl" > "$conf"
if [[ -n "$DOMAIN" ]]; then
    note "configuración escrita en $conf para $DOMAIN"
else
    note "configuración escrita en $conf; falta ajustar server_name y certificados"
fi

if command -v getenforce >/dev/null 2>&1 && [[ "$(getenforce)" == "Enforcing" ]]; then
    # Sin este booleano nginx no puede conectar con los upstream y responde 502.
    setsebool -P httpd_can_network_connect 1
    note "SELinux: httpd_can_network_connect activado"
fi

if nginx -t 2>/dev/null; then
    systemctl enable --now nginx
    systemctl reload nginx
    note "nginx recargado"
else
    nginx -t || true
    note "AVISO: 'nginx -t' falla — revisar $conf (certificados, server_name)"
fi

if systemctl is-active --quiet firewalld; then
    firewall-cmd --permanent --add-service=https >/dev/null 2>&1 || true
    firewall-cmd --permanent --add-service=http  >/dev/null 2>&1 || true
    firewall-cmd --reload >/dev/null 2>&1 || true
    note "firewalld: http y https permitidos"
fi

# --- Resumen -----------------------------------------------------------------
cat <<FIN

Instalación terminada.

  backend    ${PREFIX} (127.0.0.1:5001)
  frontend   ${PREFIX}/frontend (127.0.0.1:3000)
  worker     ${WORKER_UNIT} (no escucha; journalctl -u ${WORKER_UNIT} -f)
  registros  /var/log/nexus, journalctl -u nexus-backend -f

Pendiente:
  1. Migraciones, si es una actualización (después reiniciar backend y worker):
       cd ${PREFIX} && venv/bin/alembic upgrade head   (BD existente de NEXUS: antes, una vez, alembic stamp 0001)
  2. Certificados y server_name en /etc/nginx/conf.d/nexus.conf
  3. Comprobar:  curl -s localhost:5001/api/v1/auth/context
                 curl -s -o /dev/null -w '%{http_code}\\n' localhost:3000/login

Los puertos 5001 y 3000 escuchan solo en loopback a propósito: el backend
deduce la identidad del SSO de cabeceras que solo nginx debe poder inyectar.
FIN
