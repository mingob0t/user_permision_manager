# DIS-063 — Marco e identidad: cabecera, barra lateral, menú móvil, ítem de menú, login y páginas 404/500

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 7 |
| **Módulo / Área** | marco |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Responsable** | |
| **Creada** | 2026-10-27 |
| **Inicio** | |
| **Finalizada** | |
| **Estatus Git** | — |
| **Rama** | `dis/DIS-063-marco-e-identidad` |
| **Commits / PR** | |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- La cabecera usa `bg-panel-fill` y no sus tokens; «Nexus» en texto en 3 lugares; ítem de menú con su propia receta de seleccionado (plan §2.2, §2.4).
- Plan: [PLAN-FASE-7](../../PLAN-FASE-7-diseno-visual.md).

## Objetivo
Marco del portal con la identidad del dueño (o propuesta neutra) y el ítem de menú de la matriz.

## Alcance
- **Incluye:**
  - `AppShell`: cabecera y barra lateral con tokens de superficie; logo con tamaño fijo (o nombre en texto)
  - Ítem de menú: reposo, hover, foco, presionado, actual (`aria-current`)
  - Login, `error.tsx` y `not-found.tsx` con la misma identidad
  - Favicon si hay logo
- **No incluye:**
  - Rutas o permisos del menú
  - Selector de tema (DIS-054)

## Archivos previstos
- `frontend/src/components/app-shell.tsx`
- `frontend/src/components/mobile-menu.tsx` (contenido)
- `frontend/src/components/login-form.tsx`
- `frontend/src/app/error.tsx`, `not-found.tsx`
- `frontend/public/` (logo y favicon, si los da el dueño)

## Reutilización
`Drawer` (DIS-061), `ButtonLink` (DIS-058), `Icono` (DIS-072).

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `AppShell` | componente | todas las pantallas con marco | No |

## Variables y configuración
Ninguna.

## Criterios de aceptación
- [ ] Logo con `width`/`height` fijos (sin salto)
- [ ] Ítem actual distinguible sin color
- [ ] Desde `frontend/`: `npm run typecheck`, `npm run lint`, `npx vitest run` (incluye `tests/accesibilidad/`) y `npm run build` con código de salida 0
- [ ] Sin colores literales, sin estilos en línea, sin `dark:` ni clases de tema en TSX
- [ ] Verificada en navegador en tema claro y oscuro, a 360 px y 1280 px, y en los estados de carga, vacío y error que apliquen (nota o captura en la ficha)
- [ ] `auditor-accesibilidad` Aprobado (contraste medido en los 2 temas, foco, texto mínimo y área táctil)
- [ ] Tokens nuevos o cambiados registrados en `docs/configuracion/VARIABLES.md` y con motivo en `HISTORIAL.md`
- [ ] Sin direcciones IP ni secretos; cumple `docs/estandarizacion/` y no duplica componentes existentes
- [ ] `impacto.py` ejecutado y su tabla en esta ficha

## Impacto cruzado
- Genera → —
- Origen ← PLAN-FASE-7 §4.3, §6
- Depende de → DIS-061; logo del dueño (o nombre en texto)

## Riesgos y reversión
Afecta a todas las pantallas: verificación visual general.

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
