# DIS-061 — Superficies y diálogos: `Card` con variantes, `PanelHeader`, `Modal` y `Drawer`

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 7 |
| **Módulo / Área** | componentes |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Responsable** | |
| **Creada** | 2026-10-27 |
| **Inicio** | |
| **Finalizada** | |
| **Estatus Git** | — |
| **Rama** | `dis/DIS-061-superficies-y-dialogos` |
| **Commits / PR** | |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- 4 tarjetas con el marcado de `Card` copiado; `PanelHeader` con 0 usos; menú móvil con `role="dialog"` propio (`mobile-menu.tsx:103`) (plan §2.6).
- Plan: [PLAN-FASE-7](../../PLAN-FASE-7-diseno-visual.md).

## Objetivo
Superficies (tarjeta, cabecera de panel, diálogo, panel lateral) con la matriz de tarjeta y diálogo.

## Alcance
- **Incluye:**
  - `Card` con `variant` (plana, enlace, seleccionable) y estados; migrar `platform-card.tsx:36`, `request-catalog-card.tsx:54`, `connector-param-fields.tsx:112`, `request-form-modal.tsx:115`
  - `PanelHeader`: adoptarlo donde aplique o retirarlo (decidir y anotar)
  - `Modal` con `superficie-elevada`, `sombra-3`, `dialogo-max`, botón cerrar con `Icono`
  - `Drawer` (base de `Modal`) y migrar el menú móvil
  - Retirar sus excepciones
- **No incluye:**
  - Animación y `scrollbar-gutter` (DIS-073)
  - `AlertDialog`/`ConfirmDialog` (DIS-074)
  - Contenido del menú (DIS-063)

## Archivos previstos
- `frontend/src/components/ui.tsx`
- `frontend/src/components/form.tsx` (`Modal`)
- `frontend/src/components/drawer.tsx` (nuevo)
- `mobile-menu.tsx`, tarjetas migradas

## Reutilización
`useFocusTrap`, `useScrollLock`, `.nx-modal-glass`.

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `Card` | componente | 66 usos | No |
| `Modal` | componente | 48 usos: todos los diálogos | No |
| Menú móvil | componente | todas las pantallas en móvil | No |

## Variables y configuración
Ninguna, salvo tokens de componente.

## Criterios de aceptación
- [ ] Foco atrapado y devuelto igual que hoy (DIS-031, pruebas en verde)
- [ ] Tarjeta-enlace con foco visible y hover sin mover contenido
- [ ] Desde `frontend/`: `npm run typecheck`, `npm run lint`, `npx vitest run` (incluye `tests/accesibilidad/`) y `npm run build` con código de salida 0
- [ ] Sin colores literales, sin estilos en línea, sin `dark:` ni clases de tema en TSX
- [ ] Verificada en navegador en tema claro y oscuro, a 360 px y 1280 px, y en los estados de carga, vacío y error que apliquen (nota o captura en la ficha)
- [ ] `auditor-accesibilidad` Aprobado (contraste medido en los 2 temas, foco, texto mínimo y área táctil)
- [ ] Tokens nuevos o cambiados registrados en `docs/configuracion/VARIABLES.md` y con motivo en `HISTORIAL.md`
- [ ] Sin direcciones IP ni secretos; cumple `docs/estandarizacion/` y no duplica componentes existentes
- [ ] `impacto.py` ejecutado y su tabla en esta ficha

## Impacto cruzado
- Genera → —
- Origen ← PLAN-FASE-7 §4.4
- Depende de → DIS-059

## Riesgos y reversión
`Modal` es compartido por 48 usos: pruebas de diálogo existentes.

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
