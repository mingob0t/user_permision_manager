# Registro de variables y configuración

> Fuente única. Todo cambio de valor va a [HISTORIAL.md](HISTORIAL.md) con su **motivo**. Los secretos nunca llevan su valor aquí.
>
> Registro inicial levantado en FNC-001 (2026-10-13) leyendo el código heredado de NEXUS: `os.getenv` / `os.environ` en `app/` y `utils/`, `process.env` en `frontend/`, las plantillas de `deploy/` y los scripts `deploy/*.sh`. La columna **En `.env.example`** contrasta cada variable con ese archivo.
>
> Fuente por entorno: **dev** → `.env` local (copiado de `.env.example`); **staging/prod** → `.env` del servidor en el prefijo de instalación (lo carga systemd con `EnvironmentFile`), con los secretos tomados de Vaultwarden `pokemon/<entorno>/<VARIABLE>`.

## Variables de entorno — backend (Flask)

| Variable | Propósito | Tipo / valores | Por defecto en código | Ejemplo (sin secretos) | Obligatoria | Sensible | En `.env.example` | Dónde se usa | Alta | Estado |
|---|---|---|---|---|---|---|---|---|---|---|
| `SECRET_KEY` | Firma de la cookie de sesión y CSRF | texto aleatorio largo | `nexus-premium-secret-key` (inseguro) | — | Sí | **Sí** | Sí (marcador) | `app/__init__.py` | FNC-001, 2026-10-13 | Vigente |
| `DB_ENGINE` | Motor de BD. `mysql` usa PyMySQL; cualquier otro valor cae a SQLite `nexus.db` | `mysql` / otro | `sqlite` | `mysql` | Sí (prod) | No | Sí | `app/utils/uri_bd.py` (app y Alembic, FNC-039) | FNC-001, 2026-10-13 | Vigente |
| `DB_HOST` | Host de la BD | nombre de host | — (sin valor: URI inválida) | `localhost` | Sí con mysql | No | Sí | `app/utils/uri_bd.py` (app y Alembic, FNC-039), `deploy/preflight.sh` | FNC-001, 2026-10-13 | Vigente |
| `DB_PORT` | Puerto de la BD | entero | — en código; `3306` en preflight | `3306` | Sí con mysql | No | Sí | `app/utils/uri_bd.py` (app y Alembic, FNC-039), `deploy/preflight.sh` | FNC-001, 2026-10-13 | Vigente |
| `DB_NAME` | Nombre de la BD | texto | — | `pokemon_dev` | Sí con mysql | No | Sí (`admin_test`) | `app/utils/uri_bd.py` (app y Alembic, FNC-039), `deploy/preflight.sh` | FNC-001, 2026-10-13 | Vigente |
| `DB_USER` | Usuario de la BD | texto | — | `nexus` | Sí con mysql | No | Sí | `app/utils/uri_bd.py` (app y Alembic, FNC-039) | FNC-001, 2026-10-13 | Vigente |
| `DB_PASS` | Contraseña de la BD | texto | — | — | Sí con mysql | **Sí** | Sí (vacía) | `app/utils/uri_bd.py` (app y Alembic, FNC-039) | FNC-001, 2026-10-13 | Vigente |
| `REDIS_HOST` | Host de Redis (cola de aprovisionamiento, ADR-003) | nombre de host (IP → el worker no arranca) | `localhost` | `localhost` | Sí para el worker (FNC-049) | No | Sí | `app/__init__.py`, `deploy/preflight.sh`, `app/modules/provisioning/configuracion.py` | FNC-001, 2026-10-13 | Vigente |
| `REDIS_PORT` | Puerto de Redis | entero | `6379` | `6379` | No | No | Sí | `app/__init__.py`, `deploy/preflight.sh`, `app/modules/provisioning/configuracion.py` | FNC-001, 2026-10-13 | Vigente |
| `REDIS_PASS` | Contraseña de Redis. Fuente: `.env` en dev; Vaultwarden `pokemon/<entorno>/REDIS_PASS` en staging/prod | texto | ninguna | — | **Sí para el worker y para despertarlo** (FNC-049, SEG-29); sin ella la API arranca y los trabajos esperan | **Sí** | Sí (vacía, FNC-049) | `app/__init__.py`, `app/modules/provisioning/configuracion.py` | FNC-001, 2026-10-13 | Vigente |
| `PROVISIONING_QUEUE_NAME` | Nombre de la cola RQ del ejecutor | `[a-z0-9_-]{1,50}` | `aprovisionamiento` | `aprovisionamiento` | No | No | Sí | `app/modules/provisioning/configuracion.py` | FNC-049, 2026-10-19 | Vigente |
| `PROVISIONING_MAX_ATTEMPTS` | Intentos máximos de un trabajo (se fija al encolar) | entero 1–20 | `5` | `5` | No | No | Sí | `app/modules/provisioning/configuracion.py` | FNC-049, 2026-10-19 | Vigente |
| `PROVISIONING_BACKOFF_BASE_SECONDS` | Primer escalón del *backoff* exponencial | entero 1–3600 (s) | `60` | `60` | No | No | Sí | `app/modules/provisioning/configuracion.py` | FNC-049, 2026-10-19 | Vigente |
| `PROVISIONING_BACKOFF_MAX_SECONDS` | Tope del *backoff* (≥ base) | entero 1–86400 (s) | `900` | `900` | No | No | Sí | `app/modules/provisioning/configuracion.py` | FNC-049, 2026-10-19 | Vigente |
| `PROVISIONING_ATTEMPT_TIMEOUT_SECONDS` | Tiempo de espera de un intento (`job_timeout` de RQ); la reserva vence 30 s después | entero 5–600 (s) | `60` | `60` | No | No | Sí | `app/modules/provisioning/configuracion.py` | FNC-049, 2026-10-19 | Vigente |
| `PROVISIONING_POLL_INTERVAL_SECONDS` | Ocio del worker antes de barrer la BD (reintentos vencidos, avisos perdidos, reservas vencidas) | entero 5–3600 (s) | `30` | `30` | No | No | Sí | `app/modules/provisioning/configuracion.py` | FNC-049, 2026-10-19 | Vigente |
| `TZ_APP` | Zona horaria del proceso (fija `TZ`) | zona IANA | `TZ` o `America/Mexico_City` | `America/Mexico_City` | No | No | Sí | `app/__init__.py` | FNC-001, 2026-10-13 | Vigente |
| `TZ` | Respaldo de `TZ_APP` | zona IANA | `America/Mexico_City` | — | No | No | No (estándar del sistema) | `app/__init__.py` | FNC-001, 2026-10-13 | Vigente |
| `BASE_URL` | URL pública de la app para enlaces en correos y el retorno del cierre SSO | URL con dominio | En `api/auth.py`: la del host de la petición. En `auth/services.py`: vacío (enlace relativo; antes una IP literal, quitada en FNC-042) | `http://localhost:5001` (dev) / `https://<dominio>` | Sí en prod | No | Sí | `api/auth.py`, `auth/services.py` | FNC-001, 2026-10-13 | Vigente |
| `FRONTEND_URL` | Destino de las redirecciones de rutas heredadas y del login sin sesión | URL o vacío (mismo dominio) | vacío | `http://localhost:3000` (dev) / vacío (prod) | No | No | Sí | `app/__init__.py`, rutas heredadas de `auth`, `core`, `audit`, `settings`, `notifications`, `users`, `areas` | FNC-001, 2026-10-13 | Vigente |
| `AUTHELIA_ENABLED` | Activa el SSO por cabeceras | `true` / `false` | `false` | `false` | No | No | Sí | `api/auth.py`, `utils/toggle_authelia.py` | FNC-001, 2026-10-13 | Vigente |
| `AUTHELIA_SLO_URL` | URL de cierre de sesión de Authelia | URL | ninguna | `https://<host de authelia>/logout` | Sí si SSO | No | Sí | `api/auth.py` | FNC-001, 2026-10-13 | Vigente |
| `AUTHELIA_HEADER_USER` | Cabecera con el correo del usuario | nombre de cabecera | `Remote-Email` | `Remote-Email` | No | No | Sí | `api/auth.py` | FNC-001, 2026-10-13 | Vigente |
| `AUTHELIA_HEADER_NAME` | Cabecera con el nombre visible | nombre de cabecera | `Remote-Name` | `Remote-Name` | No | No | Sí | `api/auth.py` | FNC-001, 2026-10-13 | Vigente |
| `APP_ENV` | Entorno de la app; hoy solo decide si aplica `LOGIN_LOCAL_TODAS_LAS_CUENTAS` | `development` / `staging` / `production` | vacío (= no es desarrollo) | `development` (dev) / `production` | No | No | Sí (vacía) | `app/modules/auth/acceso_local.py` | FNC-077, 2026-10-19 | Vigente |
| `LOGIN_LOCAL_TODAS_LAS_CUENTAS` | Solo desarrollo: login local de cualquier cuenta local y `password` en `POST/PUT /users` (prueba de concepto sin Authelia). Sin ella, solo la cuenta de emergencia. Se ignora si `APP_ENV` no es `development` | `true` / `false` | `false` | `false` | No | No (seguridad crítica: nunca `true` fuera de dev) | Sí (`false`) | `app/modules/auth/acceso_local.py` | FNC-077, 2026-10-19 | Vigente |
| `AUTHELIA_HEADER_GROUPS` | Cabecera con los grupos | nombre de cabecera | `Remote-Groups` | `Remote-Groups` | No | No | No (retirada) | ninguno | FNC-001, 2026-10-13 | **Obsoleta** (2026-10-15, FNC-042): el rol ya no sale de `Remote-Groups` (RF-04) |
| `AUTHELIA_GROUP_ADMIN` | Grupos (separados por coma) que daban rol `administrador` por SSO | lista CSV | — | — | No | No | No (retirada) | ninguno | FNC-001, 2026-10-13 | **Obsoleta** (2026-10-15, FNC-042): solo el superadmin eleva en el portal (RF-04, SEG-10) |
| `TRUSTED_PROXIES` | Direcciones de origen autorizadas a inyectar cabeceras `Remote-*` y, para la auditoría, `X-Forwarded-For` (FNC-047) (se compara con `remote_addr`, por eso son direcciones y no nombres de host; excepción justificada al lineamiento "sin IPs") | lista CSV | loopback IPv4 e IPv6 | loopback | No | No (seguridad crítica) | Sí | `api/auth.py`, `audit/ip_cliente.py` | FNC-001, 2026-10-13; auditoría FNC-047, 2026-10-14 | Vigente |
| `NOTIFY_USER_CREATED` | Envía la plantilla `usuario_creado` al dar de alta por LDAP o SSO | `true` / `false` | `true` | `true` | No | No | **No (faltante)** | `api/auth.py`, `auth/services.py` | FNC-001, 2026-10-13 | Vigente |
| `NOTIFY_ACCESS_EVENTS` | Interruptor de los correos del gestor de accesos (`solicitud_nueva`, `solicitud_aprobada`, `solicitud_rechazada`, `aprovisionamiento_fallido`); `ENABLE_NOTIFICATIONS=false` también los corta | `true` / `false` | `true` | `true` | No | No | Sí | `notifications/access_notifications.py` | FNC-048, 2026-10-15 | Vigente |
| `DEBUG_LDAP` | Log detallado de ldap3 en `logs/ldap_debug.log` | `true` / otro | desactivado | `false` | No | No (el log puede contener datos del directorio) | **No (faltante)** | `app/modules/directory/depuracion.py` (antes `auth/services.py`; FNC-043) | FNC-001, 2026-10-13 | Vigente |
| `LDAP_URL` | Servidor OpenLDAP; vacío = directorio inactivo. Con valor, se valida todo al arrancar | `ldaps://<host>[:puerto]` o `ldap://<host>[:puerto]` (StartTLS obligatorio); nombre de host, no IP | vacío (inactivo) | `ldaps://ldap.<dominio>` | Sí para usar el directorio | No | Sí | `app/modules/directory/configuracion.py` | FNC-040, 2026-10-14 | Vigente (login desde FNC-042; `GET /auth-config`, prueba y búsqueda desde FNC-043; escritura en `writer.py` desde FNC-041, sin llamadores hasta FNC-049/064) |
| `LDAP_CA_CERT_FILE` | CA con la que se valida el certificado del servidor | ruta a archivo PEM legible | vacío (CA del sistema) | `/etc/pki/<nombre>/ldap-ca.pem` | Si el certificado es de una CA interna | No | Sí | `app/modules/directory/configuracion.py` | FNC-040, 2026-10-14 | Vigente (login desde FNC-042; `GET /auth-config`, prueba y búsqueda desde FNC-043; escritura en `writer.py` desde FNC-041, sin llamadores hasta FNC-049/064) |
| `LDAP_BIND_DN` | DN de la cuenta de servicio (lectura) | DN | — | `cn=<servicio>,<base>` | Sí con `LDAP_URL` | No | Sí | `app/modules/directory/configuracion.py` | FNC-040, 2026-10-14 | Vigente (login desde FNC-042; `GET /auth-config`, prueba y búsqueda desde FNC-043; escritura en `writer.py` desde FNC-041, sin llamadores hasta FNC-049/064) |
| `LDAP_BIND_PASSWORD` | Contraseña de la cuenta de servicio | texto | — | — | Sí con `LDAP_URL` | **Sí** (`.env` en dev; Vaultwarden `pokemon/<entorno>/LDAP_BIND_PASSWORD`) | Sí | `app/modules/directory/configuracion.py` | FNC-040, 2026-10-14 | Vigente (login desde FNC-042; `GET /auth-config`, prueba y búsqueda desde FNC-043; escritura en `writer.py` desde FNC-041, sin llamadores hasta FNC-049/064) |
| `LDAP_USERS_BASE_DN` | Base de búsqueda de personas | DN | — | `ou=<personas>,<base>` | Sí con `LDAP_URL` | No | Sí | `app/modules/directory/configuracion.py` | FNC-040, 2026-10-14 | Vigente (login desde FNC-042; `GET /auth-config`, prueba y búsqueda desde FNC-043; escritura en `writer.py` desde FNC-041, sin llamadores hasta FNC-049/064) |
| `LDAP_GROUPS_BASE_DN` | Base de búsqueda de grupos | DN | — | `ou=<grupos>,<base>` | Sí con `LDAP_URL` | No | Sí | `app/modules/directory/configuracion.py` | FNC-040, 2026-10-14 | Vigente (login desde FNC-042; `GET /auth-config`, prueba y búsqueda desde FNC-043; escritura en `writer.py` desde FNC-041, sin llamadores hasta FNC-049/064) |
| `LDAP_USER_ATTR` | Atributo que identifica a la persona | nombre de atributo LDAP | `uid` | `uid` | No | No | Sí | `app/modules/directory/configuracion.py` | FNC-040, 2026-10-14 | Vigente (login desde FNC-042; `GET /auth-config`, prueba y búsqueda desde FNC-043; escritura en `writer.py` desde FNC-041, sin llamadores hasta FNC-049/064) |
| `LDAP_GROUP_OBJECT_CLASS` | Clase de los grupos | `groupOfNames` / `groupOfUniqueNames` / `posixGroup` | `groupOfNames` | `groupOfNames` | No | No | Sí | `app/modules/directory/configuracion.py` | FNC-040, 2026-10-14 | Vigente (login desde FNC-042; `GET /auth-config`, prueba y búsqueda desde FNC-043; escritura en `writer.py` desde FNC-041, sin llamadores hasta FNC-049/064) |
| `LDAP_GROUP_MEMBER_ATTR` | Atributo de membresía del grupo (`memberUid` guarda el identificador; el resto, el DN) | nombre de atributo LDAP | `member` | `member` | No | No | Sí | `app/modules/directory/configuracion.py` | FNC-040, 2026-10-14 | Vigente (login desde FNC-042; `GET /auth-config`, prueba y búsqueda desde FNC-043; escritura en `writer.py` desde FNC-041, sin llamadores hasta FNC-049/064) |
| `LDAP_TIMEOUT_SECONDS` | Espera de conexión y de respuesta del directorio | entero > 0 | `5` | `5` | No | No | Sí | `app/modules/directory/configuracion.py` | FNC-040, 2026-10-14 | Vigente (login desde FNC-042; `GET /auth-config`, prueba y búsqueda desde FNC-043; escritura en `writer.py` desde FNC-041, sin llamadores hasta FNC-049/064) |
| `LDAP_USER_OBJECT_CLASSES` | Clases de las cuentas que crea el portal | clases LDAP separadas por coma | `inetOrgPerson` | `inetOrgPerson` | No | No | Sí | `configuracion.py`, `writer.py` | FNC-041, 2026-10-15 | Vigente (sin llamadores hasta FNC-064) |
| `LDAP_GROUP_PLACEHOLDER_MEMBER` | Miembro de relleno al quitar al último miembro de un `groupOfNames`/`groupOfUniqueNames` | DN de una entrada sin login ni contraseña, fuera de `LDAP_USERS_BASE_DN` (validado al arrancar) | vacío (no se quita el último miembro: `error_permanente`) | `cn=<sin-miembros>,<base>` | No | No | Sí | `configuracion.py`, `writer.py` | FNC-041, 2026-10-15 | Vigente (sin llamadores hasta FNC-049) |
| `LDAP_PLATFORM_GROUP_TEMPLATE` | Convención del DN de grupo de una plataforma, relativa a `LDAP_GROUPS_BASE_DN`; deriva los grupos cuando no llegan en `POST/PUT /platforms` | RDN con `{plataforma}` y `{nivel}` (obligatorios) y `{area}` (opcional); validada al arrancar | vacío (no se deriva; el superadmin indica los DN) | `cn={plataforma}-{nivel},ou={area}` | No | No | Sí | `configuracion.py`, `app/modules/platforms/grupos.py` | FNC-046, 2026-10-19 | Vigente |
| `SMTP_FORCE_ENV` | `true`: el SMTP sale siempre del entorno y la interfaz queda en solo lectura | booleano (`1/true/yes/on/si`) | `false` | `false` | No | No | Sí | `notifications/services.py`, `api/admin.py` | FNC-001, 2026-10-13 | Vigente |
| `SMTP_SERVER` | Servidor SMTP (respaldo o forzado) | nombre de host | ninguno (sin él no hay config de entorno) | `smtp.<dominio>` | Sí si `SMTP_FORCE_ENV` | No | Sí (vacío) | `notifications/services.py` | FNC-001, 2026-10-13 | Vigente |
| `SMTP_PORT` | Puerto SMTP | entero | `587` | `587` | No | No | Sí | `notifications/services.py` | FNC-001, 2026-10-13 | Vigente |
| `SMTP_ENCRYPTION` | Cifrado | `starttls` / `ssl` / `none` | `starttls` | `starttls` | No | No | Sí | `notifications/services.py` | FNC-001, 2026-10-13 | Vigente |
| `SMTP_AUTH` | Autenticar contra el SMTP | booleano | `true` si hay usuario y contraseña | `true` | No | No | Sí | `notifications/services.py` | FNC-001, 2026-10-13 | Vigente |
| `SMTP_USER` | Usuario SMTP | texto | ninguno | `servicio@<dominio>` | No | No | Sí (vacío) | `notifications/services.py` | FNC-001, 2026-10-13 | Vigente |
| `SMTP_PASSWORD` | Contraseña SMTP | texto | ninguna | — | No | **Sí** | Sí (vacía) | `notifications/services.py` | FNC-001, 2026-10-13 | Vigente |
| `SMTP_SENDER_NAME` | Nombre del remitente | texto | `Nexus` | `Pokemon` | No | No | Sí | `notifications/services.py` | FNC-001, 2026-10-13 | Vigente |
| `SMTP_SENDER_EMAIL` | Dirección del remitente | correo | `SMTP_USER` | `noreply@<dominio>` | No | No | Sí (vacío) | `notifications/services.py` | FNC-001, 2026-10-13 | Vigente |
| `ENABLE_NOTIFICATIONS` | Interruptor global de correo | `true` / `false` | `true` | `true` | No | No | Sí | `notifications/services.py` | FNC-001, 2026-10-13 | Vigente |
| `DEBUG_SMTP` | Traza del diálogo SMTP en consola | `true` / `false` | `false` | `false` | No | No | Sí | `notifications/services.py` | FNC-001, 2026-10-13 | Vigente |
| `NGINX_CONF_PATH` | Archivo de nginx que edita `toggle_authelia.py` (lo lee del `.env` como texto, no con `getenv`) | ruta | `/etc/nginx/conf.d/vivaro.conf` | `/etc/nginx/conf.d/<nombre>.conf` | No | No | Sí | `utils/toggle_authelia.py` | FNC-001, 2026-10-13 | Vigente |

