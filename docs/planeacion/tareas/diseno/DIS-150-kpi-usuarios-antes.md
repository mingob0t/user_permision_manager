# DIS-150 — Resumen de Solicitudes: KPI Usuarios antes que Conectores

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Fase** | 8 |
| **Estatus** | Hecha |
| **Creada / Aprobada / Finalizada** | 2026-11-27 (aprobada por pedido directo del dueño) |

## Cambios
- `access/approvals-resumen.tsx`: orden de la fila de KPI = Por estado, Pendientes por área, Usuarios, Conectores.
- Prueba `approvals-resumen.test.tsx` (DIS-150), falló antes del cambio.

## Impacto en elementos compartidos
- Ninguno; solo el Resumen de `/approvals`.

## Verificación
- tsc 0, eslint 0, vitest completo 121 archivos / 3674 pruebas, salida 0.
