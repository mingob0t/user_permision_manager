# Entornos

> Línea base documentada en FNC-001 (2026-10-13) a partir de `deploy/` (`README.md`, `preflight.sh`, `install.sh`, `backend.service.tmpl`, `frontend.service.tmpl`, `nginx.conf.tmpl`). Sin direcciones IP: los dominios y hosts salen de la configuración.

| Entorno | Propósito | Dominio (nombre de host, nunca IP) | Base de datos | Quién despliega | Cómo se despliega |
|---|---|---|---|---|---|
| Desarrollo | Trabajo local de cada agente o persona | `localhost` (backend en el puerto 5001, frontend en el 3000) | MySQL local (o SQLite si `DB_ENGINE` no es `mysql`) | Cada desarrollador | `python run.py` + `npm run dev` (ver `docs/backend/README.md` y `docs/frontend/README.md`) |
| Pruebas (staging) | Validación previa a producción | _Pendiente de definir_ (punto abierto en `docs/REQUERIMIENTOS.md`) | MySQL | _Pendiente_ | `deploy/preflight.sh` + `deploy/install.sh` |
| Producción | Servicio a usuarios | _Pendiente de definir_ | MySQL | _Pendiente_ | `deploy/preflight.sh` + `deploy/install.sh` |

## Topología de un servidor (staging y producción)

```text
cliente ──HTTPS 443──> nginx ──(auth_request)──> Authelia (existente)
                         │
                         ├── /api/ y /auth/ ──> <nombre>-backend  (Gunicorn, loopback:5001)
                         └── /  y /_next/static/ ──> <nombre>-frontend (node server.js, loopback:3000)

<nombre>-backend ──> MySQL (por nombre de host) · Redis opcional · OpenLDAP (lectura; escritura acotada, FNC-041) · SMTP
<nombre>-worker  ──> MySQL · Redis (obligatorio, con contraseña) · OpenLDAP (escritura acotada) · SMTP   (FNC-049; unidad FNC-067, no escucha)
```

- Ambos servicios bajo **el mismo dominio**: la cookie de sesión de Flask llega al frontend sin CORS.
- Los dos puertos escuchan **solo en loopback**. El backend solo acepta las cabeceras `Remote-*` desde `TRUSTED_PROXIES`, y nginx las borra si las manda el cliente.
- El bloque `auth_request` de Authelia viene **comentado** en `nginx.conf.tmpl`; hay que activarlo al conectar Authelia. Los certificados TLS también vienen comentados.

## Sistema operativo y requisitos

Rocky Linux 8 (familia RHEL 8). Requisitos mínimos en `docs/REQUERIMIENTOS.md` §7. `install.sh` no instala MySQL, Redis, Authelia ni OpenLDAP: se consideran servicios existentes.

## Preflight (`deploy/preflight.sh`)

Evaluación previa que **no modifica nada**; termina con código 1 si hay algo bloqueante. Comprueba:

1. Distribución (RHEL 8 compatible; RHEL 9 con aviso) y arquitectura.
2. Privilegios (root o sudo).
3. Recursos: 2 GB de disco y 1 GB de RAM.
4. Python ≥ 3.11 con `venv` (busca intérpretes ya instalados).
5. Node `^22.13.0 || >=24.0.0` (el rango de `engines` de `frontend/package.json`; FNC-073) y npm, y disponibilidad del módulo `nodejs:22`.
6. Cabeceras de compilación y salida a Internet (directa o por `PROXY_URL`, con credenciales enmascaradas).
7. Conectividad real a la BD y a Redis leyendo `DB_HOST`/`DB_PORT`/`REDIS_HOST`/`REDIS_PORT` del `.env`, y que `SECRET_KEY` esté definida. Desde FNC-067 Redis es **bloqueante**: no responde, `REDIS_HOST` es una IP o `REDIS_PASS` está vacía → `FALTA` (el worker no arrancaría).
8. Puertos 5001 y 3000 libres.
9. nginx (`nginx -t`, `/etc/nginx/conf.d`).
10. SELinux (`httpd_can_network_connect`) y firewalld (`https`).
11. Nombre del despliegue (`APP_NAME`), cuenta de servicio (`SVC_USER`) y estado del proyecto (venv y `node_modules` previos).

## Instalación (`deploy/install.sh`)

Idempotente; se repite para actualizar. Opciones: `--name`, `--prefix` (por defecto `/opt/<nombre>`), `--logdir` (por defecto `/var/log/<nombre>`), `--title`, `--user`, `--create-user`, `--domain`, `--python`, `--proxy`, `--no-proxy`, `--skip-packages`.

