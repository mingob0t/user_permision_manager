# DIS-149 — Resumen de Solicitudes sin scroll de página (corrección de DIS-147)

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Fase** | 8 |
| **Estatus** | Hecha |
| **Creada / Aprobada / Finalizada** | 2026-11-27 (reporte del dueño: «¿por qué habilitaste el scroll y dejaste de ser responsivo?») |
| **Origen** | DIS-147 |

## Reproducir (antes)
1. `/approvals` con 10 plataformas con solicitudes (datos demo locales).
2. Obtenido: la columna de gráficas crece (alto mínimo 32 px × filas + 28 por gráfica) y la página hace scroll; no se adapta al alto disponible.
3. Esperado: como antes de DIS-147, el Resumen llena la pantalla y las gráficas se encogen con su columna.

## Causa
- `grafica-barras.tsx` (DIS-147): `ResponsiveContainer minHeight={altoGrafica}` y se quitó `h-56`; la columna derecha de `approvals-resumen.tsx` no tenía `min-h-0`.

## Cambios
- `grafica-barras.tsx`: sin alto mínimo por filas; vuelve `h-56 flex-1 min-h-0` (las barras horizontales se ajustan al alto).
- `approvals-resumen.tsx`: columna de gráficas con `min-h-0`.
- Prueba de regresión en `approvals-resumen.test.tsx` (DIS-149), falló antes del cambio.

## Impacto en elementos compartidos
- `GraficaBarras`: único uso en el Resumen de `/approvals`.

## Verificación
- tsc 0, eslint 0, vitest completo 121 archivos / 3673 pruebas, salida 0. Sin captura visual (no verificada).
