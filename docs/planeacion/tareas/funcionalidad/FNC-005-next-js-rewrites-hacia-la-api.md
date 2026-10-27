# FNC-005 — Next.js: rewrites hacia la API solo en desarrollo y sin IP por defecto en BACKEND_URL

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | web |
| **Agente** | desarrollador |
| **Fase** | 5 |
| **Módulo / Área** | config |
| **Prioridad** | Crítica |
| **Estatus** | En revisión |
| **Responsable** | |
| **Creada** | 2026-10-13 |
| **Inicio** | 2026-10-26 |
| **Finalizada** | |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-005-next-js-rewrites-hacia-la-api` |
| **Commits / PR** | |
| **Requiere migración BD** | Por definir |
| **Requiere auditor-seguridad** | Sí |

## Contexto
Los rewrites de `frontend/next.config.ts:15-20` siguen activos en producción y no distinguen mayúsculas; `BACKEND_URL` cae a una IP de loopback (`next.config.ts`, `src/lib/api.ts`).

Origen (diagnóstico inicial, FNC-001):
- [`docs/seguridad/auditorias/2026-10-13-auditoria-inicial.md`](../../../seguridad/auditorias/2026-10-13-auditoria-inicial.md): SEG-04
- [`docs/backend/README.md`](../../../backend/README.md): discrepancias

> **Regla de fases (2026-10-13):** esta corrección se hace en la fase 5 (seguridad final), **salvo** que una tarea anterior modifique este módulo: en ese caso la tarea debe dejarlo cumpliendo `docs/seguridad/LINEAMIENTOS.md` y corrige este hallazgo de paso.

## Objetivo
_Se completa al aprobar la tarea._

## Alcance
- **Incluye:** lo descrito en el contexto.
- **No incluye:** _se precisa al aprobar._

## Criterios de aceptación
- [x] Hallazgos de origen corregidos y verificados
- [x] Prueba de regresión que primero falla (si corrige un defecto)
- [x] Pruebas mínimas del lineamiento de pruebas, ejecutadas
- [x] Cumple `docs/estandarizacion/` y no duplica código existente
- [x] Sin direcciones IP ni secretos

## Impacto cruzado
- Depende de → Junto con FNC-004 y FNC-006

## Decisiones
- Solo `NODE_ENV=development` activa el rewrite, sin variable adicional de desarrollo (menos superficie); decisión del orquestador (pendiente de validar en la prueba de concepto).
- La lógica va en `frontend/rewrites-dev.ts` (función pura, probable) y `next.config.ts` solo la invoca; decisión del orquestador (pendiente de validar en la prueba de concepto).
- `BACKEND_URL` se valida (URL http(s), no IP) al cargar la configuración; falla al arrancar; decisión del orquestador (pendiente de validar en la prueba de concepto).
- `lib/api.ts` ya usa ruta relativa en el navegador (`BASE = ''` y `/api/v1`) y `BACKEND_URL` en SSR; no se tocó; decisión del orquestador (pendiente de validar en la prueba de concepto).

## Verificación (en `frontend/`)
| Comprobación | Resultado |
|---|---|
| `npx tsc --noEmit` | código 0 |
| `npm run lint` | código 0, sin avisos |
| `npx vitest run` | código 0, 34 archivos, 1214 pruebas (incluye `tests/lib/next-config.test.ts`, 7) |
| `NODE_ENV=production next build` | código 0; `.next/routes-manifest.json` con `rewrites` vacíos (beforeFiles, afterFiles y fallback) |
| No verificado | `next dev` en navegador ni el flujo detrás de nginx real; la prueba del rewrite de dev es sobre la función de `next.config.ts` |

## Impacto en elementos compartidos (`impacto.py`)
| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `BACKEND_URL` | variable de entorno | `frontend/next.config.ts` (ahora `frontend/rewrites-dev.ts`) | `frontend/src/lib/api.ts` (sin cambios; mantiene su propio valor por defecto `http://localhost:5001`) | frontend/src | ☐ |

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-26 | Implementada junto con FNC-118 en `fnc/FNC-005-118-rewrites-next`; en revisión |
