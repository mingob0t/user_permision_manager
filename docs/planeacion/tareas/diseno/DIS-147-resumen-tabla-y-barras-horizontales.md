# DIS-147 — Resumen de Solicitudes: tabla a la izquierda y barras horizontales

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Fase** | 8 |
| **Estatus** | Hecha |
| **Creada / Aprobada / Finalizada** | 2026-11-27 (aprobada por pedido directo del dueño) |

## Cambios
- `access/approvals-resumen.tsx`: `SolicitudesPanel` a la izquierda (`lg:col-span-3`) y las dos gráficas apiladas a la derecha (`lg:col-span-2`); en móvil primero la tabla. Altura flex-1/min-h-0 intacta.
- `dashboard/grafica-barras.tsx`: `layout="vertical"` (categoría en eje Y, cantidad en eje X); etiquetas del eje Y con elipsis y `<title>` con el nombre completo; alto según filas (mín. 120 px, 32 px por fila); mantiene tabla `srOnly`, estado vacío, tokens, prop `alterna`.
- Pruebas: `approvals-resumen.test.tsx` (orden y columnas 3/5 – 2/5).

## Impacto en elementos compartidos
- `GraficaBarras` modificado; su único uso es `approvals-resumen.tsx` (vista `/approvals`, Resumen). Sin tokens ni CSS nuevos.

## Verificación
- tsc, eslint y vitest completos: ver bitácora. Sin captura visual en tema claro/oscuro ni móvil (no verificada).
