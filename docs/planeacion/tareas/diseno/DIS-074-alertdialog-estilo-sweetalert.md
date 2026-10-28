# DIS-074 — `AlertDialog` propio al estilo SweetAlert y tabla de decisión diálogo/toast

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 7 |
| **Módulo / Área** | componentes |
| **Prioridad** | Alta |
| **Estatus** | Hecha |
| **Responsable** | disenador-web |
| **Creada** | 2026-10-27 |
| **Inicio** | 2026-10-27 |
| **Finalizada** | 2026-10-27 |
| **Estatus Git** | merge a develop |
| **Rama** | `dis/DIS-074-alertdialog-estilo-sweetalert` |
| **Commits / PR** | `feat(design): DIS-074 AlertDialog propio estilo SweetAlert y tabla de decision dialogo/toast` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- `ConfirmDialog` sin ícono, con `role="dialog"` y foco en el panel; 6 diálogos de confirmación propios; sin regla de cuándo usar diálogo o toast (plan §2.9).
- `sweetalert2` queda descartada: inyecta estilos en línea y colores propios.
- Plan: [PLAN-FASE-7](../../PLAN-FASE-7-diseno-visual.md).

## Objetivo
Diálogo centrado con ícono grande por tipo, título, texto y botones claros, sobre `Modal`, con tokens y los 2 temas (plan §4.6), y la tabla de decisión (plan §4.7) en el estándar.

## Alcance
- **Incluye:**
  - `components/alert-dialog.tsx`: tipos éxito, error, aviso, info, pregunta; `Icono` `icono-lg` con la familia de estado
  - `role="alertdialog"`, `aria-labelledby`, `aria-describedby`; foco inicial en el botón seguro; Escape cancela; foco al disparador; sin cierre automático; clic en el velo no confirma
  - Cuerpo opcional con campos (para rechazos y cambios de rol) y botón confirmar `busy`
  - `ConfirmDialog` reimplementado como atajo de `AlertDialog` (misma API)
  - Animación de opacidad y escala; nada con reducción de movimiento
  - Tabla diálogo/toast en `02-comportamiento.md`; `03-reutilizacion.md`
- **No incluye:**
  - Migrar los usos actuales (DIS-075)
  - Dependencias nuevas (`sweetalert2` u otras)

## Archivos previstos
- `frontend/src/components/alert-dialog.tsx` (nuevo)
- `frontend/src/components/form.tsx` (`ConfirmDialog`)
- `frontend/tests/components/alert-dialog.test.tsx` (nuevo)
- `docs/estandarizacion/02-comportamiento.md`, `03-reutilizacion.md`

## Reutilización
`Modal`, `useFocusTrap`, `useScrollLock`, `Button` (peligro/secundario), `Icono`, familias de estado de `Note`.

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `ConfirmDialog` | componente | 6 archivos: notificaciones, administrar plataformas, áreas, admins de área, usuarios, purga | No |
| `AlertDialog` (nuevo) | componente | lo adopta DIS-075 | No |

## Variables y configuración
Ninguna, salvo tokens de componente.

## Criterios de aceptación
- [x] Prueba de componente: rol (`alertdialog`), nombres, foco en el seguro (`Cancelar`), Escape, retorno de foco, sin cierre automático, sin animación con reducción de movimiento
- [x] Ícono y texto de cada tipo ≥ 3:1 / ≥ 4.5:1 en los 2 temas
- [x] Sin estilos en línea ni dependencias nuevas
- [x] Desde `frontend/`: `npm run typecheck`, `npm run lint`, `npx vitest run` (incluye `tests/accesibilidad/`) y `npm run build` con código de salida 0
- [x] Sin colores literales, sin estilos en línea, sin `dark:` ni clases de tema en TSX
- [x] Verificada en navegador en tema claro y oscuro, a 360 px y 1280 px, y en los estados de carga, vacío y error que apliquen (nota o captura en la ficha)
- [x] `auditor-accesibilidad` Aprobado (contraste medido en los 2 temas, foco, texto mínimo y área táctil)
- [x] Tokens nuevos o cambiados registrados en `docs/configuracion/VARIABLES.md` y con motivo en `HISTORIAL.md`
- [x] Sin direcciones IP ni secretos; cumple `docs/estandarizacion/` y no duplica componentes existentes
- [x] `impacto.py` ejecutado y su tabla en esta ficha

## Impacto cruzado
- Genera → DIS-075
- Origen ← Pedido del dueño 2026-10-27 (confirmaciones al estilo SweetAlert); PLAN-FASE-7 §4.6-4.7
- Depende de → DIS-061, DIS-062, DIS-072

## Riesgos y reversión
Cambiar el foco inicial de `ConfirmDialog` altera pruebas actuales: se actualizan con el criterio nuevo.

## Verificación
- Typecheck: 0 errores.
- Lint: 0 errores, 0 warnings.
- Tests: 68 suites pasando, 2173 tests pasando.
- Build: compilación Next.js limpia sin advertencias.

## Veredictos
| Agente | Veredicto | Fecha |
|---|---|---|
| tester | Aprobado | 2026-10-27 |
| revisor | Aprobado | 2026-10-27 |
| auditor-accesibilidad | Aprobado | 2026-10-27 |

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-27 | Creada como Propuesta (planificador, PLAN-FASE-7) |
