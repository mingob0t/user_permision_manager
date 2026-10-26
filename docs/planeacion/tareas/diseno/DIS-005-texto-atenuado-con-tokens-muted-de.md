# DIS-005 — Texto atenuado con tokens muted de 4.5:1

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | tokens |
| **Prioridad** | Media |
| **Estatus** | En curso |
| **Responsable** | disenador-web |
| **Creada** | 2026-10-13 |
| **Inicio** | 2026-10-26 |
| **Finalizada** | |
| **Estatus Git** | Rama local |
| **Rama** | `dis/DIS-004-005-006-contraste` (conjunta con DIS-004, DIS-005 y DIS-006) |
| **Commits / PR** | |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
`text-label/60` 2.88-3.35, placeholder 1.61-1.75, tarjetas `opacity-70`.

Origen (diagnóstico inicial, FNC-001):
- [`docs/estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md): H-07, H-08

## Objetivo
Texto atenuado con 4.5:1 en los 7 temas: tokens `--color-bi-text-muted` y `--color-secondary`, pista de `Field` y tarjetas con opacidad.

## Alcance
- **Incluye:** pares `bi-text-muted/panel`, `bi-text-muted/surface-container`, `secondary/panel`; H-07 (`text-label/60` de `Field`, `opacity-70` de tarjetas).
- **No incluye:** rediseño visual; placeholder y `EmptyNote` (ya resueltos en DIS-013 y DIS-014).

## Decisiones (decisión del orquestador, pendiente de validar en la prueba de concepto)
| # | Decisión | Motivo |
|---|---|---|
| 1 | Oscurecer o aclarar solo la luminosidad HSL del mismo color hasta 4.55:1 | Mismo tono e intención; el mínimo cambio que cumple con margen de redondeo |
| 2 | `--color-secondary` solo cambia donde fallaba (SO oscuro, `html.dark`, obsidian); en claro, emerald y rose ya cumplía y no se toca | Alcance mínimo; en claro queda 1 punto RGB distinto de `bi-text-muted` |
| 3 | Pista de `Field`: `text-label/60` → `text-label/85` | Mismo patrón que `EmptyNote` (DIS-014), medido por `empty-note/panel` |
| 4 | Notificación leída: `opacity-70` → `opacity-85` | Conserva el atenuado; texto 5,18:1 mínimo (antes 3,62) |
| 5 | Plataforma sin enlace (`platform-card.tsx`): se quita `opacity-70` | Con cualquier opacidad la insignia de advertencia del tema claro baja de 4.5 (3,54 a 85 %); la insignia "Sin enlace" ya indica el estado |

## Cambios
| Archivo | Cambio |
|---|---|
| `frontend/src/styles/tokens.css` | `--color-bi-text-muted` (claro, emerald, rose, obsidian) y `--color-secondary` (SO oscuro, `html.dark`, obsidian) |
| `frontend/src/components/form.tsx` | Pista de `Field` a `text-label/85` |
| `frontend/src/components/notifications-list.tsx` | Tarjeta leída `opacity-85` |
| `frontend/src/components/platform-card.tsx` | Tarjeta sin enlace sin opacidad |
| `frontend/tests/accesibilidad/fallas-contraste-conocidas.ts` | Salen 8 celdas de DIS-005 |

## Contraste medido (antes → después)
| Par | claro | SO oscuro | `html.dark` | emerald | obsidian | rose | violet |
|---|---|---|---|---|---|---|---|
| `bi-text-muted/panel` | 4,76 → 5,03 | 6,96 | 6,96 | 4,80 → 5,01 | 3,67 → 5,45 | 4,80 → 5,01 | 7,34 |
| `bi-text-muted/surface-container` | 4,34 → 4,59 | 5,71 | 5,71 | 4,40 → 4,59 | 3,08 → 4,58 | 4,37 → 4,56 | 6,50 |
| `secondary/panel` | 4,76 | 3,75 → 4,55 | 3,75 → 4,55 | 4,80 | 3,67 → 4,59 | 4,80 | 7,34 |
| `text-label` en notificación leída | 4,38 → 6,67 | 3,95 → 5,32 | 4,05 → 5,37 | 3,62 → 5,18 | 3,95 → 5,30 | 3,65 → 5,21 | 3,93 → 5,28 |
| Pista de `Field` (`label/60` → `/85`) | 3,35 → pasa (`empty-note/panel`) | 3,31 → pasa | pasa | 2,88 → pasa | pasa | 2,88 → pasa | pasa |

Tarjetas con opacidad: medidas con un script de composición (texto y fondo compuestos sobre `--color-body-bg`), no con la prueba automática, que no modela la opacidad de un elemento.

## Elementos compartidos que cambian de color (para validar)
| Elemento | Cambio visible | Pantallas |
|---|---|---|
| `--color-bi-text-muted` (`text-bi-muted`) | Pista de `StatTile` apenas más oscura (claro, emerald, rose) o más clara (obsidian) | `/` (resumen por rol), `/dashboard` |
| `--color-secondary` | Solo en SO oscuro, `html.dark` y obsidian; sin consumidores React (CSS heredado `.kpi-conversion-bottom`, `.stacked-segment-secondary`) | — |
| `Field` (`form.tsx`) | Pista más legible | Todo formulario con pista: `/settings`, `/users`, `/areas`, diálogos de usuarios y de admin |
| Tarjeta de notificación leída | Menos atenuada | `/notifications` |
| `PlatformCard` sin enlace | Ya no se atenúa | `/platforms`, favoritos |

## Criterios de aceptación
- [ ] Hallazgos de origen corregidos y verificados
- [ ] Prueba de regresión que primero falla (si corrige un defecto)
- [ ] Pruebas mínimas del lineamiento de pruebas, ejecutadas
- [ ] Cumple `docs/estandarizacion/` y no duplica código existente
- [ ] Sin direcciones IP ni secretos

## Impacto cruzado
- Depende de → —

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-19 | FNC-070 (auditor-accesibilidad): `EmptyNote` `text-label/60` (3.35 claro, 3.31 oscuro) ya cubierto aquí; lo usan también las rutas reservadas de FNC-070 |
| 2026-10-19 | DIS-017 (auditor-accesibilidad): pista `text-label/60` de `Field` (`form.tsx:29`, 3.35 claro, 3.31 oscuro); DIS-017 usa su propia pista `text-label` fuera de `Field`; `form.tsx` sin tocar |
