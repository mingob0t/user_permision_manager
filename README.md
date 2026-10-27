# pokemon — gestor de accesos por áreas

Portal para gestionar el acceso a plataformas internas agrupadas por **áreas**. Origen: clon de NEXUS (`docs/REQUERIMIENTOS.md`).

| Qué hace | Cómo |
|---|---|
| Catálogo y solicitudes | El usuario pide acceso a una plataforma con nivel `usuario` o `admin` |
| Aprobaciones | El admin del área aprueba o rechaza (rechazo con motivo) |
| Aprovisionamiento | Al aprobar, un worker agrega al usuario al grupo de OpenLDAP o ejecuta un conector (API, SSH o BD), con reintentos |
| Revocación e inventario | Quién tiene qué plataforma, con qué nivel y desde cuándo |
| Auditoría | Bitácora inmutable con antes/después, visible según el rol |
| Autenticación | Authelia (SSO por cabeceras), directorio OpenLDAP y cuenta local de emergencia |

Roles: `administrador` (superadmin), `admin_area` (sus áreas) y `usuario`. Detalle: [docs/REQUERIMIENTOS.md](docs/REQUERIMIENTOS.md) §2.

## Estado

> ⚠️ **No exponer el portal** en un entorno accesible antes de cerrar la fase 5 (seguridad).

| Fase | Estado |
|---|---|
| 0 — Incorporación | Cerrada |
| 1 — Lineamientos de seguridad | Cerrada |
| 2 — Pruebas | Cerrada salvo el CI (FNC-026), que espera el repositorio remoto |
| 3 — Gestor de accesos | Cerrada (2026-10-26) |
| 4 — Estándares, modularidad y accesibilidad | Cerrada (2026-10-27) |
| 5 — Seguridad final | **En pausa** por decisión del dueño (2026-10-27); se retoma cuando él lo indique |
| 6 — Documentación y operación | En curso |

Detalle y tareas: [ROADMAP](docs/planeacion/ROADMAP.md) y [TABLERO](docs/planeacion/TABLERO.md).

## Arquitectura

| Proceso | Tecnología | Puerto (loopback) | Función |
|---|---|---|---|
| Backend | Flask, API JSON `/api/v1` | 5001 | Datos, autorización por área; no sirve interfaz |
| Frontend | Next.js 15, TypeScript, Tailwind | 3000 | Toda la interfaz; no accede a la BD |
| Worker | `flask provisioning worker` (RQ sobre Redis) | — | Otorga y revoca accesos en segundo plano |

Ambos servicios van bajo el mismo dominio tras nginx. BD: MySQL (SQLite local si `DB_ENGINE` no es `mysql`), esquema con Alembic. Decisión del stack: [ADR-001](docs/decisiones/ADR-001-stack.md).

## Desarrollo local

Requisitos: Python 3.11 o superior; Node 22 (22.13 o posterior) o Node 24 en adelante; Node 23 no sirve (FNC-073); Redis local con `requirepass` solo para el worker.

```bash
cp .env.example .env                 # completar; .env nunca se versiona
python3.11 -m venv venv
venv/bin/pip install -r requirements.txt -r requirements-dev.txt
venv/bin/alembic upgrade head        # siempre antes de arrancar
venv/bin/python run.py               # terminal 1: API en localhost:5001
(cd frontend && npm ci && npm run dev)   # terminal 2: interfaz en localhost:3000
venv/bin/flask --app run:app provisioning worker   # terminal 3: worker (opcional)
```

- **Validar en local** (sin Authelia ni Vaultwarden), con cuentas demo (FNC-131):
  - `.env` con `APP_ENV=development`, `LOGIN_LOCAL_TODAS_LAS_CUENTAS=true` y `DB_ENGINE` vacío (SQLite);
  - `venv/bin/alembic upgrade head`;
  - `venv/bin/flask --app run:app demo cargar`: crea 2 áreas, 3 plataformas, 1 admin de área, 2 usuarios y 1 solicitud pendiente, y muestra la tabla de cuentas. Contraseña: la pide con confirmación, `--password-desde-stdin` o, sin terminal, la genera y la imprime una vez;
  - `venv/bin/python run.py` y `(cd frontend && npm run dev)`; entrar por «acceso local» con el correo de la tabla (el superadmin sigue siendo `admin`).
  - Sin OpenLDAP, otorgar acceso falla y se ve como fallido en «Ejecuciones» (esperado en local).
- `run.py` arranca en modo debug: solo en tu equipo (corrección en FNC-009).
- Variables y su significado: [VARIABLES.md](docs/configuracion/VARIABLES.md).
- Entrar sin Authelia: [ENTORNOS.md](docs/operacion/ENTORNOS.md) § «Entrar en local sin Authelia».
- Más detalle: [backend](docs/backend/README.md) §6 y [frontend](docs/frontend/README.md) §7.

## Pruebas

| Qué | Comando |
|---|---|
| Backend (pytest, sin `.env` ni servicios externos) | `venv/bin/pytest` |
| Frontend: pruebas (Vitest) | `cd frontend && npm test` |
| Frontend: tipos y lint | `cd frontend && npm run typecheck && npm run lint` |
| Frontend: build | `cd frontend && npm run build` |
| Controles de lineamientos (pre-commit) | `.githooks/pre-commit` (activar con `git config core.hooksPath .githooks`) |

## Despliegue

Rocky/RHEL 8 o 9 con systemd y nginx: `deploy/preflight.sh` y `deploy/install.sh`. Guía: [deploy/README.md](deploy/README.md); entornos: [ENTORNOS.md](docs/operacion/ENTORNOS.md).

## Documentación

| Tema | Documento |
|---|---|
| Índice de `docs/` | [docs/README.md](docs/README.md) |
| Requerimientos, roles y funcionalidades | [docs/REQUERIMIENTOS.md](docs/REQUERIMIENTOS.md) |
| Backend: arquitectura, autorización, modelo de datos, endpoints, migraciones | [docs/backend/README.md](docs/backend/README.md) |
| Frontend: pantallas, menú por rol, tokens y tema | [docs/frontend/README.md](docs/frontend/README.md) |
| Contratos de la API | [docs/contratos/](docs/contratos/README.md) |
| Variables y su historial | [docs/configuracion/](docs/configuracion/VARIABLES.md) |
| Entornos, secretos, respaldos, releases, retención | [docs/operacion/](docs/operacion/ENTORNOS.md) |
| Seguridad | [docs/seguridad/](docs/seguridad/README.md) |
| Decisiones (ADR) | [docs/decisiones/](docs/decisiones/README.md) |
| Estándares y reutilización | [docs/estandarizacion/](docs/estandarizacion/) |
| Despliegue | [deploy/README.md](deploy/README.md) |
| Cambios | [CHANGELOG.md](CHANGELOG.md) |
