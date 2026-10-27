# DIS-068 — Prueba «un patrón, un componente» e inventario de patrones en el catálogo

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 7 |
| **Módulo / Área** | estandarizacion |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Responsable** | |
| **Creada** | 2026-10-27 |
| **Inicio** | |
| **Finalizada** | |
| **Estatus Git** | — |
| **Rama** | `dis/DIS-068-prueba-un-patron-un-componente` |
| **Commits / PR** | |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- Patrones resueltos a mano: 19 `<button>` y 8 `Link` con `nexus-btn`, 17 `<h1>`, 4 tarjetas copiadas, 4 barras de filtros, 2 pestañas, 2 componentes de tabla (plan §2.6).
- Plan: [PLAN-FASE-7](../../PLAN-FASE-7-diseno-visual.md).

## Objetivo
Congelar el inventario: una prueba automática que impida marcado ad hoc donde ya existe (o existirá) el componente común, con excepciones que solo pueden bajar.

## Alcance
- **Incluye:**
  - `tests/accesibilidad/patrones-unicos.test.ts` y `patrones-unicos.excepciones.ts` (archivo:patrón, motivo, tarea que la retira)
  - Reglas: `<table>` solo en el componente de datos; `nexus-btn`/clases de botón solo en `Button`/`ButtonLink`; `<input>`/`<select>`/`<textarea>` solo en `form.tsx`; `role="dialog"`/`"alertdialog"` solo en `Modal`/`Drawer`/`AlertDialog`; `<h1>` solo en `PageHeader`; `role="tablist"` solo en `Tabs`; `bg-<estado>/NN` solo en `Note`/`Badge`
  - Inventario del plan §2.6 en `03-reutilizacion.md` (duplicados D-18 en adelante, con la tarea que los resuelve)
  - `02-comportamiento.md` (nuevo): regla «un patrón, un componente»
- **No incluye:**
  - Migrar marcado (lo hacen C1–D2)
  - Crear componentes

## Archivos previstos
- `frontend/tests/accesibilidad/patrones-unicos.test.ts` (nuevo)
- `frontend/tests/accesibilidad/patrones-unicos.excepciones.ts` (nuevo)
- `docs/estandarizacion/03-reutilizacion.md`
- `docs/estandarizacion/02-comportamiento.md` (nuevo)

## Reutilización
Estructura de `colores-literales.test.ts` y su archivo de excepciones.

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| Prueba nueva | prueba | todo `frontend/src` (falla con marcado ad hoc nuevo) | No |

## Variables y configuración
Ninguna.

## Criterios de aceptación
- [ ] La prueba pasa con las excepciones iniciales del inventario y falla al agregar un `<button className="nexus-btn">` nuevo (verificado)
- [ ] Cada excepción tiene motivo y tarea
- [ ] Pruebas en verde con código de salida 0
- [ ] Sin direcciones IP ni secretos

## Impacto cruzado
- Genera → —
- Origen ← Pedido del dueño 2026-10-27 (estandarizar y reutilizar); PLAN-FASE-7 §2.6, §4.4
- Depende de → DIS-054 (en paralelo con el bloque B)

## Riesgos y reversión
Falsos positivos por análisis de texto: excepciones con motivo.

## Verificación
Pendiente (tarea en Propuesta).

## Veredictos
| Agente | Veredicto | Fecha |
|---|---|---|
| tester | | |
| revisor | | |
| auditor-accesibilidad | | |

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-27 | Creada como Propuesta (planificador, PLAN-FASE-7) |