### Presentes en `.env.example` pero no leídas por el código

| Variable | Observación | Estado |
|---|---|---|
| `FLASK_APP` | Solo la usa el CLI `flask` (`flask run`); `run.py` no la necesita. | Vigente (CLI) |
| `FLASK_ENV` | Obsoleta en Flask 3; no tiene efecto. | Sin uso |
| `PORT_APP` | `run.py` fija el puerto 5001 y Gunicorn usa `--bind` en la unidad systemd; la variable no se lee. | Sin uso |
| `AUTHELIA_SSO_URL` | Ningún archivo la lee. | Sin uso |
| `DEBUG_AUTH` | Ningún archivo la lee. | Sin uso |

## Variables de entorno — frontend (Next.js)

| Variable | Propósito | Tipo | Por defecto en código | Ejemplo | Obligatoria | Sensible | En `.env.example` | Dónde se usa | Alta | Estado |
|---|---|---|---|---|---|---|---|---|---|---|
| `BACKEND_URL` | URL del backend para los `rewrites` de dev y las llamadas desde el servidor (SSR) | URL | `lib/api.ts`: `http://localhost:5001` (constante `BACKEND_URL_POR_DEFECTO`, FNC-069); `next.config.ts`: IP de loopback (deuda, FNC-005) | `http://localhost:5001` | No | No | Sí | `frontend/next.config.ts`, `frontend/src/lib/api.ts` | FNC-001, 2026-10-13 | Vigente |
| `NEXT_PUBLIC_ACCESS_MOCKS` | `1` = el cliente del gestor de accesos (`lib/access/`) devuelve los datos simulados de los contratos; se ignora con `NODE_ENV=production` | `1` o vacío | vacío (apagado) | `1` | No | No | Sí | `frontend/src/lib/access/client.ts` | FNC-069, 2026-10-19 | Vigente (temporal: se retira al integrar el backend) |
| `NODE_ENV` | Modo de ejecución | `production` | — | `production` | Sí (prod) | No | No (lo fija la unidad systemd) | `deploy/frontend.service.tmpl` | FNC-001, 2026-10-13 | Vigente |
| `PORT` | Puerto de `server.js` | entero | 3000 | `3000` | Sí (prod) | No | No (unidad systemd) | `deploy/frontend.service.tmpl` | FNC-001, 2026-10-13 | Vigente |
| `HOSTNAME` | Interfaz de escucha de `server.js` (solo loopback) | dirección de loopback | — | loopback | Sí (prod) | No | No (unidad systemd) | `deploy/frontend.service.tmpl` | FNC-001, 2026-10-13 | Vigente |

