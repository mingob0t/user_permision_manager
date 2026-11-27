# DIS-151 — Resumen de Solicitudes: títulos cortos sin repetir «Solicitudes»

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Fase** | 8 |
| **Estatus** | Hecha |
| **Creada / Aprobada / Finalizada** | 2026-11-27 (el dueño eligió el juego «Cortos») |

## Cambios
| Panel | Antes | Ahora (título · subtítulo) |
|---|---|---|
| KPI estado | Solicitudes por estado | Por estado · N en total |
| KPI áreas | Solicitudes pendientes por área | Pendientes por área · N por aprobar |
| KPI usuarios / conectores | sin cambio | Usuarios / Conectores · N en total |
| Tabla | Solicitudes · Pendientes por aprobar | Por aprobar · Pendientes de tu decisión |
| Gráficas | Solicitudes por área / por plataforma | Áreas / Plataformas · Las 10 con más solicitudes |

- `DonaKpi`: prop opcional `textoTotal` (por defecto «en total»).
- Pruebas: `approvals-resumen.test.tsx` actualizada y caso DIS-151 (falló antes del cambio).

## Impacto en elementos compartidos
- `DonaKpi` (prop opcional, sin cambio por defecto) y `SolicitudesPanel`: únicos usos en el Resumen de `/approvals`.

## Verificación
- tsc 0, eslint 0, vitest completo 121 archivos / 3675 pruebas, salida 0.
