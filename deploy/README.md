# Despliegue

Dos servicios tras un reverse proxy y un worker en segundo plano:

| Servicio | Escucha | Sirve |
|---|---|---|
| `<nombre>-backend` (Flask/Gunicorn) | loopback:5001 | API `/api/v1` |
| `<nombre>-frontend` (Next.js) | loopback:3000 | La interfaz |
| `<nombre>-worker` (`flask provisioning worker`, RQ) | no escucha | Otorgar y revocar accesos con reintentos (FNC-049, ADR-003) |

`<nombre>` lo define `--name` (por defecto `nexus`).

Nginx enruta `/api/` al backend y el resto al frontend. Ambos van
bajo el mismo dominio a propósito: así la cookie de sesión que emite Flask
llega al frontend sin CORS, y Authelia sigue siendo la autoridad de
autenticación.

## Instalación automatizada (Rocky/RHEL 8 o 9)

```bash
./deploy/preflight.sh                              # evaluación, no modifica nada
sudo ./deploy/install.sh --domain nexus.ejemplo.com
```

`preflight.sh` termina con código 1 si encuentra algo bloqueante. Revisa:

- Distribución y arquitectura
- Espacio (2 GB) y memoria (1 GB; `next build` es lo que más consume)
- Python **3.11 o superior** con `venv`, y Node `^22.13.0 || >=24.0.0` (FNC-073)
- Cabeceras de compilación (`gcc`, `openssl-devel`, `libffi-devel`), que
  `cryptography`, `cffi`, `bcrypt` y `PyNaCl` necesitan si no hay rueda
  binaria para la plataforma; PyMySQL y ldap3 son puro Python (FNC-125)
- Servicio de BD local detectado (`mysqld`, `mariadb` o `mysql`), o ninguno
  si la BD es remota
- Conectividad real con la base de datos y con Redis, leyendo `.env`; Redis
  es **obligatorio** (lo exige el worker), `REDIS_HOST` debe ser un nombre de
  host y `REDIS_PASS` debe tener valor (no se imprime)
- Que `SECRET_KEY` esté definida
- Puertos del backend y del frontend libres (por defecto 5001 y 3000; ver «Puertos»)
- nginx, SELinux (`httpd_can_network_connect`) y firewalld

`install.sh` acepta `--prefix` (por defecto `/opt/nexus`), `--user`,
`--domain`, `--python`, `--proxy`, `--no-proxy`, `--db-service`, `--web-port`,
`--api-port`, `--create-user` y `--skip-packages`. Es idempotente: repetirlo actualiza la instalación.

### El `.env` vive en el prefijo

- El instalador **nunca sobrescribe ni borra** `<prefijo>/.env` (FNC-125).
- Si el prefijo no tiene `.env` y la carpeta clonada sí, se copia **una sola vez** (permisos 600).
- El `.env` debe ser un **archivo regular**: si es un enlace simbólico, un directorio o tiene otro enlace duro, el instalador se detiene. Dueño y permisos se aplican sobre el archivo ya abierto sin seguir enlaces (`O_NOFOLLOW` + `fchown`/`fchmod`), y `chown -R -h` no sigue enlaces del prefijo.
- La copia (`rsync --delete`) tampoco toca lo local del prefijo: `.env.*` (salvo `.env.example`), `instance/`, `backups/`, `uploads/`, `storage/` y `logs/`.
- Prueba: `pytest tests/deploy/test_copia_proyecto_sh.py`.

### Puertos del backend y del frontend

- `--web-port` (frontend Next.js, por defecto `3000`) y `--api-port` (backend Gunicorn, por defecto `5001`) (FNC-127).
- Precedencia: opción > variable `WEB_PORT`/`API_PORT` > `<prefijo>/.env` > por defecto.
- Del `.env` solo se leen esas dos líneas (sin cargarlo ni imprimir nada más).
- Enteros de 1024 a 65535 y distintos entre sí; si no, el instalador se detiene.
- Siempre en loopback (`127.0.0.1`): solo cambia el número. nginx, las unidades y el `BACKEND_URL` del SSR usan el mismo valor.
- `preflight.sh` comprueba los mismos puertos (entorno > `.env` > por defecto).
- Caso típico: Grafana ya ocupa el 3000.

```bash
WEB_PORT=3100 APP_NAME=portal ./deploy/preflight.sh
sudo ./deploy/install.sh --name portal --web-port 3100 …
```

