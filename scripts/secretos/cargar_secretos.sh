#!/usr/bin/env bash
# Carga los secretos de un entorno desde Vaultwarden (compatible con el CLI de Bitwarden) y ejecuta un comando
# con ellos en el entorno del proceso. NUNCA escribe secretos en el repositorio ni en archivos persistentes.
#
# Uso:   scripts/secretos/cargar_secretos.sh <entorno> -- <comando>
# Ej.:   scripts/secretos/cargar_secretos.sh staging -- docker compose up -d
#
# Requisitos (los configura una PERSONA, nunca el agente):
#   - VAULTWARDEN_URL con NOMBRE DE HOST (nunca IP), p. ej. https://vault.empresa.local
#   - Bóveda desbloqueada y su sesión exportada en BW_SESSION (en CI: inicio de sesión con API key
#     usando BW_CLIENTID/BW_CLIENTSECRET guardados como secretos del CI).
#   - Ítems nombrados  <proyecto>/<entorno>/<VARIABLE>  (p. ej. nexus/staging/DB_PASSWORD); el valor va en el campo password.
#   - La lista de variables sale de .env.example (solo los NOMBRES).
set -euo pipefail

ENTORNO="${1:?Uso: $0 <entorno> -- <comando>}"; shift
[[ "${1:-}" == "--" ]] && shift
PROYECTO="${PROYECTO:-$(basename "$(git rev-parse --show-toplevel)")}"
: "${VAULTWARDEN_URL:?Define VAULTWARDEN_URL (nombre de host, no IP)}"
: "${BW_SESSION:?Desbloquea la bóveda y exporta BW_SESSION antes de ejecutar este script}"

if [[ "$ENTORNO" == "dev" ]]; then
  echo "En dev se usa el .env local; este script es para staging y producción." >&2
  exit 1
fi

CLI="bw"
"$CLI" config server "$VAULTWARDEN_URL" >/dev/null 2>&1 || true
"$CLI" sync --session "$BW_SESSION" >/dev/null

while IFS= read -r linea; do
  [[ -z "$linea" || "$linea" == \#* ]] && continue
  NOMBRE="${linea%%=*}"
  VALOR="$("$CLI" get password "${PROYECTO}/${ENTORNO}/${NOMBRE}" --session "$BW_SESSION" 2>/dev/null || true)"
  if [[ -z "$VALOR" ]]; then
    echo "Falta el secreto ${PROYECTO}/${ENTORNO}/${NOMBRE} en Vaultwarden" >&2
    exit 1
  fi
  export "${NOMBRE}=${VALOR}"
done < .env.example

exec "$@"