Única `NEXT_PUBLIC_*`: `NEXT_PUBLIC_ACCESS_MOCKS` (no es secreta; se incrusta en el build). El navegador usa rutas relativas.

## Variables de los scripts de despliegue

Se pasan al invocar `deploy/preflight.sh` o `deploy/install.sh`; no van en `.env`.

| Variable | Script | Propósito | Por defecto | Sensible |
|---|---|---|---|---|
| `APP_NAME` | preflight | Nombre del despliegue (equivale a `--name`) | `nexus` | No |
| `API_PORT` | preflight | Puerto del backend a comprobar | `5001` | No |
| `WEB_PORT` | preflight | Puerto del frontend a comprobar | `3000` | No |
| `SVC_USER` | preflight | Cuenta de servicio a comprobar | quien invoca sudo | No |
| `CREATE_USER` | install | `1` crea la cuenta de servicio (equivale a `--create-user`) | `0` | No |
| `PROXY_URL` (o `HTTPS_PROXY`/`HTTP_PROXY` en mayúsculas o minúsculas) | ambos | Proxy de salida para dnf, pip y npm | ninguno | **Sí** si lleva credenciales |
| `NO_PROXY` / `no_proxy` | ambos | Excepciones del proxy | localhost y loopback | No |

## Plantilla anterior retirada

