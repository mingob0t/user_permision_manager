# Secretos en ejecución: Vaultwarden (FNC-068, ADR-005)

> Sin valores. Los pone una persona; el agente nunca lee `.env` ni consulta el gestor.

## Mecanismo

| Punto | Decisión |
|---|---|
| Alternativa de ADR-005 | A: API de Vaultwarden con cuenta de servicio limitada a una colección |
| Autenticación | Llave de API **personal** (`client_credentials`) de la cuenta de servicio |
| Descifrado | Del lado del cliente en la app (`app/modules/secretos/`, con `cryptography`): KDF con la contraseña maestra → clave de usuario → llave RSA → clave de la organización → ítem |
| Descartado | CLI `bw` (sesión desbloqueada, Node en el servidor; ADR-005 B) y SDK de Bitwarden (no compatible con Vaultwarden) |
| Credencial de arranque | `VAULTWARDEN_CLIENT_SECRET` y `VAULTWARDEN_MASTER_PASSWORD` en el `.env` del servidor (600, cuenta de servicio, `EnvironmentFile`). systemd 239 (Rocky 8) no tiene `LoadCredential=` |
| Lectura | Ítem tipo *login* cuyo **nombre** es la referencia, en `VAULTWARDEN_COLLECTION_ID`; secreto = contraseña, usuario = nombre de usuario |
| Fallos | Sin ítem o con dos legibles del mismo nombre → `credencial_no_encontrada` (uno ilegible se ignora); caído → `gestor_no_disponible` (se reintenta); credencial de arranque, TLS o datos rechazados → `gestor_no_configurado` |
| Red | Solo `https` con nombre de host, TLS 1.2+ validado, sin proxies ni redirecciones, `VAULTWARDEN_TIMEOUT_SECONDS` por operación, respuesta ≤ 8 MiB |
| Caché | Credenciales: `CONNECTOR_CREDENTIAL_CACHE_SECONDS` (≤ 128 entradas, por proceso). Sesión: hasta que vence el token |

## Preparar un entorno (staging o producción)

1. En Vaultwarden, una organización del portal y una colección `pokemon-<entorno>`.
2. Cuenta de servicio `svc-portal-<entorno>` (correo propio), miembro de la organización con acceso **de solo lectura** y **solo** a esa colección. KDF por defecto (PBKDF2 ≥ 600 000 o Argon2id).
3. En esa cuenta: Ajustes → Seguridad → Llave de API → copiar `client_id` (`user.<uuid>`) y `client_secret`.
4. En el `.env` del servidor: `VAULTWARDEN_URL`, `VAULTWARDEN_CLIENT_ID`, `VAULTWARDEN_CLIENT_SECRET`, `VAULTWARDEN_EMAIL`, `VAULTWARDEN_MASTER_PASSWORD`, `VAULTWARDEN_COLLECTION_ID` (y `VAULTWARDEN_CA_CERT_FILE` si la CA es interna).
5. `sudo ./deploy/preflight.sh`: debe dar `OK` en cada `VAULTWARDEN_*` (solo comprueba que tengan valor).
6. Reiniciar `<nombre>-backend` y `<nombre>-worker`.

## Alta de un ítem de conector

1. En la colección, ítem tipo **Inicio de sesión**; nombre = `credential_ref` exacto (p. ej. `pokemon/contabilidad-api`); usuario y contraseña del destino.
2. En `/admin/connectors`, la misma referencia y **Probar conexión**: `ok` = resuelta.
3. Un nombre repetido en la colección da `credencial_no_encontrada`: no se adivina.

## Bind LDAP desde Vaultwarden

1. Ítem *login* `pokemon/<entorno>/LDAP_BIND_PASSWORD` con la contraseña de la cuenta de servicio de OpenLDAP.
2. En el `.env`: `LDAP_BIND_PASSWORD_REF=pokemon/<entorno>/LDAP_BIND_PASSWORD` y `LDAP_BIND_PASSWORD` **vacía** (las dos = la app no arranca).
3. Ajustes → Directorio → Probar conexión.
4. Esa referencia queda reservada: un conector no puede usarla (se rechaza al guardar y al ejecutar).

## Rotación

| Qué | Pasos |
|---|---|
| Credencial de un conector | Cambiar en el destino y en el ítem → **Probar conexión** (vacía la caché de ese proceso) → esperar `CONNECTOR_CREDENTIAL_CACHE_SECONDS` o reiniciar backend y worker para el resto de procesos |
| Contraseña de bind LDAP | Igual: ítem y OpenLDAP; los binds fallan hasta que vence la caché o se reinicia |
| Llave de API de la cuenta de servicio | Rotar en Vaultwarden → nuevo `VAULTWARDEN_CLIENT_SECRET` en el `.env` → reiniciar |
| Contraseña maestra | Cambiarla en Vaultwarden → `VAULTWARDEN_MASTER_PASSWORD` en el `.env` → reiniciar |

`limpiar_cache()` es por proceso: la API lo llama al guardar, borrar o probar un conector (FNC-061), pero el worker y los demás workers de Gunicorn esperan a que venza la caché.

## Reversión

- Retirar la cuenta de servicio (o su acceso a la colección) y vaciar `VAULTWARDEN_*`: los conectores fallan cerrado (`gestor_no_configurado`).
- Bind LDAP: volver a `LDAP_BIND_PASSWORD` inyectada y vaciar `LDAP_BIND_PASSWORD_REF`.

## Verificación pendiente (PoC en staging)

- [ ] Resolver una credencial de prueba sin que su valor aparezca en `journalctl` ni en la bitácora.
- [ ] Una rotación completa.
- [ ] Confirmar contra la versión de Vaultwarden real que la respuesta del token trae `Key`/`PrivateKey`/`Kdf*` (si no, el cliente usa `prelogin` y el perfil de `sync`).