- Prueba: `pytest tests/deploy/test_puertos_sh.py`.

### Servicio de la base de datos

- Backend y worker arrancan después del servicio de BD local: `@DB_SERVICE@` en las plantillas (FNC-125).
- Detección, en este orden: `mysqld.service`, `mariadb.service`, `mysql.service` (los alias no cuentan).
- Sin ninguno (BD remota): la dependencia se quita de `After=`/`Wants=`.
- Forzarlo: `--db-service mariadb` (o `DB_SERVICE=mariadb`); se valida como nombre de unidad.
- Cliente `mysql` (opcional, para respaldos): solo si no hay uno; paquete `mariadb` con MariaDB y `mysql` en los demás casos (en el9 chocan). Si falla, es un aviso y sigue.
- Prueba: `pytest tests/deploy/test_servicio_bd_sh.py`.

### Nombre del despliegue

`--name` define todo lo que lleva el nombre, de una sola vez:

```bash
sudo ./deploy/install.sh --name portal --domain portal.ejemplo.com
```

| Qué | Valor |
|---|---|
| Unidades systemd | `portal-backend`, `portal-frontend`, `portal-worker` |
| Prefijo | `/opt/portal` |
| Registros | `/var/log/portal` |
| Config de nginx | `/etc/nginx/conf.d/portal.conf` |
| Upstreams de nginx | `portal_api`, `portal_web` |

Cada uno se puede ajustar aparte con `--prefix` y `--logdir`; `--title` cambia
solo el texto de `Description=`. El nombre admite minúsculas, dígitos, `-` y
`_`, hasta 32 caracteres: acaba en rutas, unidades systemd y nombres de
upstream, y debe ser válido en los tres.

Para que `preflight.sh` compruebe el mismo nombre:

```bash
APP_NAME=portal ./deploy/preflight.sh
```

### Usuario de servicio

El script **no crea cuentas por defecto**. Usa la que indique `--user`, y si se
omite, la que invoca sudo:

```bash
sudo ./deploy/install.sh --user www-data      # cuenta existente
```

Si la cuenta no existe, aborta indicando cómo proceder. Para que la cree —una
cuenta de sistema sin shell ni directorio propio— hay que pedirlo:

```bash
sudo ./deploy/install.sh --user nexus --create-user
```

Sobre una cuenta que ya existe, `--create-user` no la modifica. El grupo se
toma del que tenga el usuario, sin asumir que coincida con su nombre.

### Servidor detrás de un proxy corporativo

Si el servidor no tiene salida directa a Internet, hay que indicar el proxy o
la instalación fallará al descargar paquetes:

```bash
PROXY_URL=http://proxy.empresa.com:3128 ./deploy/preflight.sh
sudo ./deploy/install.sh --proxy http://proxy.empresa.com:3128 \
                        --no-proxy localhost,.empresa.com
```

Cada herramienta lee el proxy de un sitio distinto, y el script cubre los tres:

| Herramienta | De dónde lo lee |
|---|---|
| `dnf` | `/etc/dnf/dnf.conf` — ignora las variables de entorno |
| `pip` | `--proxy` por línea de órdenes |
| `npm` | `--proxy` / `--https-proxy` por línea de órdenes |

Los dos últimos se pasan explícitamente porque `sudo -u` no hereda el entorno
del invocador. Antes de tocar `dnf.conf` se guarda una copia.

`preflight.sh` comprueba la salida real contra pypi.org y el registro de npm, y
enmascara las credenciales del proxy al mostrarlas.

Si el proxy usa autenticación, conviene exportar `PROXY_URL` en lugar de pasar
`--proxy` en la orden, para que la contraseña no quede en el historial de bash:

```bash
export PROXY_URL='http://usuario:clave@proxy.empresa.com:3128'
sudo -E ./deploy/install.sh --domain nexus.ejemplo.com
```

### Notas propias de Rocky/RHEL 8

- **Python**: el proyecto funciona con 3.11 o superior, y el instalador
  reutiliza el intérprete que ya haya en el servidor para no acumular
  versiones. Solo si no encuentra ninguno válido instala `python311` desde
  AppStream (Rocky 8 trae 3.6 de serie). Con `--python /ruta/al/python` se
  fuerza uno concreto.
- **Node 22** puede no estar en AppStream según la versión menor de Rocky; si
  falta el módulo, el script cae al repositorio de NodeSource.
