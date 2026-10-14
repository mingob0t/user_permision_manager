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

<nombre>-backend ──> MySQL (por nombre de host) · Redis opcional · OpenLDAP (solo lectura) · SMTP
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
5. Node ≥ 18.18 y npm (recomienda 22 LTS) y disponibilidad del módulo `nodejs:22`.
6. Cabeceras de compilación y salida a Internet (directa o por `PROXY_URL`, con credenciales enmascaradas).
7. Conectividad real a la BD y a Redis leyendo `DB_HOST`/`DB_PORT`/`REDIS_HOST`/`REDIS_PORT` del `.env`, y que `SECRET_KEY` esté definida.
8. Puertos 5001 y 3000 libres.
9. nginx (`nginx -t`, `/etc/nginx/conf.d`).
10. SELinux (`httpd_can_network_connect`) y firewalld (`https`).
11. Nombre del despliegue (`APP_NAME`), cuenta de servicio (`SVC_USER`) y estado del proyecto (venv y `node_modules` previos).

## Instalación (`deploy/install.sh`)

Idempotente; se repite para actualizar. Opciones: `--name`, `--prefix` (por defecto `/opt/<nombre>`), `--logdir` (por defecto `/var/log/<nombre>`), `--title`, `--user`, `--create-user`, `--domain`, `--python`, `--proxy`, `--no-proxy`, `--skip-packages`.

1. Paquetes del sistema: Python 3.11 si no hay uno válido, Node 22 (AppStream o NodeSource), nginx y cabeceras de compilación.
2. Cuenta de servicio: usa la indicada (o quien invoca sudo); solo la crea con `--create-user`.
3. Copia del proyecto al prefijo; el `.env` queda legible solo por la cuenta de servicio.
4. Backend: `venv` y `pip install -r requirements.txt`.
5. Frontend: `npm ci`, `npm run build` y copia de estáticos a `.next/standalone`.
6. Unidades systemd a partir de las plantillas.
7. nginx en `/etc/nginx/conf.d/<nombre>.conf`, SELinux y firewalld.

**No aplica migraciones**: se ejecuta `venv/bin/alembic upgrade head` a mano antes de reiniciar (ver `docs/backend/README.md` §7). `utils/migrations/` queda como histórico.

## Servicios systemd

| Unidad | Proceso | Escucha | Detalles |
|---|---|---|---|
| `<nombre>-backend` | `venv/bin/gunicorn run:app`, 4 workers, timeout 120 s | loopback:5001 | `EnvironmentFile=<prefijo>/.env`; logs `access.log` y `error.log` en el directorio de registros; `After=mysql.service`; endurecido (`ProtectSystem=strict`, `ProtectHome`, `PrivateTmp`, `NoNewPrivileges`; solo escribe en el directorio de registros). |
| `<nombre>-frontend` | `node server.js` en `frontend/.next/standalone` | loopback:3000 | `NODE_ENV=production`, `PORT=3000`, `HOSTNAME` en loopback; depende del backend; mismo endurecimiento. |

## Promoción de un cambio

1. Rama de la tarea → revisión (`revisor`, `tester` y, si aplica, `auditor-seguridad`) → merge aprobado por el usuario.
2. Despliegue a **pruebas**: `preflight.sh`, `install.sh` (repetible), migraciones pendientes a mano y verificación.
3. Despliegue a **producción** con la versión etiquetada (ver [RELEASES.md](RELEASES.md)).

## Diferencias entre entornos

Qué variables cambian por entorno. El valor de cada una está en `docs/configuracion/VARIABLES.md`, nunca aquí.

| Variable | Desarrollo | Staging / producción |
|---|---|---|
| `FRONTEND_URL` | URL del frontend local (puerto 3000) | vacía (mismo dominio) |
| `BASE_URL` | URL local | `https://<dominio del entorno>` |
| `BACKEND_URL` (frontend) | backend local | no se usa (enruta nginx) |
| `AUTHELIA_ENABLED` | normalmente `false` | `true` al conectar Authelia |
| `DB_*`, `SECRET_KEY`, `SMTP_*` | `.env` local | `.env` del servidor con secretos de Vaultwarden |
| `LDAP_*` (FNC-040) | `.env` local; vacío = directorio inactivo | `.env` del servidor; `LDAP_BIND_PASSWORD` de Vaultwarden. Con CA interna: copiar su PEM al servidor y apuntar `LDAP_CA_CERT_FILE` (si no, la app no conecta: el certificado se valida) |

## Discrepancias detectadas en `deploy/README.md`

- La instalación manual menciona `deploy/nexus-*.service` y `deploy/nginx-nexus.conf`, que **no existen**; los archivos reales son plantillas (`*.service.tmpl`, `nginx.conf.tmpl`) con marcadores `@APP_NAME@`, `@PREFIX@`, etc., que rellena `install.sh`.
- Los ejemplos de `--no-proxy` incluyen rangos de red numéricos; en este proyecto deben expresarse con nombres de host o dominios cuando sea posible.
