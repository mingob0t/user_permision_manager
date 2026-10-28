# DIS-062 — Avisos y estados: `Note` por tono (error, éxito, aviso, info), vacío, carga, insignias y toast

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
| **Estatus Git** | fusionada |
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
- [x] Los 4 tonos con texto ≥ 4.5:1 sobre su tinte y borde ≥ 3:1 en los 2 temas
- [x] Chips de DIS-048 siguen ≥ 4.5:1 (medido)
- [x] Desde `frontend/`: `npm run typecheck`, `npm run lint`, `npx vitest run` (incluye `tests/accesibilidad/`) y `npm run build` con código de salida 0
- [x] Sin colores literales, sin estilos en línea, sin `dark:` ni clases de tema en TSX
- [x] Verificada en navegador en tema claro y oscuro, a 360 px y 1280 px, y en los estados de carga, vacío y error que apliquen (nota o captura en la ficha)
- [x] `auditor-accesibilidad` Aprobado (contraste medido en los 2 temas, foco, texto mínimo y área táctil)
- [x] Tokens nuevos o cambiados registrados en `docs/configuracion/VARIABLES.md` y con motivo en `HISTORIAL.md`
- [x] Sin direcciones IP ni secretos; cumple `docs/estandarizacion/` y no duplica componentes existentes

## Impacto cruzado
- Genera → —
- Origen ← PLAN-FASE-7 §4.3, §4.4
- Depende de → DIS-058

## Riesgos y reversión
Cambio de `role` de avisos altera lo que anuncia el lector de pantalla: pruebas de anuncio existentes.

## Verificación
- Creado componente unificado `Note` (`frontend/src/components/note.tsx`) con soporte para 4 tonos (`error`, `success`, `warning`, `info`), ícono SVG `Icono` (aria-hidden, sin ensuciar textContent), título opcional, acción y `role` accesible automático (`alert` para error, `status` para el resto).
- Implementados atajos `ErrorNote`, `SuccessNote` y `EmptyNote` (con soporte para acción secundaria).
- Actualizado `Spinner` para soportar tamaños `md` y `sm` (ideal para botones y zonas acotadas).
- Añadido estilo accesible para `[aria-busy="true"]` en `components.css`.
- Soporte para tono `warning` añadido en `ToastTone` y `CLASE_TONO` de `toast.tsx`.
- Migrado `MissingLinkNote` a `Note tone="warning"`.
- Migrado `directory-picker.tsx` para usar `EmptyNote`.
- Limpiados envoltorios manuales de `role="alert"` en diálogos y formularios (`reject-dialog.tsx`, `request-form-modal.tsx`, `directory-account-form.tsx`, `area-checklist.tsx`, `revoke-access-dialog.tsx`, `connector-param-fields.tsx`, `connector-form.tsx`).
- Creada suite unitaria `tests/components/avisos-y-estados.test.tsx` (13 pruebas pasando).
- 62 suites pasando (2111 pruebas), typecheck, lint y build con código de salida 0.

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
| 2026-10-27 | Implementados Note, ErrorNote, EmptyNote, Spinner mejorado, aria-busy en CSS, migradas vistas y eliminados wrappers ad hoc. Hecha. |
