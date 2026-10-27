# DIS-062 — Avisos y estados: `Note` por tono (error, éxito, aviso, info), vacío, carga, insignias y toast

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
| **Rama** | `dis/DIS-062-avisos-y-estados-note` |
| **Commits / PR** | |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- Sin componente de aviso ni info; errores en `Card` a mano (`directory-tab.tsx:95-98`, `connector-panel.tsx:163-166`); 12 `role="alert"` envolviendo a mano; tintes de estado a mano (`missing-link-note.tsx:8`, `notifications-list.tsx:21-23`); `aria-busy` sin estilo (plan §2.4, §2.6).
- Plan: [PLAN-FASE-7](../../PLAN-FASE-7-diseno-visual.md).

## Objetivo
Un `Note` con tono (y `ErrorNote`/`SuccessNote` como atajos), `EmptyNote` con acción, `Spinner` acotado, `Badge` y toast con las familias de estado de DIS-055.

## Alcance
- **Incluye:**
  - `Note` (tono, ícono `icono-md`, título opcional, `role` correcto dentro del componente)
  - Migrar los avisos y envoltorios a mano listados
  - `EmptyNote` con acción opcional; `directory-picker.tsx:60`
  - Estilo de `aria-busy`; `Spinner` solo en botón o zona de alto fijo
  - `Badge` y `.nx-chip-*` con familias de estado; volver a medir los chips de DIS-048 en los 2 temas
  - Toast con tokens y botón cerrar 48 px
  - Retirar sus excepciones
- **No incluye:**
  - Esqueletos (DIS-073)
  - Diálogo de alerta (DIS-074) y la decisión diálogo/toast (DIS-075)

## Archivos previstos
- `frontend/src/components/ui.tsx`
- `frontend/src/components/toast.tsx`
- `frontend/src/styles/components.css` (`.nx-badge*`, `.nx-chip-*`)
- Archivos migrados listados

## Reutilización
`ErrorNote`, `SuccessNote`, `EmptyNote`, `Badge`, `Tone`, `useToast`, `RegionDeAnuncios`, `textoLegible`.

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `ErrorNote`/`SuccessNote`/`EmptyNote` | componentes | 79 + 13 + 23 usos | No |
| `Badge`/`.nx-chip-*` | componente/CSS | 43 usos; tarjetas de plataforma, áreas, administrar plataformas | No |

## Variables y configuración
Tokens de estado de componente, si hacen falta: registro y historial.

## Criterios de aceptación
- [ ] Los 4 tonos con texto ≥ 4.5:1 sobre su tinte y borde ≥ 3:1 en los 2 temas
- [ ] Chips de DIS-048 siguen ≥ 4.5:1 (medido)
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
Cambio de `role` de avisos altera lo que anuncia el lector de pantalla: pruebas de anuncio existentes.

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
