# DIS-050 — Mis solicitudes y mis accesos: anunciar los cambios de estado

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | solicitudes |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Rama** | `dis/DIS-050-anunciar-cambios-de-estado` |
| **Creada** | 2026-10-27 |

## Contexto
- Observación del `auditor-accesibilidad` en DIS-033: `my-requests.tsx` y `my-access.tsx` no tienen región `aria-live`; un lector de pantalla no anuncia que `en_proceso` pasó a `activo` (ni antes ni después de DIS-033).

## Objetivo
- Región `polite` que anuncie solo los cambios de estado entre una respuesta y la siguiente, no cada refresco.
- Pruebas de componente.

## Impacto cruzado
- Origen ← DIS-033
