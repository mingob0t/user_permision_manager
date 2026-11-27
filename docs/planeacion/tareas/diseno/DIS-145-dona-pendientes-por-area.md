# DIS-145 — Dona «Solicitudes pendientes por área»

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Fase** | 8 |
| **Estatus** | Hecha |
| **Creada / Aprobada / Finalizada** | 2026-11-27 (aprobada por pedido directo del dueño) |

## Contexto
- Dueño: la dona del Resumen de Solicitudes debe contar solo pendientes por área; la gráfica de barras «Solicitudes por área» no se toca.

## Cambios
- `access/dona-areas.tsx`: usa `stats.pending_by_area` (sin él, `[]`); título «Solicitudes pendientes por área»; vacío «Sin solicitudes pendientes». Misma lógica de 5 series / «Otras».
- `InboxStats.pending_by_area` ya existía en `lib/access/types.ts` (FNC-212); sin cambios.
- `tests/components/access/approvals-resumen.test.tsx`: fixture con `pending_by_area`; pruebas de título, vacío, leyenda y «Otras» ajustadas.

## Impacto en elementos compartidos
- Ninguno. `DonaAreas` solo se usa en `approvals-resumen.tsx` (Resumen de Solicitudes); `DonaKpi` y tokens sin cambios.

## Verificación
- Vitest del archivo 19/19; tsc, lint y suite: ver bitácora. Sin captura visual (sin cambios de estilo; mismos tokens y clases).
