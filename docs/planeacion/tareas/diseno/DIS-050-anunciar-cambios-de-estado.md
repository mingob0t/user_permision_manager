# DIS-050 — Mis solicitudes y mis accesos: anunciar los cambios de estado

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | solicitudes |
| **Prioridad** | Baja |
| **Estatus** | En revisión |
| **Rama** | `dis/DIS-050-anunciar-cambios-de-estado` |
| **Creada** | 2026-10-27 |

## Contexto
- Observación del `auditor-accesibilidad` en DIS-033: `my-requests.tsx` y `my-access.tsx` no tienen región `aria-live`; un lector de pantalla no anuncia que `en_proceso` pasó a `activo` (ni antes ni después de DIS-033).

## Objetivo
- Región `polite` que anuncie solo los cambios de estado entre una respuesta y la siguiente, no cada refresco.
- Pruebas de componente.

## Impacto cruzado
- Origen ← DIS-033

## Implementación
- `frontend/src/lib/use-cambios-de-estado.ts`: hook `useCambiosDeEstado(items, contexto, estadosDe)`; compara cada estado con la respuesta anterior y devuelve solo el texto de lo que cambió.
- `frontend/src/components/region-de-anuncios.tsx`: `RegionDeAnuncios`, `aria-live="polite"` con `sr-only`, siempre montada.
- `my-requests.tsx` (estado de la solicitud y del acceso derivado) y `my-access.tsx`: anuncian «Acceso a X: Con acceso».
- La primera respuesta de cada filtro/página es solo línea base: no se anuncia. Un refresco igual no anuncia. Un elemento que sale de la lista por el filtro tampoco.
- Decisión del orquestador (pendiente de validar en la prueba de concepto): región sin `role="status"` (el `Spinner` ya lo usa y duplicaría el rol); hook y región en `lib/` y `components/` para reutilizarlos en otras pantallas.
- Decisión del orquestador (pendiente de validar en la prueba de concepto): el texto anunciado reutiliza las etiquetas de los badges, sin textos nuevos.

## Impacto en elementos compartidos
- Ninguno modificado. Nuevos: `useCambiosDeEstado` y `RegionDeAnuncios` (catálogo `03-reutilizacion.md`); sus únicos usos son `my-requests.tsx` y `my-access.tsx` (vista `/requests`, pestañas Mis solicitudes y Mis accesos).
- Exportaciones de `access-status-badge.tsx` (`ESTADOS`) solo importadas, sin cambios.

## Verificación
- `tests/components/access/anuncio-de-estado.test.tsx`: anuncia un cambio, no anuncia sin cambios, no anuncia en la carga inicial (+ solicitudes).
- typecheck 0, lint 0, vitest 0 (1525), build 0; pruebas de accesibilidad 0 fallas (1070 ok).
- No verificado en navegador ni con lector de pantalla real. `auditor-accesibilidad` pendiente de ejecutar.

## Bitácora
- 2026-10-27: Propuesta → En curso → En revisión (autoaprobada en modo autónomo).
