# shellcheck shell=bash
#
# Revisión de las variables de Vaultwarden en el .env del servidor (FNC-068,
# ADR-005). La cargan preflight.sh e install.sh con `source`.
#
#   revisar_vaultwarden RUTA_ENV
#
# Imprime una línea por hallazgo: "OK <texto>", "AVISO <texto>" o
# "FALTA <texto>". Sale con 1 si hay algún FALTA.
#
# Solo comprueba que cada variable tenga valor y el formato de las que no son
# secretas. NUNCA imprime un valor ni ejecuta el .env (no se hace `source`:
# corre como root y el archivo no es de confianza).

VW_REQUERIDAS=(VAULTWARDEN_URL VAULTWARDEN_CLIENT_ID VAULTWARDEN_CLIENT_SECRET
               VAULTWARDEN_EMAIL VAULTWARDEN_MASTER_PASSWORD
               VAULTWARDEN_COLLECTION_ID)

# Valor no vacío: unas comillas vacías ("" o '') no cuentan.
_vw_tiene_valor() {
    grep -qE "^$2=([^\"'[:space:]].*|\"[^\"]+\".*|'[^']+'.*)$" "$1"
}

# Valor de una variable NO secreta, sin comillas ni espacios.
_vw_valor() {
    grep -E "^$2=" "$1" | tail -1 | cut -d= -f2- | tr -d '"'"'"' '
}

revisar_vaultwarden() {
    local env="$1" fallos=0 app_env alguna=0 var url host
    app_env="$(_vw_valor "$env" APP_ENV | tr '[:upper:]' '[:lower:]')"
    if [[ "$app_env" == "development" ]]; then
        echo "OK APP_ENV=development: credenciales desde el .env (sin Vaultwarden)"
        return 0
    fi

    for var in "${VW_REQUERIDAS[@]}" VAULTWARDEN_CA_CERT_FILE \
               VAULTWARDEN_TIMEOUT_SECONDS LDAP_BIND_PASSWORD_REF; do
        _vw_tiene_valor "$env" "$var" && alguna=1
    done

    # Bind LDAP: exactamente una fuente (ADR-005 A con la referencia, C con la
    # contraseña inyectada en el .env).
    if _vw_tiene_valor "$env" LDAP_URL; then
        local con_pass=0 con_ref=0
        _vw_tiene_valor "$env" LDAP_BIND_PASSWORD && con_pass=1
        _vw_tiene_valor "$env" LDAP_BIND_PASSWORD_REF && con_ref=1
        if (( con_pass + con_ref == 0 )); then
            echo "FALTA LDAP_BIND_PASSWORD_REF (o LDAP_BIND_PASSWORD): el directorio no tendría contraseña de bind"
            fallos=1
        elif (( con_pass + con_ref == 2 )); then
            echo "FALTA definir LDAP_BIND_PASSWORD o LDAP_BIND_PASSWORD_REF, no ambas (la app no arrancaría)"
            fallos=1
        elif (( con_ref )); then
            echo "OK contraseña de bind LDAP desde Vaultwarden (LDAP_BIND_PASSWORD_REF)"
        else
            echo "AVISO contraseña de bind LDAP en el .env (ADR-005 C); se recomienda LDAP_BIND_PASSWORD_REF"
        fi
    fi

    if (( ! alguna )); then
        echo "AVISO sin VAULTWARDEN_*: los conectores fallarán cerrado (credencial no configurada)"
        return "$fallos"
    fi

    for var in "${VW_REQUERIDAS[@]}"; do
        if _vw_tiene_valor "$env" "$var"; then
            echo "OK $var definida"
        else
            echo "FALTA $var sin definir (obligatoria con Vaultwarden)"
            fallos=1
        fi
    done

    url="$(_vw_valor "$env" VAULTWARDEN_URL)"
    if [[ -n "$url" ]]; then
        host="${url#https://}"; host="${host%%/*}"; host="${host%:*}"
        if [[ "$url" != https://* ]]; then
            echo "FALTA VAULTWARDEN_URL debe usar https://"
            fallos=1
        elif [[ "$host" =~ ^[0-9.]+$ || "$host" == \[* || ! "$host" =~ ^[A-Za-z0-9.-]+$ ]]; then
            echo "FALTA VAULTWARDEN_URL debe usar un nombre de host, no una IP"
            fallos=1
        fi
    fi
    local cliente
    cliente="$(_vw_valor "$env" VAULTWARDEN_CLIENT_ID)"
    if [[ -n "$cliente" && "$cliente" != user.* ]]; then
        echo "FALTA VAULTWARDEN_CLIENT_ID debe ser la llave de API personal (user.<uuid>)"
        fallos=1
    fi
    return "$fallos"
}
