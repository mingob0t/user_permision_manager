# DIS-157 — Historial de solicitudes: sin descripción y error de carga en toast

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Fase** | 8 |
| **Estatus** | Hecha |
| **Creada / Aprobada / Finalizada** | 2026-11-28 (captura del dueño) |

## Cambios
- `access/approvals-view.tsx`: el Historial ya no lleva la descripción «Consulta con filtros…» (el h1 `sr-only` se conserva).
- `access/approvals-inbox.tsx`: el error de carga ya no es un recuadro `ErrorNote` sobre la tabla; sale con `useToast().avisar('error', …)`, una vez por racha de fallos (los reintentos de `usePolling` no lo repiten; una carga correcta lo rearma). Con datos la tabla sigue; sin datos queda «No se pudo cargar la lista.» y «Reintentar» (`aria-label` específico).
- Pruebas en `approvals-inbox.test.tsx` (fallaron antes del cambio).

## Impacto en elementos compartidos
- Ninguno: `toast.tsx`, `PageHeader` y `usePolling` se usan sin cambios.

## Notas
- «Todas» responde 400: FNC-218 (backend de `status=todas` y `q`) sigue en curso; no es de esta tarea.
- auditor-accesibilidad: una falla menor (Reintentar suelto tras cerrarse el toast), corregida.