1. Paquetes del sistema: Python 3.11 si no hay uno válido, Node 22 (AppStream o NodeSource) si el presente no cumple `^22.13.0 || >=24.0.0` (con `--skip-packages` solo lo comprueba), nginx y cabeceras de compilación.
2. Cuenta de servicio: usa la indicada (o quien invoca sudo); solo la crea con `--create-user`.
3. Copia del proyecto al prefijo; el `.env` queda legible solo por la cuenta de servicio.
4. Backend: `venv` y `pip install -r requirements.txt`.
5. Frontend: `npm ci`, `npm run build` y copia de estáticos a `.next/standalone`.
6. Unidades systemd a partir de las plantillas: backend, frontend y worker (`reset-failed` del worker antes de `enable --now`).
7. nginx en `/etc/nginx/conf.d/<nombre>.conf`, SELinux y firewalld.

**No aplica migraciones**: se ejecuta `venv/bin/alembic upgrade head` a mano antes de reiniciar (ver `docs/backend/README.md` §7). Los SQL sueltos `utils/migrations/` se retiraron en FNC-028 (la línea base `0001` ya los incluye).

## Servicios systemd

| Unidad | Proceso | Escucha | Detalles |
|---|---|---|---|
| `<nombre>-backend` | `venv/bin/gunicorn run:app`, 4 workers, timeout 120 s | loopback:5001 | `EnvironmentFile=<prefijo>/.env`; logs `access.log` y `error.log` en el directorio de registros; `After=mysql.service`; endurecido (`ProtectSystem=strict`, `ProtectHome`, `PrivateTmp`, `NoNewPrivileges`; solo escribe en el directorio de registros). |
| `<nombre>-frontend` | `node server.js` en `frontend/.next/standalone` | loopback:3000 | `NODE_ENV=production`, `PORT=3000`, `HOSTNAME` en loopback; depende del backend; mismo endurecimiento. |
| `<nombre>-worker` (FNC-067) | `venv/bin/flask --app run:app provisioning worker` (FNC-049) | no escucha | Misma cuenta y mismo `.env`; `After=` red, `mysql.service` y `redis.service`; `KillSignal=SIGTERM` (termina el intento en curso) y `TimeoutStopSec=630` (máximo de `PROVISIONING_ATTEMPT_TIMEOUT_SECONDS` + 30 s); `Restart=on-failure` cada 30 s, máx. 10 en 15 min y luego `failed`; registros en journald; endurecido como el backend más `PrivateDevices`, kernel y cgroups protegidos, sin capacidades y solo `AF_UNIX`/`AF_INET`/`AF_INET6`. Sin `REDIS_PASS` o sin Redis sale con código 1. |

## Promoción de un cambio

1. Rama de la tarea → revisión (`revisor`, `tester` y, si aplica, `auditor-seguridad`) → merge aprobado por el usuario.
2. Despliegue a **pruebas**: `preflight.sh`, `install.sh` (repetible), migraciones pendientes a mano, reinicio de backend y worker (`systemctl restart <nombre>-backend <nombre>-worker`) y verificación.
3. Despliegue a **producción** con la versión etiquetada (ver [RELEASES.md](RELEASES.md)).

## Diferencias entre entornos

Qué variables cambian por entorno. El valor de cada una está en `docs/configuracion/VARIABLES.md`, nunca aquí.

