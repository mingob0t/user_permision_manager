# Despliegue

Dos servicios tras un reverse proxy y un worker en segundo plano:

| Servicio | Escucha | Sirve |
|---|---|---|
| `<nombre>-backend` (Flask/Gunicorn) | 127.0.0.1:5001 | API `/api/v1` |
| `<nombre>-frontend` (Next.js) | 127.0.0.1:3000 | La interfaz |
| `<nombre>-worker` (`flask provisioning worker`, RQ) | no escucha | Otorgar y revocar accesos con reintentos (FNC-049, ADR-003) |

`<nombre>` lo define `--name` (por defecto `nexus`).

Nginx enruta `/api/` al backend y el resto al frontend. Ambos van
bajo el mismo dominio a propósito: así la cookie de sesión que emite Flask
llega al frontend sin CORS, y Authelia sigue siendo la autoridad de
autenticación.

## Instalación automatizada (Rocky Linux 8)

```bash
./deploy/preflight.sh                              # evaluación, no modifica nada
sudo ./deploy/install.sh --domain nexus.ejemplo.com
```

`preflight.sh` termina con código 1 si encuentra algo bloqueante. Revisa:

- Distribución y arquitectura
- Espacio (2 GB) y memoria (1 GB; `next build` es lo que más consume)
- Python **3.11 o superior** con `venv`, y Node ≥ 18.18
- Cabeceras de compilación (`gcc`, `openssl-devel`, `libffi-devel`,
  `openldap-devel`), que `cryptography` y `ldap3` necesitan si no hay rueda
  binaria para la plataforma
- Conectividad real con la base de datos y con Redis, leyendo `.env`; Redis
  es **obligatorio** (lo exige el worker), `REDIS_HOST` debe ser un nombre de
  host y `REDIS_PASS` debe tener valor (no se imprime)
- Que `SECRET_KEY` esté definida
- Puertos 5001 y 3000 libres
- nginx, SELinux (`httpd_can_network_connect`) y firewalld

`install.sh` acepta `--prefix` (por defecto `/opt/nexus`), `--user`,
`--domain`, `--python`, `--proxy`, `--no-proxy`, `--create-user` y
`--skip-packages`. Es idempotente: repetirlo actualiza la instalación.

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
                        --no-proxy localhost,127.0.0.1,10.0.0.0/8
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

### Notas propias de Rocky 8

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
| Orden de arranque | Después de la red, `mysql.service` y `redis.service` (si están en el mismo servidor) |
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

### Servicios

```bash
sudo cp deploy/nexus-*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now nexus-backend nexus-frontend nexus-worker
```

### Nginx

```bash
sudo cp deploy/nginx-nexus.conf /etc/nginx/conf.d/
sudo nginx -t && sudo systemctl reload nginx
```

Rellenar `server_name` y las rutas de los certificados.

## Migraciones

No las aplica el instalador. Desde FNC-039 se usa Alembic: respaldo,
`venv/bin/alembic upgrade head` y reinicio del backend y del worker
(`sudo systemctl restart nexus-backend nexus-worker`). Una BD existente se
marca una vez con `venv/bin/alembic stamp 0001` (ver `docs/backend/README.md` §7).

Histórico (anterior a Alembic; ya incluido en la línea base `0001`):

```bash
mysql -u USUARIO -p BASE < utils/migrations/002_drop_drive.sql
venv/bin/python utils/migrations/003_logo_to_db.py
mysql -u USUARIO -p BASE < utils/migrations/004_drop_access_requests.sql
```

## Correo (SMTP)

Dos formas de configurarlo, y una variable que decide cuál manda:

| `SMTP_FORCE_ENV` | Qué se usa |
|---|---|
| `false` (por defecto) | Lo guardado desde la interfaz. El `.env` solo actúa de respaldo si en la base de datos no hay nada. |
| `true` | Siempre el `.env`. La interfaz pasa a solo lectura y `PUT /api/v1/smtp` responde 409. |

Forzar el entorno sirve para fijar el servidor de correo por despliegue: nadie
puede cambiarlo desde la interfaz, ni siquiera un administrador global.

```ini
SMTP_FORCE_ENV=true
SMTP_SERVER=smtp.empresa.com
SMTP_PORT=587
SMTP_ENCRYPTION=starttls      # starttls | ssl | none
SMTP_AUTH=true                # si se omite, se asume true cuando hay usuario y clave
SMTP_USER=servicio@empresa.com
SMTP_PASSWORD=...
SMTP_SENDER_NAME=Nexus
SMTP_SENDER_EMAIL=noreply@empresa.com   # remitente visible; por defecto, SMTP_USER
```

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
