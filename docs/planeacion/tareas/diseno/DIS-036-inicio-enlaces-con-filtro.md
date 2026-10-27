# DIS-036 — Inicio: enlaces que abren la pantalla con el filtro del contador

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | dashboard |
| **Prioridad** | Baja |
| **Estatus** | Hecha |
| **Creada** | 2026-10-21 |

## Contexto
- DIS-024 enlaza cada contador a su pantalla, pero ninguna lee parámetros de la URL
- "Mis accesos" abre `/requests` en la pestaña "Mis solicitudes"; "Accesos con falla" abría `/inventory` con el filtro `vigente`

## Objetivo
- `/requests?tab=accesos&status=...`, `/inventory?status=fallido`, `/approvals?status=pendiente`, leídos al montar (solo frontend, sin FNC)

## Impacto cruzado
- Origen ← DIS-024

## Decisiones
- Decisión del orquestador (pendiente de validar en la prueba de concepto): autoaprobada; solo frontend, sin FNC.
- Decisión del orquestador (pendiente de validar en la prueba de concepto): filtros leídos una vez al montar con `useSearchParams`; valor fuera de la lista se ignora (queda el predeterminado). Cada `page.tsx` envuelve la pantalla en `Suspense` (exigencia del build de Next 15).
- Decisión del orquestador (pendiente de validar en la prueba de concepto): enlaces → `/requests?status=pendiente|aprobada|rechazada`, `/requests?tab=accesos&status=activo|en_proceso|fallido`, `/approvals?status=pendiente`, `/inventory?status=fallido` ("Accesos con falla") y `?status=activo` ("Accesos activos").
- Decisión del orquestador (pendiente de validar en la prueba de concepto): ayudas `valorPermitido` y `rutaConFiltro` en `access/filtro-url.ts`; no se toca `components/settings/`, `users/` ni `platforms/`.

## Impacto en elementos compartidos
- `MyRequests` y `MyAccess`: prop opcional `estadoInicial` (sin ella, igual que antes); `ESTADOS` de `my-requests.tsx` ahora se exporta. Usos: solo `MyRequestsView`.
- `MyRequestsView`, `Inventory`, `ApprovalsInbox`: leen `useSearchParams` (sin contexto de Next devuelve null y se comportan como antes). Vistas: `/requests`, `/inventory`, `/approvals`.
- `RoleSummary` (`gruposDelResumen`): `Contador.ruta` ahora incluye la consulta; la usa `Dashboard` (`/`).
- Páginas `requests`, `inventory`, `approvals`: envueltas en `Suspense` con `Spinner`.
- `impacto.py`: los demás hallazgos (`Fila`, `Page`, `enlace`, `alPulsar`, `FiltrosInventario`) son coincidencias de nombre; no se modificó su comportamiento fuera de lo anterior.

## Verificación
- `tsc` 0, `lint` 0, `vitest` 0 (1511, 41 archivos; incluye accesibilidad en 0), `build` 0.
- Pruebas nuevas: `tests/components/home/filtro-url.test.tsx` (10: ayudas, lectura del filtro en las tres pantallas, valores inválidos); `role-summary.test.tsx` ajustada a los enlaces con filtro.
- No verificado en navegador (sin cambios visuales; temas, móvil y escritorio sin revisar). Sin `revisor` ni `auditor-accesibilidad` en esta ejecución.

## Bitácora
- 2026-10-27: implementada; En revisión.

- 2026-10-27: `auditor-accesibilidad` Aprobado. Observaciones menores: el filtro se lee solo al montar (navegar dentro de la misma pantalla con otra consulta no lo actualiza) y el fallback de `Suspense` dice «Cargando…» genérico. Hecha (decisión del orquestador, pendiente de validar en la prueba de concepto). Sin verificar en navegador.