La versión inicial de este registro (estructura genérica) listaba `APP_ENV`, `LOG_DIR`, `LOG_LEVEL`, `DB_PASSWORD` y `NEXT_PUBLIC_API_URL`. **Ninguna la lee el código**: la contraseña de BD se llama `DB_PASS` y el frontend no usa `NEXT_PUBLIC_API_URL`. Se dan de baja en HISTORIAL.md. `APP_ENV` se reactivó en FNC-077 (2026-10-19), ahora leída por `auth/acceso_local.py` (fila en la tabla de arriba).

## Constantes de configuración en el código

| Constante | Propósito | Valor | Unidad | Dónde se define | Alta (tarea, fecha) | Estado |
|---|---|---|---|---|---|---|
| `PERMANENT_SESSION_LIFETIME` | Duración de la sesión | 7 | días | `app/__init__.py` | FNC-001, 2026-10-13 | Vigente |
| `SESSION_COOKIE_NAME` | Nombre de la cookie | `nexus_session` | — | `app/__init__.py` | FNC-001, 2026-10-13 | Vigente |
| `WTF_CSRF_TIME_LIMIT` | Caducidad del token CSRF | sin límite | — | `app/__init__.py` | FNC-001, 2026-10-13 | Vigente |
| `pool_recycle` | Reciclado de conexiones de BD | 3600 | s | `app/__init__.py` | FNC-001, 2026-10-13 | Vigente |
| `SQLITE_URI_POR_DEFECTO` | BD SQLite cuando `DB_ENGINE` no es `mysql` (en `instance/`) | `sqlite:///nexus.db` | — | `app/utils/uri_bd.py` | FNC-001, 2026-10-13; constante con nombre FNC-039 | Vigente |
| `CARPETA_INSTANCIA` | Dónde resuelve Alembic la ruta SQLite relativa (igual que Flask) | `instance/` de la raíz | — | `migrations/env.py` | FNC-039, 2026-10-14 | Vigente |
| `MAX_LOGO_BYTES` | Tamaño máximo del logo del portal | 512 | KB | `app/modules/api/admin.py` | FNC-001, 2026-10-13 | Vigente |
| `ALLOWED_LOGO_TYPES` | Tipos de imagen del logo | png, jpeg, gif, webp, svg+xml | — | `app/modules/api/admin.py` | FNC-001, 2026-10-13 | Vigente |
| `PURGE_MIN_DAYS` | Mínimo de días de inactividad para purgar | 7 | días | `app/modules/api/crud.py` | FNC-001, 2026-10-13 | Vigente |
| `ASSIGNABLE_ROLES` / `RESERVED_NAMES` | Roles asignables por admin de área / identificadores reservados | `usuario`, `admin_area` / `admin` | — | `app/modules/api/crud.py` | FNC-001, 2026-10-13 | Vigente |
| Intervalo de refresco | Límites de `pref_refresh_interval` | 15–3600 | s | `app/modules/api/crud.py` | FNC-001, 2026-10-13 | Vigente |
| `INTERVALO_POLLING_MIN_S` / `INTERVALO_POLLING_MAX_S` / `INTERVALO_POLLING_POR_DEFECTO_S` | Límites y valor por defecto del polling web (espejo de `pref_refresh_interval`; el máximo es también el tope del *backoff*) | 15 / 3600 / 60 | s | `frontend/src/lib/use-polling.ts` | FNC-071, 2026-10-19 | Vigente |
| `JITTER_POLLING` | Fracción máxima restada a la espera tras un error | 0.1 | fracción | `frontend/src/lib/use-polling.ts` | FNC-071, 2026-10-19 | Vigente |
| `MAX_LENGTH` | Longitud máxima de nombres visibles | 100 | caracteres | `app/utils/naming.py` | FNC-001, 2026-10-13 | Vigente |
| `ACTOR_SISTEMA` | Valor de `AuditLog.user` cuando actúa el sistema | `sistema` | — | `app/modules/audit/events.py` | FNC-001 (`SYSTEM`), 2026-10-13; constante con nombre FNC-047 | Vigente |
| `IP_INTERNA` | IP de auditoría fuera de una petición | `INTERNAL` | — | `app/modules/audit/services.py` | FNC-001, 2026-10-13; constante con nombre FNC-047 | Vigente |
| `FRAGMENTOS_SENSIBLES` / `VALOR_OMITIDO` / `CAMPOS_NOMBRE_PAR`, `CAMPO_VALOR_PAR` | Claves que no se guardan en antes/después de la auditoría / valor que las sustituye / forma par nombre-valor | password, pass, pwd, hash, token, secret, key, otp, session, cookie, authorization, header, clave… / `[omitido]` / `key`, `name` y `value` | — | `app/modules/audit/sanitizar.py` | FNC-047, 2026-10-14 | Vigente |
| `AL_BORRAR_REFERENCIA` | Acción de las FK de `audit_logs` al borrar usuario, área o plataforma | `SET NULL` (sin cascada) | — | `app/modules/audit/models.py` | FNC-047, 2026-10-14 | Vigente |
| Largos de `audit_logs` | `user` / `action` / `target` | 255 / 150 / 255 (antes 100 / 50 / 100) | caracteres | `app/modules/audit/models.py` | FNC-047, 2026-10-14 | Vigente |
| `LIMITE_POR_DEFECTO` / `AUDIT_PAGE_SIZE_MAX` | Registros de `GET /audit` sin `page` (`?limit=`, cliente actual) | 100 por defecto, máx. 500 | registros | `app/modules/audit/parametros.py` | FNC-001, 2026-10-13 (`api/routes.py`); constantes con nombre FNC-060 | Vigente |
| `POR_PAGINA_POR_DEFECTO` / `POR_PAGINA_MAX` / `LARGO_MAX_BUSQUEDA` / `RANGO_MAX_DIAS` / `MAX_DIGITOS_ENTERO` | Auditoría paginada: `per_page` por defecto y tope / largo de `q` / rango `from`–`to` / dígitos de ids y página | 25 / 100 / 100 / 366 / 9 | registros / caracteres / días / dígitos | `app/modules/audit/parametros.py` | FNC-060, 2026-10-19 | Vigente |
| Límite de notificaciones | Notificaciones in-app devueltas | 50 | registros | `app/modules/api/admin.py` | FNC-001, 2026-10-13 | Vigente |
| `LIMITE_BUSQUEDA_PERSONAS` / `MIN_BUSQUEDA`, `MAX_BUSQUEDA` | Búsqueda en directorio: resultados máximos / caracteres del texto | 50 / 2–64 | — | `app/modules/directory/ldap_client.py` / `app/modules/directory/api.py` | FNC-001, 2026-10-13 (`api/admin.py`); constantes con nombre y máximo 64 en FNC-043 | Vigente |
| Timeouts | SMTP (el de LDAP es `LDAP_TIMEOUT_SECONDS`) | 10 | s | `notifications/services.py` | FNC-001, 2026-10-13; LDAP retirado de `auth/services.py` en FNC-043 | Vigente |
| `ESQUEMAS_PERMITIDOS` | Esquemas de `LDAP_URL` y puerto por defecto | `ldaps` 636 / `ldap` 389 (StartTLS) | — | `app/modules/directory/configuracion.py` | FNC-040, 2026-10-14 | Vigente |
| `LIMITE_BUSQUEDA_USUARIO` | Entradas pedidas al buscar una persona (2 = detectar duplicados) | 2 | entradas | `app/modules/directory/ldap_client.py` | FNC-040, 2026-10-14 | Vigente |
| `ATRIBUTOS_PERFIL` | Atributos de perfil leídos de la persona | `mail`, `cn`, `displayName` | — | `app/modules/directory/ldap_client.py` | FNC-040, 2026-10-14 | Vigente |
| `CLAVES_POR_PLANTILLA` | Lista blanca de variables de cada plantilla del gestor (SEC-MAIL-02) | ver el código | — | `app/modules/notifications/access_notifications.py` | FNC-048, 2026-10-15 | Vigente |
| `OPERACIONES` / `SEPARADOR_DESTINATARIOS` / `PATRON_CORREO` | Operaciones del aviso de fallo / separador de `To` (un envío por evento) / dirección aceptada (sin espacios, comas ni saltos) | `otorgar`, `revocar` / `, ` / `x@y` | — | `app/modules/notifications/access_notifications.py` | FNC-048, 2026-10-15 | Vigente |
| `PATRON_VARIABLE` / `PATRON_SALTO_DE_LINEA` | `{clave}` de una plantilla / CR-LF quitados del asunto (SEC-MAIL-01) | `\{(\w+)\}` / `[\r\n]+` | — | `app/modules/notifications/services.py` | FNC-048, 2026-10-15 | Vigente |
| `CLASES_GRUPO_CON_MIEMBRO_OBLIGATORIO` | Clases de grupo que no pueden quedar sin miembros | `groupOfNames`, `groupOfUniqueNames` | — | `app/modules/directory/writer.py` | FNC-041, 2026-10-15 | Vigente |
| `ATRIBUTO_NOMBRE_COMPLETO`, `ATRIBUTO_APELLIDO`, `ATRIBUTO_NOMBRE`, `ATRIBUTO_CORREO` | Atributos que se llenan en el alta de cuenta | `cn`, `sn`, `givenName`, `mail` | — | `app/modules/directory/writer.py` | FNC-041, 2026-10-15 | Vigente |
| `PATRON_IDENTIFICADOR`, `PATRON_CORREO` | Formato de uid y correo en el alta de cuenta | `[a-z0-9._-]+` / `x@y.z` sin espacios | — | `app/modules/directory/writer.py` | FNC-041, 2026-10-15 | Vigente |
| `ERRORES_TRANSITORIOS` | Errores de `ldap3` que se reintentan | red, espera, `busy`, `unavailable`, límites de tiempo/administración | — | `app/modules/directory/errors.py` | FNC-041, 2026-10-15 | Vigente |
| `MENSAJE_CREDENCIALES` | Respuesta única de login fallido (directorio y local) | `Credenciales incorrectas.` | — | `app/modules/auth/services.py` | FNC-042, 2026-10-15 | Vigente |
| `ORIGEN_DIRECTORIO` | `auth_source` de las cuentas del login de directorio | `ldap` | — | `app/modules/auth/services.py` | FNC-042, 2026-10-15 | Vigente |
| `ORIGENES_VINCULADOS` / `MOTIVO_CONFLICTO`, `MOTIVO_DESACTIVADA` | Orígenes que el directorio y el SSO pueden usar / motivos auditados del bloqueo | `ldap`, `sso` / `cuenta_local_en_conflicto`, `cuenta_desactivada` | — | `app/modules/auth/services.py` | FNC-042, 2026-10-15 | Vigente |
| `ESQUEMAS_URL` / `URL_MAX` / `CARACTER_DEL` | Esquemas aceptados en `direct_link` y `logo_url` (sin credenciales ni IP) / largo máximo / carácter rechazado | `https` / 255 | caracteres | `app/modules/platforms/validacion.py` | FNC-046, 2026-10-19 | Vigente |
| `NOMBRE_MIN/MAX`, `DESCRIPCION_MIN/MAX` | Largo del nombre y la descripción de una plataforma | 2–100 / 1–1000 | caracteres | `app/modules/platforms/validacion.py` | FNC-046, 2026-10-19 | Vigente |
| `TIPOS_INTEGRACION` / `LARGO_DN` | Tipos de integración / largo de los DN de grupo | `ldap`, `conector` / 512 | — / caracteres | `app/modules/platforms/tipos.py` | FNC-046, 2026-10-19 | Vigente |
| `MARCADORES_PLANTILLA_GRUPO` / `MARCADORES_OBLIGATORIOS_GRUPO` | Marcadores de `LDAP_PLATFORM_GROUP_TEMPLATE` | `plataforma`, `area`, `nivel` / `plataforma`, `nivel` | — | `app/modules/directory/configuracion.py` | FNC-046, 2026-10-19 | Vigente |
| `MARGEN_RESERVA_SEGUNDOS` | Margen sobre el tiempo de espera del intento para dar por vencida una reserva | 30 | s | `app/modules/provisioning/configuracion.py` | FNC-049, 2026-10-19 | Vigente |
| `MAX_INTENTOS`, `BACKOFF_BASE_SEGUNDOS`, `BACKOFF_MAX_SEGUNDOS`, `TIEMPO_INTENTO_SEGUNDOS`, `INTERVALO_BARRIDO_SEGUNDOS` | (por defecto, mínimo, máximo) de las `PROVISIONING_*` | ver la fila de cada variable | — | `app/modules/provisioning/configuracion.py` | FNC-049, 2026-10-19 | Vigente |
| `FACTOR_BACKOFF` | Base del crecimiento exponencial (*equal jitter*) | 2 | — | `app/modules/provisioning/reintentos.py` | FNC-049, 2026-10-19 | Vigente |
| `LOTE_BARRIDO` | Trabajos enviados a la cola por barrido | 100 | trabajos | `app/modules/provisioning/worker.py` | FNC-049, 2026-10-19 | Vigente |
| `TIEMPO_ESPERA_REDIS_SEGUNDOS` | Conexión y lectura de Redis del worker (RQ sube la lectura para su espera) | 5 | s | `app/modules/provisioning/queue.py` | FNC-049, 2026-10-19 | Vigente |
| `TIEMPO_ESPERA_REDIS_WEB_SEGUNDOS` | Conexión y envío a Redis al despertar al worker desde la app web (dentro del commit) | 0,5 | s | `app/modules/provisioning/queue.py` | FNC-049, 2026-10-19 | Vigente |
| `ATRIBUTOS_CALLBACK` | *Callbacks* de RQ que hacen rechazar un mensaje | `_success_callback_name`, `_failure_callback_name`, `_stopped_callback_name` | — | `app/modules/provisioning/worker.py` | FNC-049, 2026-10-19 | Vigente |
| `SERIALIZADOR_RQ` | Mensajes RQ en JSON (sin pickle) en la cola y el worker | `JSONSerializer` | — | `app/modules/provisioning/queue.py` | FNC-049, 2026-10-19 | Vigente |
| `TTL_RESULTADO_RQ` | RQ no guarda resultados (el estado vive en la BD) | 0 | s | `app/modules/provisioning/queue.py` | FNC-049, 2026-10-19 | Vigente |
| `LARGO_ERROR`, `LARGO_CLAVE_IDEMPOTENCIA` | Error de la bitácora truncado / largo de la clave | 500 / 100 | caracteres | `app/modules/provisioning/tipos.py` | FNC-049, 2026-10-19 | Vigente |
| `VARIABLES_SECRETAS`, `LARGO_MINIMO_SECRETO`, `MENSAJES` | Valores que se borran del error, largo mínimo buscado y catálogo de mensajes de la bitácora (SEC-CON-10) | `LDAP_BIND_PASSWORD`, `REDIS_PASS`, `DB_PASS`, `SMTP_PASSWORD`, `SECRET_KEY` / 4 / ver el código | — | `app/modules/provisioning/saneo.py` | FNC-049, 2026-10-19 | Vigente |
| Gunicorn | Workers / timeout / puerto | 4 / 120 s / 5001 | — | `deploy/backend.service.tmpl` | FNC-001, 2026-10-13 | Vigente |
| Puerto del backend en dev | Puerto de `run.py` | 5001 | — | `run.py` | FNC-001, 2026-10-13 | Vigente |
| `client_max_body_size` | Tamaño máximo de petición en nginx | 64 | MB | `deploy/nginx.conf.tmpl` | FNC-001, 2026-10-13 | Vigente |

