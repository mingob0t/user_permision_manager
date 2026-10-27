# DIS-060 — Pestañas y conmutadores: componente `Tabs` único y `ToggleChip`

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
| **Rama** | `dis/DIS-060-pestanas-y-conmutadores` |
| **Commits / PR** | |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- Dos pestañas idénticas a mano (`settings-panel.tsx:58-77`, `access/my-requests-view.tsx:86-108`); chips de `tag-picker` y favorito con su propia receta de seleccionado (plan §2.4, §2.6).
- Plan: [PLAN-FASE-7](../../PLAN-FASE-7-diseno-visual.md).

## Objetivo
Un `Tabs` y un `ToggleChip` con los estados de la matriz (pestaña, chip).

## Alcance
- **Incluye:**
  - `components/tabs.tsx`: `role="tablist"`, teclado WAI-ARIA con `destinoPorTecla`, *roving tabindex*, estados reposo/hover/foco/presionado/seleccionado/deshabilitado
  - Migrar `settings-panel` y `my-requests-view`
  - `components/toggle-chip.tsx` con `aria-pressed`; migrar `users/tag-picker.tsx` y `favorite-button.tsx`
  - Retirar sus excepciones
- **No incluye:**
  - Contenido de las pestañas
  - Ítem de menú (DIS-063)

## Archivos previstos
- `frontend/src/components/tabs.tsx` (nuevo)
- `frontend/src/components/toggle-chip.tsx` (nuevo)
- `settings-panel.tsx`, `access/my-requests-view.tsx`, `users/tag-picker.tsx`, `favorite-button.tsx`
- `03-reutilizacion.md`

## Reutilización
`destinoPorTecla` (`my-requests-view.tsx`), `tabId`/`panelId` (`settings/`).

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `Tabs` (nuevo) | componente | Ajustes, Mis solicitudes y accesos | No |
| `ToggleChip` (nuevo) | componente | Usuarios (etiquetas), tarjetas de plataforma (favorito) | No |

## Variables y configuración
Ninguna, salvo tokens de componente.

## Criterios de aceptación
- [ ] Teclado igual al actual (pruebas existentes en verde) y seleccionado distinguible sin color (borde/indicador ≥ 3:1)
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
- Depende de → DIS-072, DIS-068

## Riesgos y reversión
Regresión de teclado: pruebas de componente actuales.

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
