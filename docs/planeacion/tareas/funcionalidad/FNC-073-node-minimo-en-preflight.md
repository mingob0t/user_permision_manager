# FNC-073 — Alinear la versión mínima de Node en el despliegue

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | infra |
| **Agente** | devops |
| **Fase** | 6 |
| **Módulo / Área** | deploy |
| **Prioridad** | Baja |
| **Estatus** | Hecha |
| **Creada** | 2026-10-13 |

## Contexto
- `deploy/preflight.sh:19,128` acepta Node 18 o mayor.
- Desde FNC-025, vitest 4 y jsdom 29 piden Node 20.19+ o 22.13+; con versiones menores `npm ci` avisa `EBADENGINE`.

## Criterios de aceptación
- [x] `preflight.sh` y la documentación de entornos exigen la misma versión mínima que `package.json`

## Decisiones
Todas: decisión del orquestador (pendiente de validar en la prueba de concepto).
- Rango único `^22.13.0 || >=24.0.0`: Vitest 4 y jsdom 29 piden `^20.19 || ^22.13 || >=24` y Vitest excluye el 23; Next 15 pide `>=18.18`. Se deja fuera Node 20 (sin soporte desde 2026-04) y el despliegue ya instala 22.
- Se declara `engines.node` en `frontend/package.json` y en la raíz de `package-lock.json` (como lo escribe npm); sin `engine-strict`, `npm ci` solo avisa.
- `install.sh` instala Node 22 cuando el presente no cumple (antes solo si era < 18), comprueba después y, si dnf no cambió la versión, se detiene indicando `dnf module switch-to`. Con `--skip-packages` comprueba y se detiene, igual que con Python.
- No había `.nvmrc`, `.node-version`, Dockerfile, docker-compose ni `.github/workflows`: no se crearon (fuera de alcance).

## Cambios
- `frontend/package.json`, `frontend/package-lock.json`: `engines.node`.
- `deploy/preflight.sh`, `deploy/install.sh`: `NODE_MIN_MINOR`, `NODE_NEXT_MAJOR`, `NODE_RANGO` y `node_cumple_minimo()`.
- `docs/operacion/ENTORNOS.md`, `docs/frontend/README.md`, `docs/configuracion/VARIABLES.md` (constantes), `HISTORIAL.md`.

## Pendiente para FNC-035
No se editaron (FNC-035 los reescribe); deben decir `^22.13.0 || >=24.0.0`:
- `README.md:60`: "Node 18.18 o superior (se recomienda 22 LTS)".
- `deploy/README.md:29`: "Node ≥ 18.18".

## Verificación
| Comando | Resultado |
|---|---|
| `node --version` | v22.23.2 (cumple) |
| `bash -n` de `preflight.sh` e `install.sh` | 0 |
| `probar_node.sh` (scratchpad): `node_cumple_minimo` de cada script contra `semver.satisfies` con el rango de `package.json`, 12 versiones (18.20, 20.18, 20.19, 22.12, 22.13, 22.23, 23.11, 24, 25, 26, vacío, basura) | 0 discrepancias en ambos scripts |
| `npm ci --dry-run` (frontend) | 0, sin `EBADENGINE` |
| `npm run build` (frontend) | 0 |
| `npx vitest run` (frontend) | 0; 53 archivos, 1699 pruebas |

No verificado: `preflight.sh` e `install.sh` completos en un servidor Rocky (instalación con dnf/NodeSource y el caso de un Node 20 previo); queda para la prueba en el servidor. `shellcheck` no está instalado.

## Impacto en elementos compartidos
**Impacto en elementos compartidos:** ninguno detectado (comparado contra `develop`; 9 archivos cambiados).
Afecta a todos los entornos que se instalen con `deploy/`: un servidor con Node < 22.13 o 23 ahora da `FALTA` en preflight y el instalador intenta Node 22.

## Bitácora
- 2026-10-27: aprobada en modo autónomo; En curso → En revisión. Commit en `fnc/FNC-073-node-minimo`.

- 2026-10-27: el orquestador ajustó `README.md` y `deploy/README.md` al rango nuevo tras integrar FNC-035. Pendiente: `preflight.sh` e `install.sh` completos en un servidor Rocky. Hecha (decisión del orquestador, pendiente de validar en la prueba de concepto).
