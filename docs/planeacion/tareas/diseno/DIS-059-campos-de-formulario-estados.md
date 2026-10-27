# DIS-059 — Campos de formulario: estados completos (hover, foco, deshabilitado, solo lectura, inválido)

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 7 |
| **Módulo / Área** | componentes |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Responsable** | |
| **Creada** | 2026-10-27 |
| **Inicio** | |
| **Finalizada** | |
| **Estatus Git** | — |
| **Rama** | `dis/DIS-059-campos-de-formulario-estados` |
| **Commits / PR** | |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- `TextInput` usa `focus:` y la regla global `:focus` con halo al 10 %; deshabilitado con opacidades que se multiplican; `aria-invalid` sin estilo; 3 `<input>` crudos; `area-form.tsx:24` duplica `FieldErrorNote` (plan §2.4, §2.6).
- Plan: [PLAN-FASE-7](../../PLAN-FASE-7-diseno-visual.md).

## Objetivo
`Field`, `TextInput`, `TextArea`, `Select`, `Checkbox` y entradas de color y archivo con la fila de la matriz de campo, select y casilla.

## Alcance
- **Incluye:**
  - Retirar la normalización global `:where(input…)` y las reglas `select` duplicadas de `global.css`/`components.css` en favor del componente
  - Estados con utilidades de DIS-056; inválido por `aria-invalid`; solo lectura (`readOnly`) con su estilo; flecha del `select` con `Icono`
  - `ColorInput` y `FileInput` en `form.tsx`; migrar `settings/backup-tab.tsx:72`, `settings/portal-tab.tsx:104`, `access/request-form-modal.tsx:117`
  - `areas/area-form.tsx:24` a `FieldErrorNote`
  - Error de campo con línea reservada (sin empujar)
  - Retirar sus excepciones
- **No incluye:**
  - Textos o validaciones
  - Barras de filtros (DIS-069)
  - DIS-053 (campo «Color de texto»)

## Archivos previstos
- `frontend/src/components/form.tsx`
- `frontend/src/components/platforms/field-notes.tsx`
- `frontend/src/styles/components.css`, `global.css`
- Archivos migrados listados

## Reutilización
`FieldErrorNote`, `FieldHint`, `describedBy`, `focusFirstError`.

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `Field`/`TextInput`/`Select`/`Checkbox` | componentes | 108 + 38 + 50 + 13 usos: todos los formularios | No |
| Normalización global de inputs | CSS | controles nativos en todas las pantallas | No |

## Variables y configuración
Tokens de componente de campo, si hacen falta: registro y historial.

## Criterios de aceptación
- [ ] Un campo con `aria-invalid="true"` muestra borde de error ≥ 3:1 e ícono/nota, no solo color
- [ ] Deshabilitado y solo lectura distinguibles entre sí y del normal
- [ ] Desde `frontend/`: `npm run typecheck`, `npm run lint`, `npx vitest run` (incluye `tests/accesibilidad/`) y `npm run build` con código de salida 0
- [ ] Sin colores literales, sin estilos en línea, sin `dark:` ni clases de tema en TSX
- [ ] Verificada en navegador en tema claro y oscuro, a 360 px y 1280 px, y en los estados de carga, vacío y error que apliquen (nota o captura en la ficha)
- [ ] `auditor-accesibilidad` Aprobado (contraste medido en los 2 temas, foco, texto mínimo y área táctil)
- [ ] Tokens nuevos o cambiados registrados en `docs/configuracion/VARIABLES.md` y con motivo en `HISTORIAL.md`
- [ ] Sin direcciones IP ni secretos; cumple `docs/estandarizacion/` y no duplica componentes existentes
- [ ] `impacto.py` ejecutado y su tabla en esta ficha

## Impacto cruzado
- Genera → —
- Origen ← PLAN-FASE-7 §4.3, §4.4
- Depende de → DIS-058

## Riesgos y reversión
Quitar la normalización global afecta inputs sin componente: inventario previo con `patrones-unicos`.

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
