# DIS-004 — Botones: texto sobre primary por token, peligro y advertencia, hover del secundario

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | componentes |
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
`.nexus-btn-primary` fuerza blanco (`components.css:1526-1530`): 2.56-4.23 según tema.

Origen (diagnóstico inicial, FNC-001):
- [`docs/estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md): H-05, H-09

## Objetivo
Texto de los botones con contraste AA (4.5:1) en los 7 temas, solo por tokens.

## Alcance
- **Incluye:** par `button-text/button-bg`; botón `danger` de `form.tsx`; medir el hover de `.nexus-btn-secondary` (H-09).
- **No incluye:** botón primario (DIS-015); rediseño visual (lo hace el dueño); cambiar a `danger` los diálogos que hoy usan primario por la falla anterior (propuesta DIS-043).

## Decisiones (decisión del orquestador, pendiente de validar en la prueba de concepto)
| # | Decisión | Motivo |
|---|---|---|
| 1 | `--color-button-bg`/`-text` = `var(--color-primary-solid)`/`var(--color-on-primary)` en los 5 bloques que los declaran | Mismo arreglo que la pestaña activa (DIS-001); sin consumidores en clases ni componentes |
| 2 | Tokens nuevos `--color-error-solid` (Red-600 `220 38 38`) y `--color-on-error` (blanco) en los 7 temas; obsidian `var(--color-error)` + `9 9 11` | Un paso más oscuro del mismo rojo, como `primary-solid` (DIS-001); obsidian conserva su texto oscuro sobre relleno claro (5,29:1) |
| 3 | `danger` = `nexus-btn-primary !bg-error-solid !text-on-error shadow-error/20` | Mismo patrón de override que ya tenía; la sombra conserva `error` |
| 4 | Botón de advertencia: no se crea | No existe ninguna variante ni botón de advertencia en `src/`; crear tokens sin consumidor queda fuera del alcance |
| 5 | Hover del secundario: sin cambio de valores | Ya usa `--color-primary-text` (DIS-001): 4,95–7,69:1; se agregan pares para fijarlo |

## Cambios
| Archivo | Cambio |
|---|---|
| `frontend/src/styles/tokens.css` | `--color-button-bg/-text` por referencia; `--color-error-solid` y `--color-on-error` en los 7 bloques |
| `frontend/tailwind.config.ts` | Utilidades `error-solid` y `on-error` |
| `frontend/src/components/form.tsx` | Variante `danger` de `Button` con los tokens nuevos |
| `frontend/tests/accesibilidad/pares-contraste.ts` | Pares `on-error/error-solid`, `btn-secondary-hover/panel` y `/body-bg` |
| `frontend/tests/accesibilidad/fallas-contraste-conocidas.ts` | Sale `button-text/button-bg` (3 celdas) |

## Contraste medido (antes → después)
| Par | claro | SO oscuro | `html.dark` | emerald | obsidian | rose | violet |
|---|---|---|---|---|---|---|---|
| `button-text/button-bg` | 5,17 → 5,17 | 5,17 → 5,17 | 5,17 → 5,17 | 3,77 → 5,48 | 7,76 → 7,76 | 3,67 → 4,70 | 4,23 → 5,70 |
| texto de `danger` | 3,76 → 4,83 | 3,76 → 4,83 | 3,76 → 4,83 | 3,76 → 4,83 | 5,29 → 5,29 | 3,76 → 4,83 | 3,76 → 4,83 |
| hover secundario sobre panel | 6,26 | 6,74 | 6,74 | 5,17 | 6,42 | 5,89 | 6,61 |

## Elementos compartidos que cambian de color (para validar)
| Elemento | Cambio visible | Pantallas |
|---|---|---|
| `Button variant="danger"` (`form.tsx`) | Relleno rojo un tono más oscuro (Red-500 → Red-600), salvo obsidian | `/notifications` (Vaciar), `/users` (Purgar cuentas) y todo `ConfirmDialog`: `/admin/platforms`, `/areas` (áreas y administradores de área), `/users`, `/notifications`, bandeja de aprobaciones (`approve-dialog`) |
| `--color-button-bg/-text`, utilidades `bg-button-bg`/`text-button-text` | Ninguno visible (sin consumidores) | — |

## Criterios de aceptación
- [ ] Hallazgos de origen corregidos y verificados
- [ ] Prueba de regresión que primero falla (si corrige un defecto)
- [ ] Pruebas mínimas del lineamiento de pruebas, ejecutadas
- [ ] Cumple `docs/estandarizacion/` y no duplica código existente
- [ ] Sin direcciones IP ni secretos

## Impacto cruzado
- Depende de → Depende de DIS-001

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-19 | DIS-002 (revisión): botón `danger` (`form.tsx:84`, `!bg-error`) texto blanco sobre `#ef4444` = 3.76:1 (falla previa, sin cambio en DIS-002). Proponer `--color-error-solid` + `--color-on-error`, como DIS-001 hizo con `primary-solid`/`on-primary` |
| 2026-10-20 | Parte del botón primario resuelta en DIS-015 (auditor-accesibilidad): `.nexus-btn-primary` (`components.css`) usa `--color-primary-solid` y `--color-on-primary` (antes `--color-primary` con blanco: obsidian 2,56, rose 3,67, emerald 3,77, violet 4,23); par `nexus-btn-primary` en la prueba de contraste, pasa en los 7 temas. Sigue pendiente: el par `button-text/button-bg` (tokens `--color-button-*`, sin uso en clases ni componentes; falla conocida en emerald, rose y violet), el botón `danger` (3,76:1) y advertencia/hover del secundario |
