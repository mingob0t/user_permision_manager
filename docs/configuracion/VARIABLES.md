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
| `DB_ENGINE` | Motor de BD. `mysql` usa PyMySQL; cualquier otro valor cae a SQLite `nexus.db` | `mysql` / otro | `sqlite` | `mysql` | Sí (prod) | No | Sí | `app/__init__.py` | FNC-001, 2026-10-13 | Vigente |
| `DB_HOST` | Host de la BD | nombre de host | — (sin valor: URI inválida) | `localhost` | Sí con mysql | No | Sí | `app/__init__.py`, `deploy/preflight.sh` | FNC-001, 2026-10-13 | Vigente |
| `DB_PORT` | Puerto de la BD | entero | — en código; `3306` en preflight | `3306` | Sí con mysql | No | Sí | `app/__init__.py`, `deploy/preflight.sh` | FNC-001, 2026-10-13 | Vigente |
| `DB_NAME` | Nombre de la BD | texto | — | `pokemon_dev` | Sí con mysql | No | Sí (`admin_test`) | `app/__init__.py`, `deploy/preflight.sh` | FNC-001, 2026-10-13 | Vigente |
| `DB_USER` | Usuario de la BD | texto | — | `nexus` | Sí con mysql | No | Sí | `app/__init__.py` | FNC-001, 2026-10-13 | Vigente |
| `DB_PASS` | Contraseña de la BD | texto | — | — | Sí con mysql | **Sí** | Sí (vacía) | `app/__init__.py` | FNC-001, 2026-10-13 | Vigente |
| `REDIS_HOST` | Host de Redis | nombre de host | `localhost` | `localhost` | No (Redis sin uso funcional) | No | Sí | `app/__init__.py`, `deploy/preflight.sh` | FNC-001, 2026-10-13 | Vigente |
| `REDIS_PORT` | Puerto de Redis | entero | `6379` | `6379` | No | No | Sí | `app/__init__.py`, `deploy/preflight.sh` | FNC-001, 2026-10-13 | Vigente |
| `REDIS_PASS` | Contraseña de Redis | texto | ninguna | — | No | **Sí** | **No (faltante)** | `app/__init__.py` | FNC-001, 2026-10-13 | Vigente |
| `TZ_APP` | Zona horaria del proceso (fija `TZ`) | zona IANA | `TZ` o `America/Mexico_City` | `America/Mexico_City` | No | No | Sí | `app/__init__.py` | FNC-001, 2026-10-13 | Vigente |
| `TZ` | Respaldo de `TZ_APP` | zona IANA | `America/Mexico_City` | — | No | No | No (estándar del sistema) | `app/__init__.py` | FNC-001, 2026-10-13 | Vigente |
| `BASE_URL` | URL pública de la app para enlaces en correos y el retorno del cierre SSO | URL con dominio | En `api/auth.py`: la del host de la petición. En `auth/services.py`: **una IP literal** (deuda) | `http://localhost:5001` (dev) / `https://<dominio>` | Sí en prod | No | Sí | `api/auth.py`, `auth/services.py` | FNC-001, 2026-10-13 | Vigente |
| `FRONTEND_URL` | Destino de las redirecciones de rutas heredadas y del login sin sesión | URL o vacío (mismo dominio) | vacío | `http://localhost:3000` (dev) / vacío (prod) | No | No | Sí | `app/__init__.py`, rutas heredadas de `auth`, `core`, `audit`, `settings`, `notifications`, `users`, `areas` | FNC-001, 2026-10-13 | Vigente |
| `AUTHELIA_ENABLED` | Activa el SSO por cabeceras | `true` / `false` | `false` | `false` | No | No | Sí | `api/auth.py`, `utils/toggle_authelia.py` | FNC-001, 2026-10-13 | Vigente |
| `AUTHELIA_SLO_URL` | URL de cierre de sesión de Authelia | URL | ninguna | `https://<host de authelia>/logout` | Sí si SSO | No | Sí | `api/auth.py` | FNC-001, 2026-10-13 | Vigente |
| `AUTHELIA_HEADER_USER` | Cabecera con el correo del usuario | nombre de cabecera | `Remote-Email` | `Remote-Email` | No | No | Sí | `api/auth.py` | FNC-001, 2026-10-13 | Vigente |
| `AUTHELIA_HEADER_NAME` | Cabecera con el nombre visible | nombre de cabecera | `Remote-Name` | `Remote-Name` | No | No | Sí | `api/auth.py` | FNC-001, 2026-10-13 | Vigente |
| `AUTHELIA_HEADER_GROUPS` | Cabecera con los grupos | nombre de cabecera | `Remote-Groups` | `Remote-Groups` | No | No | Sí | `api/auth.py` | FNC-001, 2026-10-13 | Vigente |
| `AUTHELIA_GROUP_ADMIN` | Grupos (separados por coma) que dan rol `administrador` por SSO | lista CSV | `administrador` | `<grupo admins>` | Sí si SSO | No | Sí | `api/auth.py` | FNC-001, 2026-10-13 | Vigente |
| `TRUSTED_PROXIES` | Direcciones de origen autorizadas a inyectar cabeceras `Remote-*` (se compara con `remote_addr`, por eso son direcciones y no nombres de host; excepción justificada al lineamiento "sin IPs") | lista CSV | loopback IPv4 e IPv6 | loopback | No | No (seguridad crítica) | Sí | `api/auth.py` | FNC-001, 2026-10-13 | Vigente |
| `NOTIFY_USER_CREATED` | Envía la plantilla `usuario_creado` al dar de alta por LDAP o SSO | `true` / `false` | `true` | `true` | No | No | **No (faltante)** | `api/auth.py`, `auth/services.py` | FNC-001, 2026-10-13 | Vigente |
| `DEBUG_LDAP` | Log detallado de ldap3 en `logs/ldap_debug.log` | `true` / otro | desactivado | `false` | No | No (el log puede contener datos del directorio) | **No (faltante)** | `auth/services.py` | FNC-001, 2026-10-13 | Vigente |
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
| `BACKEND_URL` | URL del backend para los `rewrites` de dev y las llamadas desde el servidor (SSR) | URL | backend local en el puerto 5001, escrito como IP de loopback (deuda) | `http://localhost:5001` | No | No | **No (faltante)** | `frontend/next.config.ts`, `frontend/src/lib/api.ts` | FNC-001, 2026-10-13 | Vigente |
| `NODE_ENV` | Modo de ejecución | `production` | — | `production` | Sí (prod) | No | No (lo fija la unidad systemd) | `deploy/frontend.service.tmpl` | FNC-001, 2026-10-13 | Vigente |
| `PORT` | Puerto de `server.js` | entero | 3000 | `3000` | Sí (prod) | No | No (unidad systemd) | `deploy/frontend.service.tmpl` | FNC-001, 2026-10-13 | Vigente |
| `HOSTNAME` | Interfaz de escucha de `server.js` (solo loopback) | dirección de loopback | — | loopback | Sí (prod) | No | No (unidad systemd) | `deploy/frontend.service.tmpl` | FNC-001, 2026-10-13 | Vigente |