## Configuración en la BD (obsoleta)

| Campo | Propósito anterior | Estado | Motivo | Tarea, fecha |
|---|---|---|---|---|
| `auth_config.ldap_pass` | Contraseña de bind LDAP en claro | **Obsoleta**: la migración 0004 la vacía y el modelo rechaza escribirla | Credencial fuera de la BD (SEG-08, SEC-LDAP-11); la fuente es `LDAP_BIND_PASSWORD` | FNC-043, 2026-10-18 |
| `auth_config.ldap_host`, `ldap_port`, `ldap_ssl`, `ldap_base_dn`, `ldap_user`, `ldap_user_attr` | Conexión y esquema LDAP editables en Ajustes | **Obsoletos**: nada los lee ni los edita la API; solo viajan en el respaldo | ADR-004: toda la configuración va en `LDAP_*` | FNC-043, 2026-10-18 |
| `auth_config.ldap_group_admin`, `ldap_group_user`, `ldap_role_mappings` | Mapeo de grupos LDAP a roles | **Obsoletos**: el directorio no asigna rol | RF-04, SEG-10 (FNC-042) | FNC-042, 2026-10-15; API retirada en FNC-043 |

## Tokens de diseño

Definidos en `frontend/src/styles/tokens.css` (tema claro en `:root, html.light`; oscuro en `@media (prefers-color-scheme: dark)` y `html.dark`) y mapeados a utilidades en `frontend/tailwind.config.ts`. El inventario detallado por token queda pendiente de la auditoría de accesibilidad y estandarización.

