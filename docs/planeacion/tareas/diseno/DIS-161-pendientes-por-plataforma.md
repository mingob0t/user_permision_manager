# DIS-161 — Gestión > área > plataformas: «Solicitudes pendientes» por plataforma

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Fase** | 8 |
| **Estatus** | Hecha |
| **Depende de** | FNC-219 (`inbox/stats.pending_by_platform`, contrato solicitudes 1.6) |
| **Creada / Aprobada / Finalizada** | 2026-11-28 (pedido del dueño) |

## Cambios
- `platforms/platform-columns.tsx`: columna «Solicitudes pendientes» (opción `pendientes`); la cifra es un enlace a `/approvals?status=pendiente&area_id=…&platform_id=…` (`rutaPendientesPlataforma`), que el Historial lee y limpia (DIS-163). Nombre accesible «Solicitudes pendientes: N, en {plataforma}. Abrir Historial.»; 48 px; `stopPropagation` para no seleccionar la fila (hallazgo de auditor-accesibilidad).
- `platform-admin.tsx`: `pendientesPorPlataforma` desde el mismo `inbox/stats` que ya consulta (DIS-137); sin datos, la columna no aparece.
- `lib/access/types.ts`: `InboxStats.pending_by_platform`.
- Pruebas: `platforms/platform-columns-pendientes.test.tsx` y una en `platform-admin.test.tsx` (fallaron antes del cambio).

## Decisiones
- Se integra después de FNC-219: sin el campo, la columna mostraría 0 en todas.

## Impacto en elementos compartidos
- `columnasPlataformas`: opción nueva opcional; solo `platform-admin.tsx` la usa.
