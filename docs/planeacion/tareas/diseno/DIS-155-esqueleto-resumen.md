# DIS-155 — Resumen de Solicitudes: esqueleto de carga con la forma de la pantalla

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Fase** | 8 |
| **Estatus** | Hecha |
| **Creada / Aprobada / Finalizada** | 2026-11-27 (captura del dueño: 3 rectángulos a todo lo ancho al entrar) |

## Cambios
- `access/approvals-resumen.tsx`: `EsqueletoResumen` con la rejilla real (4 KPI `min-h-52`; tabla 3/5 y dos gráficas 2/5), un solo `role="status"`; reemplaza `Skeleton variant="tarjeta" count={3}`.
- `ui.tsx`: exporta `CLASES_ESQUELETO` (las mismas clases base de `Skeleton`, sin cambio de aspecto).
- Prueba DIS-155 en `approvals-resumen.test.tsx` (falló antes del cambio).

## Impacto en elementos compartidos
- `ui.tsx`/`Skeleton`: solo se extrae la constante; el resto de usos de `Skeleton` no cambia.

## Nota
- En `next dev` la primera visita a una ruta compila y el esqueleto dura varios segundos; en producción es breve.

## Verificación
- tsc 0, eslint 0, vitest completo 121 archivos / 3679 pruebas, salida 0.