| Token | Rol | Valor tema claro | Valor tema oscuro | Archivo | Alta (tarea, fecha) | Estado |
|---|---|---|---|---|---|---|
| `--color-primary-text` | Texto de marca (enlaces, menú activo, pestaña de Ajustes) | `29 78 216`; emerald `4 120 87`; rose `190 18 60` | `96 165 250` (SO y `html.dark`); obsidian `161 161 170`; violet `167 139 250` | `tokens.css` | DIS-001, 2026-10-19 | Vigente |
| `--color-brand-text` | Texto en color brand | `67 56 202`; emerald `4 120 87`; rose `190 18 60` | `129 140 248`; obsidian `161 161 170`; violet `167 139 250` | `tokens.css` | DIS-001, 2026-10-19 | Vigente (sin consumidor aún) |
| `--color-accent-text` | Texto en color accent | `124 58 237`; emerald `15 118 110`; rose `190 18 60` | `167 139 250`; obsidian `250 204 21`; violet `167 139 250` | `tokens.css` | DIS-001, 2026-10-19 | Vigente (sin consumidor aún) |
| `--color-accent-sky-text` | Texto en color sky | `14 116 144`; emerald `15 118 110`; rose `190 18 60` | `6 182 212`; obsidian `161 161 170`; violet `167 139 250` | `tokens.css` | DIS-001, 2026-10-19 | Vigente (sin consumidor aún) |
| `--color-accent-peach-text` | Texto en color peach/KPI | `180 83 9`; emerald `180 83 9`; rose `194 65 12` | `245 158 11`; obsidian `250 204 21`; violet `251 146 60` | `tokens.css` | DIS-001, 2026-10-19 | Vigente (sin consumidor aún) |
| `--color-success-text` | Texto de éxito ("Guardado", notificación success) | `4 120 87` (todos los claros) | `110 231 183` (SO, `html.dark`, obsidian, violet) | `tokens.css` | DIS-002, 2026-10-19 | Vigente |
| `--color-error-text` | Texto de error (`ErrorNote`, errores por campo, Eliminar) | `185 28 28` | `252 165 165` | `tokens.css` | DIS-002, 2026-10-19 | Vigente |
| `--color-warning-text` | Texto de advertencia y estrella de favorito | `146 64 14` | `252 211 77` | `tokens.css` | DIS-002, 2026-10-19 | Vigente |
| `--color-info-text` | Texto informativo | `29 78 216` | `147 197 253` | `tokens.css` | DIS-002, 2026-10-19 | Vigente (sin consumidor aún) |
| `--color-error` | Relleno/tinte de error (utilidad `error`) | `239 68 68` (todos) | ídem | `tokens.css` | DIS-002, 2026-10-19 (antes literal en `tailwind.config.ts`) | Vigente |
| `--color-info` | Relleno/tinte informativo (utilidad `info`) | `59 130 246` (todos) | ídem | `tokens.css` | DIS-002, 2026-10-19 (antes literal) | Vigente (sin consumidor aún) |
| `--color-warning` | Relleno/tinte de advertencia (utilidad `warning`) | `245 158 11` (todos) | ídem | `tokens.css` | FNC-001 (heredado); utilidad DIS-002 | Vigente |
| `--color-ntf-text-subject`, `--color-status-active` | Asunto de notificación / estado activo (sin consumidor en React) | emerald `4 120 87`; rose `190 18 60`; resto sin cambio | sin cambio | `tokens.css` | FNC-001 (heredado); emerald/rose DIS-002 | Vigente |
| `--color-primary-solid` | Relleno de marca con texto encima (pestaña activa) | `var(--color-primary)`; emerald `4 120 87`; rose `225 29 72` | `var(--color-primary)`; violet `124 58 237` | `tokens.css` | DIS-001, 2026-10-19 | Vigente |
| `--color-on-primary` | Texto sobre `--color-primary-solid` | `255 255 255` | `255 255 255`; obsidian `9 9 11` | `tokens.css` | DIS-001, 2026-10-19 | Vigente |
| `--color-panel-header-text` | Título de modales y cabeceras de tabla | `30 58 138` | `96 165 250` (SO, `html.dark`); obsidian `212 212 216`; violet `167 139 250` | `tokens.css` | FNC-001 (heredado); por tema DIS-001 | Vigente |
| `--badge-<tono>-bg` / `-text` (8 tonos) | Insignias `.nx-badge-*` | tinte 0.1 + tono 700 | tinte 0.15 + tono 300-400 (ahora también SO oscuro, obsidian, violet; mismos valores repetidos en 4 bloques: observación, sin tarea) | `tokens.css` | FNC-001 (heredado); por tema DIS-001 | Vigente |
| `--color-header-bg` | Fondo del header | `#2563eb`; emerald `#047857`; rose `#e11d48` | `#1e3a8a`; obsidian `#18181b`; violet `#2e1065` | `tokens.css` | FNC-001; valores emerald/rose DIS-001 | Vigente |
| `--color-tab-active-bg` / `-text` | Pestaña activa | `var(--color-primary-solid)` / `var(--color-on-primary)` | ídem | `tokens.css` | FNC-001 (heredado); DIS-001 | Vigente |
