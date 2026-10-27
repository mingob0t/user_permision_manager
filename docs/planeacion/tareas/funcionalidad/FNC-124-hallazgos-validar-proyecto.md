# FNC-124 — Hallazgos de `validar_proyecto.py`

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | infra |
| **Agente** | devops |
| **Fase** | 6 |
| **Módulo / Área** | operacion |
| **Prioridad** | Media |
| **Estatus** | Hecha |
| **Rama** | `fnc/FNC-124-hallazgos-validar-proyecto` |
| **Creada** | 2026-10-27 |

## Contexto
Salida de `~/.claude/agentes/herramientas/validar_proyecto.py` durante FNC-035 (ya existían en `develop`):

| Tipo | Hallazgo |
|---|---|
| Error | `.gitignore` no ignora `logs/` |
| Aviso | `NODE_ENV` y `TZ` se usan en el código y no están en `.env.example` ni en `VARIABLES.md` |
| Aviso | `deploy/install.sh`: dirección de loopback literal en la lista `no_proxy` por defecto (usar nombre de host) |

## Criterios de aceptación
- [x] `validar_proyecto.py` sin errores ni esos avisos
- [x] Variables registradas en `VARIABLES.md` y `.env.example`

## Impacto cruzado
- Origen ← FNC-035

## Cambios
| Archivo | Cambio |
|---|---|
| `.gitignore` | `/logs/` → `logs/` + `!docs/logs/` |
| `.env.example` | alta `TZ=America/Mexico_City` (sección SYSTEM) y `NODE_ENV=` vacía (sección Next.js), con comentario |
| `deploy/install.sh` | ejemplo de ayuda de `--no-proxy`: rango privado → dominio `.intranet.example`; `NO_PROXY_LIST` por defecto sin cambio |
| `docs/configuracion/VARIABLES.md` | filas `TZ` y `NODE_ENV`: en `.env.example`, valores por defecto y dónde se usan |
| `docs/configuracion/HISTORIAL.md` | alta de `TZ` y `NODE_ENV` en `.env.example` con motivo |

## Decisiones (decisión del orquestador, pendiente de validar en la prueba de concepto)
- **`logs/` sin anclar + `!docs/logs/`.** `/logs/` ya estaba y el validador compara el texto exacto `logs/`. La excepción re-incluye la carpeta `docs/logs/` (su padre `docs/` no está ignorado); comprobado con `git check-ignore`. Además ignora cualquier `logs/` anidado (p. ej. `frontend/logs/`).
- **`TZ` con valor y no vacía.** `app/__init__.py`: `os.getenv('TZ_APP', os.getenv('TZ', ...))`; una `TZ` vacía con `TZ_APP` ausente deja el proceso en UTC. Mismo valor que `TZ_APP`: sin cambio de comportamiento.
- **`NODE_ENV` vacía.** La fija Next (`next dev`/`build`/`start`) y la unidad `frontend.service` (`Environment=`, no carga el `.env`); Flask no la lee. Un valor en el ejemplo no tendría efecto o confundiría.
- **`no_proxy` por defecto conserva `127.0.0.1,::1`.** No es equivalente a `localhost`: curl, npm y pip comparan el texto del host de la URL, así que una petición a `http://127.0.0.1:...` dejaría de excluirse y saldría por el proxy. La regla de IPs del método permite `127.0.0.1` (`IP_PERMITIDAS`). El aviso real del validador era el rango privado del ejemplo de ayuda (línea 7), que es lo que se cambió. Sin cambio de valor → sin fila en HISTORIAL.

## Verificación
| Comando | Resultado |
|---|---|
| `validar_proyecto.py` antes | 1 error (`.gitignore no ignora: logs/`), 3 avisos (sin carpeta `logs/`; `NODE_ENV`, `TZ` fuera de `.env.example`; IP en `deploy/install.sh`); salida 1 |
| `validar_proyecto.py` después | 0 errores, 1 aviso (sin carpeta `logs/`); «Cumple»; salida 0 |
| `git check-ignore -v --no-index` | `docs/logs/2026-10-27.md` y un `docs/logs/` nuevo: no ignorados; `logs/app.log`, `frontend/logs/x.log`: ignorados; 10 archivos de `docs/logs/` siguen versionados |
| `bash -n deploy/install.sh` | salida 0 |
| pre-commit (`scripts/lineamientos/precommit.py`) | al hacer el commit |

**No verificado:** `install.sh` real con proxy (servidor); despliegue.

**Fuera de alcance (sin tarea):** el aviso «no hay carpeta logs/» sigue; los registros van a `/var/log/<nombre>` (ENTORNOS.md) y crear `logs/` no se pidió. `scripts/secretos/cargar_secretos.sh` pide a Vaultwarden un ítem por cada variable de `.env.example` (ahora también `TZ` y `NODE_ENV`); hoy no lo invoca nada en el repo.

## Impacto en elementos compartidos
`impacto.py`: **ninguno detectado** (contra `develop`; 7 archivos). Configuración compartida por naturaleza:
- `.gitignore`: todos los entornos y el equipo; solo agrega `logs/` anidados a lo ignorado.
- `.env.example`: plantilla del `.env` de dev y de servidores (backend y worker cargan el `.env` con `EnvironmentFile`; `TZ` igual a `TZ_APP`, sin efecto); `cargar_secretos.sh` (sin uso).
- `deploy/install.sh`: solo texto de ayuda.

## Bitácora
- 2026-10-27 — devops: implementación y verificación; En revisión.

- 2026-10-27: revisado por el orquestador; desviaciones justificadas (`logs/` + `!docs/logs/` porque el validador busca el texto exacto; loopback en `no_proxy` se conserva porque `localhost` no equivale para curl/npm/pip). `validar_proyecto.py`: 0 errores. Observación: `scripts/secretos/cargar_secretos.sh` pide a Vaultwarden un ítem por cada variable de `.env.example`, ahora también `TZ` y `NODE_ENV`, que no son secretos; revisar al usar el script en staging. Hecha (decisión del orquestador, pendiente de validar en la prueba de concepto).