| Variable | Desarrollo | Staging / producción |
|---|---|---|
| `FRONTEND_URL` | URL del frontend local (puerto 3000) | vacía (mismo dominio) |
| `BASE_URL` | URL local | `https://<dominio del entorno>` |
| `BACKEND_URL` (frontend) | backend local | no se usa (enruta nginx) |
| `AUTHELIA_ENABLED` | normalmente `false` | `true` al conectar Authelia |
| `APP_ENV` (FNC-077) | `development` | `staging` / `production` (o vacía) |
| `LOGIN_LOCAL_TODAS_LAS_CUENTAS` (FNC-077) | `false`; `true` solo para la PoC sin Authelia | `false` (se ignora: `APP_ENV` no es `development`) |
| `DB_*`, `SECRET_KEY`, `SMTP_*` | `.env` local | `.env` del servidor con secretos de Vaultwarden |
| `LDAP_*` (FNC-040) | `.env` local; vacío = directorio inactivo; `LDAP_BIND_PASSWORD_REF` no se admite | `.env` del servidor; contraseña de bind con `LDAP_BIND_PASSWORD_REF` (ítem de Vaultwarden, FNC-068) o, como alternativa, `LDAP_BIND_PASSWORD` inyectada (nunca las dos). Con CA interna: copiar su PEM al servidor y apuntar `LDAP_CA_CERT_FILE` (si no, la app no conecta: el certificado se valida) |
| `VAULTWARDEN_*` (FNC-068) | no se usan (`APP_ENV=development`: credenciales de conectores en `CONNECTOR_CREDENTIAL_*`) | `.env` del servidor (600): llave de API y contraseña maestra de la cuenta de servicio, solo lectura de una colección; las pone una persona. Ver [SECRETOS.md](SECRETOS.md) |
| `REDIS_PASS` (FNC-049) | `.env` local; obligatoria para el worker (Redis local con `requirepass`) | Vaultwarden `pokemon/<entorno>/REDIS_PASS`; Redis con `requirepass` y solo en loopback (`REDIS_HOST=localhost`, SEC-CFG-08); remoto solo como excepción con TLS, hoy no soportado por la app (FNC-067) |
| `PROVISIONING_*` (FNC-049) | por defecto (o valores cortos para probar reintentos) | por defecto; ajustar solo con motivo en `HISTORIAL.md` |
| `LDAP_USER_OBJECT_CLASSES`, `LDAP_GROUP_PLACEHOLDER_MEMBER` (FNC-041) | `.env` local; vacías = `inetOrgPerson` / sin relleno | `.env` del servidor. El relleno es una entrada sin login ni contraseña, fuera de `LDAP_USERS_BASE_DN` (si no, la app no arranca) |

## Entrar en local sin Authelia (FNC-077)
- El login local solo admite la **cuenta de emergencia**: superadmin (`administrador`) con `auth_source=local`. En una BD local nueva es el usuario semilla `admin` (FNC-003 lo reemplazará por un comando explícito).
- Pantalla de login → acceso local → `admin` y su contraseña. Sin variables extra.
- Para entrar con **otras cuentas locales** (PoC): en el `.env` local `APP_ENV=development` y `LOGIN_LOCAL_TODAS_LAS_CUENTAS=true`, y reiniciar el backend. Así también se aceptan contraseñas en el alta y la edición de usuarios.
- Cualquier otro valor de `APP_ENV` (o vacío) ignora la bandera: en staging y producción solo entra la cuenta de emergencia.
- Las cuentas creadas sin contraseña (ya no reciben `nexus123`) no entran por login local: se les fija una con la bandera activa.

## ACL de OpenLDAP para la cuenta de servicio (FNC-041, SEC-LDAP-03)

Una sola cuenta (`LDAP_BIND_DN`) lee y escribe (decisión del dueño, 2026-10-15). La aplica el administrador del directorio; el portal no la crea:

| Alcance | Permiso de la cuenta de servicio |
|---|---|
| Atributo de membresía (`LDAP_GROUP_MEMBER_ATTR`) de las entradas bajo `LDAP_GROUPS_BASE_DN` | `write` (agregar y quitar valores) |
| Resto de atributos de los grupos | `read` |
| Crear entradas hijas de `LDAP_USERS_BASE_DN` (`entry` + `children` de la OU) | `add` (sin `delete`) |
| `userPassword` en cualquier entrada | sin acceso (`none`) |
| Personas bajo `LDAP_USERS_BASE_DN` | `read` (búsqueda y perfil) |
| Todo lo demás del directorio | sin escritura |

- Ejemplo de forma (`olcAccess`; los DN reales los define el dueño): `to dn.subtree="<LDAP_GROUPS_BASE_DN>" attrs=member by dn.exact="<LDAP_BIND_DN>" write` y `to dn.base="<LDAP_USERS_BASE_DN>" attrs=children by dn.exact="<LDAP_BIND_DN>" write`.
- Verificar tras aplicarla: la cuenta no puede cambiar `userPassword` ni escribir fuera de esas OU.

## Requisitos del directorio OpenLDAP (FNC-042)
- `mail` único en todo el directorio.
- `mail` no editable por el propio usuario (ACL de OpenLDAP): las cuentas vinculadas del portal confían en él.
- Authelia usa el mismo OpenLDAP: una cuenta `sso` puede entrar por directorio y una `ldap` por SSO.

## Discrepancias de `deploy/README.md` (corregidas en FNC-035, 2026-10-27)

- Instalación manual: ahora apunta a las plantillas `*.service.tmpl` y `nginx.conf.tmpl` (antes, a `deploy/nexus-*.service` y `deploy/nginx-nexus.conf`, que no existen).
- `--no-proxy` y la tabla de servicios: sin direcciones numéricas (dominio y `loopback`).
