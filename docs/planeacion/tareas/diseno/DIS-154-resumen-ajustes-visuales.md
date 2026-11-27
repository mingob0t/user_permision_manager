# DIS-154 — Resumen de Solicitudes: barras sólidas, etiquetas sin recorte, leyenda sin desborde y nombres accesibles

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Fase** | 8 |
| **Estatus** | Hecha |
| **Creada / Aprobada / Finalizada** | 2026-11-27 (auditor-accesibilidad sobre DIS-147..152 y captura del dueño) |
| **Origen** | DIS-147, DIS-151, DIS-152 |

## Hallazgos que corrige
| Severidad | Hallazgo | Corrección |
|---|---|---|
| Media | Extremo del degradado de la barra a 2.13:1 en oscuro (≥ 3:1); con 0.9 aún 2.94 | Barras sólidas: 3.33 oscuro / 5.17 claro |
| Media (visto en captura) | Leyenda de Usuarios y Pendientes por área corta el porcentaje | `li` con `min-w-0` y porcentaje `shrink-0` en `DonaKpi` (el nombre se trunca) |
| Baja | Etiquetas del eje Y recortadas contra el borde («Jemo Infraestru…») | `ANCHO_ETIQUETA` 124 px y 15 caracteres |
| Baja | Nombres accesibles ambiguos tras títulos cortos | Prop `etiqueta` en `DonaKpi` y `GraficaBarras`: «Solicitudes por estado», «Solicitudes pendientes por área», «Solicitudes por área/plataforma» |

## Diagnóstico del «no carga todo»
- Captura sin interfaz (Playwright) a 1.5, 4, 8, 20 y 35 s: todo carga y se mantiene. Lo visto por el dueño era la recarga en caliente de `next dev` al integrar DIS-148..152 en la carpeta base; no ocurre en producción.

## Impacto en elementos compartidos
- `DonaKpi` (prop opcional, leyenda) y `GraficaBarras`: únicos usos en el Resumen de `/approvals`.

## Verificación
- tsc 0, eslint 0, vitest completo 121 archivos / 3678 pruebas, salida 0. Prueba DIS-154 falló antes del cambio.
