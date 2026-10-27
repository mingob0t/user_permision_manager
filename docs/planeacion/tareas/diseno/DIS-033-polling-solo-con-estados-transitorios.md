# DIS-033 — Mis solicitudes y mis accesos: refrescar solo con estados transitorios

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | solicitudes |
| **Prioridad** | Baja |
| **Estatus** | En revisión |
| **Creada** | 2026-10-20 |

## Contexto
- Contratos `solicitudes.md` y `accesos.md` (tabla Refresco): polling "mientras haya `pendiente` o `en_proceso`/`revocando`"
- DIS-014 refresca siempre al intervalo del usuario: `usePolling` no tiene opción para pausarse según los datos

## Objetivo
- `usePolling` admite pausarse según los datos
- `MyRequests` y `MyAccess` consultan periódicamente solo con estados transitorios en la página mostrada

## Impacto cruzado
- Origen ← DIS-014
- Incluye la opción de pausa (`enabled` o equivalente) en `usePolling` (`lib/use-polling.ts`): es frontend, va en esta misma tarea sin FNC aparte (decisión del orquestador)
- Elemento compartido: `usePolling` (DIS-015, DIS-018, DIS-022, DIS-024)

## Decisiones
- Decisión del orquestador (pendiente de validar en la prueba de concepto): autoaprobada.
- Decisión del orquestador (pendiente de validar en la prueba de concepto): `usePolling` ya tenía `activo` (DIS-022); no se modifica el hook ni se crea FNC.
- Decisión del orquestador (pendiente de validar en la prueba de concepto): `MyRequests` es transitoria con solicitud `pendiente` o acceso derivado `en_proceso`/`revocando` (contrato `solicitudes.md`); `MyAccess` con `en_proceso` o `revocando`. Patrón de `jobs-log.tsx`: estado `transitorios` calculado con cada respuesta; cambio de filtro o página recarga siempre.

## Impacto en elementos compartidos
- `usePolling`: sin cambios; sus usos (DIS-015, 018, 022, 024) no se afectan.
- `access-status-badge.tsx` y `request-status-badge.tsx`: solo se agregan exports (`hayAccesosTransitorios`, `ESTADOS_ACCESO_TRANSITORIOS`, `hayTransitoriosEnSolicitudes`); `request-status-badge` ahora importa de `access-status-badge` (usados por `approvals-inbox`, `user-access-panel`, inventario: sin cambio de comportamiento).
- Vistas cuyo comportamiento cambia: `MyRequests`, `MyAccess`.

## Verificación
- `tsc` 0, `lint` 0, `vitest` 0 (1499; accesibilidad 1065 en 0), `build` 0.
- Pruebas nuevas en `tests/components/access/my-requests-view.test.tsx` (3): se detiene sin transitorios, refresca con ellos, se detiene al desaparecer.
- No verificado en navegador (sin cambios visuales).

## Bitácora
- 2026-10-27: implementada; En revisión.
