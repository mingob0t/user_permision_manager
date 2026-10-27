# FNC-118 — Web: retirar el rewrite de `/auth/:path*` en `next.config.ts`

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | web |
| **Agente** | desarrollador |
| **Fase** | 4 |
| **Módulo / Área** | frontend |
| **Prioridad** | Baja |
| **Estatus** | Hecha |
| **Creada** | 2026-10-26 |
| **Inicio** | 2026-10-26 |
| **Requiere auditor-seguridad** | No |

## Contexto
`frontend/next.config.ts:18` reenvía `/auth/:path*` al backend en desarrollo. Desde FNC-027 el backend no tiene rutas `/auth` (responderían 404). Ninguna llamada del frontend las usa: todo va a `/api/v1/auth/*`.

## Alcance
- **Incluye:** quitar el `rewrite` y actualizar su comentario.
- **No incluye:** nada más del frontend.

## Impacto cruzado
- Origen ← FNC-027

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
| 2026-10-26 | Creada como Propuesta desde FNC-027 |
| 2026-10-26 | Implementada junto con FNC-005 en `fnc/FNC-005-118-rewrites-next`; en revisión |