No hay variables `NEXT_PUBLIC_*`: el navegador usa rutas relativas.

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

La versión inicial de este registro (estructura genérica) listaba `APP_ENV`, `LOG_DIR`, `LOG_LEVEL`, `DB_PASSWORD` y `NEXT_PUBLIC_API_URL`. **Ninguna la lee el código**: la contraseña de BD se llama `DB_PASS` y el frontend no usa `NEXT_PUBLIC_API_URL`. Se dan de baja en HISTORIAL.md.

## Constantes de configuración en el código

| Constante | Propósito | Valor | Unidad | Dónde se define | Alta (tarea, fecha) | Estado |
|---|---|---|---|---|---|---|
| `PERMANENT_SESSION_LIFETIME` | Duración de la sesión | 7 | días | `app/__init__.py` | FNC-001, 2026-10-13 | Vigente |
| `SESSION_COOKIE_NAME` | Nombre de la cookie | `nexus_session` | — | `app/__init__.py` | FNC-001, 2026-10-13 | Vigente |
| `WTF_CSRF_TIME_LIMIT` | Caducidad del token CSRF | sin límite | — | `app/__init__.py` | FNC-001, 2026-10-13 | Vigente |
| `pool_recycle` | Reciclado de conexiones de BD | 3600 | s | `app/__init__.py` | FNC-001, 2026-10-13 | Vigente |
| `MAX_LOGO_BYTES` | Tamaño máximo del logo del portal | 512 | KB | `app/modules/api/admin.py` | FNC-001, 2026-10-13 | Vigente |
| `ALLOWED_LOGO_TYPES` | Tipos de imagen del logo | png, jpeg, gif, webp, svg+xml | — | `app/modules/api/admin.py` | FNC-001, 2026-10-13 | Vigente |
| `PURGE_MIN_DAYS` | Mínimo de días de inactividad para purgar | 7 | días | `app/modules/api/crud.py` | FNC-001, 2026-10-13 | Vigente |
| `ASSIGNABLE_ROLES` / `RESERVED_NAMES` | Roles asignables por admin de área / identificadores reservados | `usuario`, `admin_area` / `admin` | — | `app/modules/api/crud.py` | FNC-001, 2026-10-13 | Vigente |
| Intervalo de refresco | Límites de `pref_refresh_interval` | 15–3600 | s | `app/modules/api/crud.py` | FNC-001, 2026-10-13 | Vigente |
| `MAX_LENGTH` | Longitud máxima de nombres visibles | 100 | caracteres | `app/utils/naming.py` | FNC-001, 2026-10-13 | Vigente |
| Límite de auditoría | Registros devueltos por `/audit` | 100 por defecto, máx. 500 | registros | `app/modules/api/routes.py` | FNC-001, 2026-10-13 | Vigente |
| Límite de notificaciones | Notificaciones in-app devueltas | 50 | registros | `app/modules/api/admin.py` | FNC-001, 2026-10-13 | Vigente |
| Búsqueda en directorio | Resultados máximos / caracteres mínimos | 50 / 2 | — | `app/modules/api/admin.py` | FNC-001, 2026-10-13 | Vigente |
| Timeouts | Conexión LDAP / SMTP | 5 / 10 | s | `auth/services.py`, `notifications/services.py` | FNC-001, 2026-10-13 | Vigente |
| Gunicorn | Workers / timeout / puerto | 4 / 120 s / 5001 | — | `deploy/backend.service.tmpl` | FNC-001, 2026-10-13 | Vigente |
| Puerto del backend en dev | Puerto de `run.py` | 5001 | — | `run.py` | FNC-001, 2026-10-13 | Vigente |
| `client_max_body_size` | Tamaño máximo de petición en nginx | 64 | MB | `deploy/nginx.conf.tmpl` | FNC-001, 2026-10-13 | Vigente |

## Tokens de diseño

Definidos en `frontend/src/styles/tokens.css` (tema claro en `:root, html.light`; oscuro en `@media (prefers-color-scheme: dark)` y `html.dark`) y mapeados a utilidades en `frontend/tailwind.config.ts`. El inventario detallado por token queda pendiente de la auditoría de accesibilidad y estandarización.

| Token | Rol | Valor tema claro | Valor tema oscuro | Archivo | Alta (tarea, fecha) | Estado |
|---|---|---|---|---|---|---|
