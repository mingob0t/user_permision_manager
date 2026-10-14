# FNC-069 — Cliente y tipos web del gestor de accesos

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | web |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | lib-api |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-069-cliente-tipos-web-gestor-accesos` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- Todo `fetch` pasa por `request()` de `frontend/src/lib/api.ts`, que no se exporta; los tipos viven en `lib/types.ts` (206 líneas)
- La fase agrega unos 25 endpoints
- `api.ts` además tiene una IP de loopback como valor por defecto de `BACKEND_URL` (deuda 9, FNC-005)
- Requerimientos: Contratos de FNC-038

## Objetivo
- Agregar funciones y tipos por sección en archivos propios bajo `frontend/src/lib/access/`, reutilizando `request()` y `ApiError`, con datos simulados del contrato para que las pantallas avancen antes que el backend

## Alcance
- **Incluye:**
  - Exportar `request` (o un `apiRequest`) de `lib/api.ts` sin cambiar su comportamiento
  - `lib/access/{requests,grants,inventory,audit,connectors,provisioning,users,home}.ts` y `lib/access/types.ts`
  - Datos simulados del contrato tras una bandera de desarrollo, marcados como pendientes de integración
  - Pruebas de Vitest del cliente (forma de las peticiones y manejo de 401/403/409)
- **No incluye:**
  - Pantallas (DIS-013 a DIS-024)
  - Rewrites de `next.config.ts` (FNC-005)

## Hallazgos de seguridad que absorbe
- **FNC-005** parcial: la IP por defecto de `BACKEND_URL` en `lib/api.ts` pasa a `localhost` o a configuración. La parte de `next.config.ts` queda en FNC-005.

## Archivos previstos
- `frontend/src/lib/api.ts` (exportar `request`, valor por defecto sin IP)
- `frontend/src/lib/access/*.ts` (nuevos)
- `frontend/src/lib/access/__tests__/`

## Reutilización
- `request`, `ApiError`, `useAsync`

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `frontend/src/lib/api.ts` | Cliente HTTP compartido | Todas las pantallas del frontend | Pendiente |

## Variables y configuración
- `BACKEND_URL`: cambio del valor por defecto registrado en `HISTORIAL.md` con motivo (sin IP).

## Criterios de aceptación
- [ ] Cada endpoint del contrato tiene su función tipada (revisión contra el contrato)
- [ ] Las pantallas existentes siguen funcionando (typecheck, lint y prueba de humo)
- [ ] Criterios comunes web (FNC-037)

## Impacto cruzado
- Genera → DIS-013 a DIS-024
- Origen ← FNC-037
- Depende de → FNC-036, FNC-024, FNC-025, FNC-038

## Riesgos y reversión
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