- **SELinux** en `Enforcing` impide que nginx conecte con los upstream locales,
  y responde 502 sin explicación clara. El script activa
  `httpd_can_network_connect`.
- **firewalld** suele venir activo: el script permite `http` y `https`.

### Notas propias de RHEL 9 (el9)

- **Servicios**: MySQL es `mysqld.service`, MariaDB `mariadb.service` y Redis `redis.service`; el instalador detecta el de la BD.
- **Python 3.12**: paquete `python3.12` (no es módulo); si `cryptography` no trae rueda para la plataforma, instalar `python3.12-devel`.
- **Node 24** en `/usr/bin/node` cumple el rango; el instalador no instala otro.
- **Redis 6.2**: la configuración está en `/etc/redis/redis.conf` o `/etc/redis.conf` según el paquete (`requirepass` y `bind` de loopback van ahí).

## Instalación manual

```bash
# Backend — sirve cualquier Python >= 3.11
python3.11 -m venv venv          # o python3.12, el que tengas
venv/bin/pip install -r requirements.txt

# Frontend
cd frontend && npm ci && npm run build
```

El build usa `output: standalone`, así que el servicio arranca
`.next/standalone/server.js` — **`next start` no funciona con esa
configuración** y Next lo advierte al arrancar.

`standalone` **no copia los estáticos**, hay que ponerlos donde `server.js` los
busca, o la interfaz carga sin CSS:

```bash
cp -r frontend/.next/static frontend/.next/standalone/.next/static
[ -d frontend/public ] && cp -r frontend/public frontend/.next/standalone/
```

`server.js` resuelve esas rutas relativas a su propio directorio, por eso la
unidad systemd usa `WorkingDirectory=.../.next/standalone`.

### Worker de aprovisionamiento

Plantilla `deploy/worker.service.tmpl` → unidad `<nombre>-worker`
(FNC-067). Corre `venv/bin/flask --app run:app provisioning worker` con la
misma cuenta de servicio y el mismo `.env` que el backend.

| Aspecto | Valor |
|---|---|
| Requisitos | MySQL migrado, Redis con `requirepass` y `REDIS_PASS` en el `.env` (SEG-29); sin ellos sale con código 1 |
| Redis | En el mismo servidor, escuchando **solo en loopback** y con `REDIS_HOST=localhost` (SEC-CFG-08) |
| Orden de arranque | Después de la red, el servicio de BD local detectado (`mysqld`, `mariadb` o `mysql`; ninguno si es remota) y `redis.service` |
| Reinicio | `Restart=on-failure` cada 30 s; tras 10 fallos en 15 min queda en `failed` |
| Apagado | `SIGTERM` termina el intento en curso; `TimeoutStopSec=630` (600 s máx. de intento + 30 s de margen) y después `SIGKILL` |
| Registros | journald: `journalctl -u <nombre>-worker -f` |
| Endurecimiento | Sin privilegios ni capacidades, `ProtectSystem=strict`, `ProtectHome`, `PrivateTmp`, `PrivateDevices`, kernel y cgroups protegidos, solo familias `AF_UNIX`/`AF_INET`/`AF_INET6`; no escribe en disco |

**Redis remoto (excepción):** solo con TLS hacia Redis y aprobación del dueño
registrada. La app aún no habla TLS con Redis, así que hoy no se admite: hace
falta antes una tarea de backend. Una conexión en claro por la red expondría
`REDIS_PASS` y los mensajes de la cola.

Tras agotar los reinicios:

```bash
sudo systemctl reset-failed nexus-worker && sudo systemctl start nexus-worker
```

Reversión: `sudo systemctl disable --now nexus-worker` (los trabajos quedan en
la BD y se retoman al volver a arrancarlo).

### Servicios y nginx

En `deploy/` solo hay **plantillas**; `install.sh` las rellena y las instala. A mano, sustituir los marcadores `@...@` (por ejemplo `@APP_NAME@`, `@PREFIX@`, `@DB_SERVICE@`) con los mismos valores que usaría `install.sh`; sin BD local, quitar `@DB_SERVICE@` de `After=`/`Wants=` (y la línea `Wants=` si queda vacía):

