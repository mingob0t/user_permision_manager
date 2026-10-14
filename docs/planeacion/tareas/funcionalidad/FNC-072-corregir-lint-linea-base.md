# FNC-072 — Corregir los hallazgos de lint de la línea base web

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | web |
| **Agente** | desarrollador |
| **Fase** | 2 |
| **Módulo / Área** | frontend |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Creada / Inicio** | 2026-10-13 |
| **Rama** | `fnc/FNC-072-corregir-lint-linea-base` (desde `fnc/FNC-024-linea-base-web`) |

## Contexto
- Tras instalar ESLint (FNC-024), `npm run build` falla por 1 error de lint.
- Error: `src/app/error.tsx:36` usa `<a href="/">` en vez de `Link`.
- Avisos: `dashboard.tsx:11` (variable sin uso), `settings-panel.tsx:106` (`<img>`), `use-async.ts:30` (dependencias del hook).
- Aprobada por el dueño el 2026-10-13 (opción "corregir el enlace").

## Criterios de aceptación
- [x] `npm run lint` sin errores ni avisos
- [x] `npm run build` y `npm run typecheck` con código de salida 0
- [x] Sin cambios visuales ni de comportamiento (único matiz: "Ir al inicio" navega del lado del cliente)

## Cambios
- `frontend/src/app/error.tsx`: el enlace "Ir al inicio" usa `Link` de `next/link` (mismo `href` y clases).
- `frontend/src/components/dashboard.tsx`: se quita el import `EmptyNote` sin uso.
- `frontend/src/components/settings-panel.tsx`: se desactiva `no-img-element` solo en la línea del logo; es un data URI de la BD y `next/image` no lo optimiza.
- `frontend/src/lib/use-async.ts`: se desactiva `exhaustive-deps` solo en `useCallback(load, deps)`; las dependencias llegan por parámetro a propósito. El código no cambia.

## Verificación
- `npm ci`: instalado (código 0).
- `npm run lint`: "No ESLint warnings or errors", código 0.
- `npm run typecheck`: sin errores, código 0.
- `npm run build`: compila las 14 rutas, código 0.
- No verificado: navegación manual en el navegador (no hay backend levantado en este worktree).
- `auditor-accesibilidad` no aplica: no hay cambio visual ni de tokens.
- Revisor: "Con observaciones", solo de documentación y commit; atendidas.
- auditor-accesibilidad (modo cambio): Aprobado. El enlace "Ir al inicio" sigue siendo <a href="/"> (next/link), con las mismas clases, texto y foco; sin cambio de color ni tamaño; el resto son imports y comentarios.

## Impacto en elementos compartidos
| Elemento | Definido en | Usado en | Validar |
|---|---|---|---|
| `useAsync` | `frontend/src/lib/use-async.ts` | areas-list, audit-log, dashboard, favorites-list, notifications-list, platform-admin, platform-catalog, settings-panel, users-list | Solo se agregaron comentarios; sin cambio de comportamiento |
- `impacto.py` también marca `save` en `settings-panel.tsx`: falso positivo, esa función no se tocó.

## Bitácora
- 2026-10-13: corregidos 1 error y 3 avisos de lint; lint, typecheck y build en verde; commit local sin push.
