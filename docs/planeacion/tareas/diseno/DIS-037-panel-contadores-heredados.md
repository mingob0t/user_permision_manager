# DIS-037 — Panel: retirar o reubicar los contadores heredados de `/stats` que duplican el resumen por rol

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | dashboard |
| **Prioridad** | Baja |
| **Estatus** | En revisión |
| **Creada** | 2026-10-21 |
| **Inicio** | 2026-10-27 |

## Contexto
- Tras DIS-024, el admin y el superadmin ven "Áreas" y "Plataformas" dos veces: en el resumen (`/home/summary`) y en "Actividad del portal" (`/stats`)
- DIS-024 no quitó contenido existente (fuera de su alcance); la gráfica y "Más visitadas" no se duplican

## Objetivo
- Decidir con el dueño, en el rediseño visual, si se retiran los contadores duplicados y se deja de `/stats` solo visitas, gráfica y "Más visitadas"

## Impacto cruzado
- Origen ← DIS-024
- Relacionada → DIS-003 (gráfica con variables `--nx-*` inexistentes)

## Decisiones (decisión del orquestador, pendiente de validar en la prueba de concepto)
- Se retiran "Áreas" y "Plataformas" de "Actividad del portal" para `is_admin` e `is_area_admin`: el resumen (`totals`) ya los muestra en "Todo el sistema" / "Tus áreas", con enlace a su pantalla
- Se conservan para el usuario sin rol de administración, cuyo resumen no trae totales: así no se pierde información
- Se conservan "Visitas", "Usuarios" (si llega), "Más visitadas" y la gráfica; `/stats` no cambia
- Sin salto: Áreas y Plataformas no se muestran hasta conocer el rol (sesión cargada); `RoleSummary` avisa con `onFallo` si el resumen falla y entonces el admin los recupera de `/stats` (respaldo). Decisión del orquestador (pendiente de validar en la prueba de concepto)
- Para validar por el dueño (auditor, D1): para el admin de área, "Plataformas" del resumen (solo sus áreas) puede ser menor que el de `/stats` (suma accesos activos en otras áreas)
- Pruebas: admin y admin de área sin duplicados; usuario conserva los dos contadores

## Impacto en elementos compartidos (`impacto.py`, contra `develop`)
| Elemento | Usado en | Nota |
|---|---|---|
| `Dashboard` (`dashboard.tsx`) | `app/page.tsx` | Es la ruta `/`; validar en navegador |
| `useTokenColors` (nuevo, `lib/use-token-colors.ts`) | solo `dashboard.tsx` | Sin otros usos |
| `PARES` (`pares-contraste.ts`) | `contraste.test.ts` | 2 pares nuevos, solo pruebas |
| `contadores` (falso positivo) | — | Ayuda local de `dashboard.test.tsx`; el nombre coincide con otro de `role-summary` y del backend, sin relación |
| `TopeLiterales` | `colores-literales.test.ts` | Se quita la excepción de `dashboard.tsx` (hex 1 → 0) |

## Verificación (2026-10-27, en `frontend/`)
- typecheck 0, lint 0, vitest 0 (1297 pruebas), next build 0; contraste conocido 0, texto mínimo 0, área táctil 0
- No verificado en navegador (tema claro y oscuro, móvil): la gráfica se lee con `getComputedStyle`, solo medida con pares de tokens

| 2026-10-27 | En curso → En revisión: contadores duplicados retirados para quien administra; commit `[DIS-037]` |