| Plantilla | Destino |
|---|---|
| `backend.service.tmpl` | `/etc/systemd/system/<nombre>-backend.service` |
| `frontend.service.tmpl` | `/etc/systemd/system/<nombre>-frontend.service` |
| `worker.service.tmpl` | `/etc/systemd/system/<nombre>-worker.service` |
| `nginx.conf.tmpl` | `/etc/nginx/conf.d/<nombre>.conf` (rellenar `server_name` y certificados) |

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nexus-backend nexus-frontend nexus-worker
sudo nginx -t && sudo systemctl reload nginx
```

## Migraciones

No las aplica el instalador. Desde FNC-039 se usa Alembic: respaldo,
`venv/bin/alembic upgrade head` y reinicio del backend y del worker
(`sudo systemctl restart nexus-backend nexus-worker`). Una BD existente se
marca una vez con `venv/bin/alembic stamp 0001` (ver `docs/backend/README.md` §7).

Los SQL sueltos de `utils/migrations/001-004` se retiraron en FNC-028: la línea base `0001` ya contiene su efecto. Si un portal heredado aún guarda el logo como ruta `/assets/...` en `system_config.portal_icon`, hay que volver a subirlo desde Ajustes.

## Correo (SMTP)

Dos formas de configurarlo, y una variable que decide cuál manda:

| `SMTP_FORCE_ENV` | Qué se usa |
|---|---|
| `false` (por defecto) | Lo guardado desde la interfaz. El `.env` solo actúa de respaldo si en la base de datos no hay nada. |
| `true` | Siempre el `.env`. La interfaz pasa a solo lectura y `PUT /api/v1/smtp` responde 409. |

Forzar el entorno sirve para fijar el servidor de correo por despliegue: nadie
puede cambiarlo desde la interfaz, ni siquiera un administrador global.

Las `SMTP_*` (servidor, puerto, cifrado, usuario, remitente) y sus valores por
defecto están en [`docs/configuracion/VARIABLES.md`](../docs/configuracion/VARIABLES.md);
`SMTP_PASSWORD` es secreto (Vaultwarden en staging y producción).

Con `SMTP_FORCE_ENV=true` y `SMTP_SERVER` vacío no se envía nada y la interfaz
lo advierte: se prefiere fallar de forma visible a enviar por un servidor
distinto del previsto.

`ENABLE_NOTIFICATIONS=false` corta todo el correo, al margen de lo anterior.

## Secretos de staging y producción (Vaultwarden, FNC-068)

- `preflight.sh` e `install.sh` cargan `deploy/secretos.sh` (`revisar_vaultwarden`): fuera de `APP_ENV=development` comprueban que cada `VAULTWARDEN_*` obligatoria tenga valor (nunca lo imprimen), que `VAULTWARDEN_URL` sea `https://` con nombre de host y que el bind LDAP use **una** fuente (`LDAP_BIND_PASSWORD_REF` o `LDAP_BIND_PASSWORD`). Con un `FALTA`, `install.sh` se detiene.
- Sin ninguna `VAULTWARDEN_*`: solo `AVISO` (los conectores fallan cerrado).
- Las variables las pone una persona en `<prefijo>/.env` (600). Procedimiento completo, alta de ítems y rotación: [`docs/operacion/SECRETOS.md`](../docs/operacion/SECRETOS.md).
- Prueba: `pytest tests/deploy/test_secretos_sh.py` (`.env` sintéticos).

## Seguridad

> El portal **no se expone** en un entorno accesible antes de cerrar la fase 5
> (seguridad), hoy en pausa por decisión del dueño ([ROADMAP](../docs/planeacion/ROADMAP.md)).

Los puertos de ambos servicios deben escuchar **solo en loopback**. El backend
deduce la identidad SSO de las cabeceras `Remote-*`, y solo las acepta si la
petición viene de un proxy declarado en `TRUSTED_PROXIES` (por defecto
loopback). Nginx, además, borra esas cabeceras si las envía el cliente: sin
eso, cualquiera que alcance el puerto podría enviar `Remote-Email: admin` y
entrar como administrador.

## Notas

- El `venv` del repositorio es de desarrollo y no es portable entre máquinas
  con versiones distintas de Python: hay que recrearlo en el servidor.
- El backend no sirve ningún archivo estático. El logo del portal se guarda
  como data URI en la base de datos, así que no hace falta volumen persistente
  más allá de la BD.
- `FRONTEND_URL` se retiró (FNC-027): el backend ya no redirige a ninguna
  pantalla; sin sesión responde `401` JSON y el frontend lleva al login.
