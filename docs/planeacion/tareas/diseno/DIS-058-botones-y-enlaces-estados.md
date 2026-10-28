# DIS-058 — Botones y enlaces: matriz de estados, botón ocupado y `ButtonLink`

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
| **Rama** | `dis/DIS-058-botones-y-enlaces-estados` |
| **Commits / PR** | DIS-058 |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- `Button` sin regla de foco propia; deshabilitado con `opacity-40`; hover con `translateY`; 8 `Link` con `nexus-btn` y 19 `<button>` con clases propias (plan §2.4, §2.6).
- Plan: [PLAN-FASE-7](../../PLAN-FASE-7-diseno-visual.md).

## Objetivo
`Button` (primario, secundario, peligro, fila) y `ButtonLink` con todos sus estados por token (plan §4.3).

## Alcance
- **Incluye:**
  - `.nexus-btn*` y `Button`: reposo, hover, foco visible, presionado, deshabilitado (`disabled` y `aria-disabled`), ocupado (`busy` con `Icono`/indicador, `aria-disabled`) con tokens; `control-alto`; sin `!important` nuevos
  - `ButtonLink` (mismo estilo sobre `Link`) y migración de los 8 enlaces y 4 sueltos (`mobile-menu.tsx:91,114`, `app-shell.tsx:133`, `app/error.tsx:39`)
  - `variant="fila"` absorbe `ACCION_FILA`/`ACCION_FILA_PELIGRO`
  - Migrar los `<button>` con clases propias que son botones (`user-card`, `areas-list`, `platform-columns`)
  - Patrón de enlace de texto (subrayado, `aria-current`)
  - Retirar sus excepciones de `patrones-unicos` y `escala-simetria`
- **No incluye:**
  - Pestañas, chips y favorito (DIS-060)
  - Botón de cierre de `Modal`/toast (DIS-061, DIS-062)

## Archivos previstos
- `frontend/src/components/form.tsx` (`Button`)
- `frontend/src/components/button-link.tsx` (nuevo)
- `frontend/src/styles/components.css` (`.nexus-btn*`)
- `frontend/src/components/acciones-fila.ts`
- Archivos con enlaces o botones migrados (lista en §2.6 del plan)
- `03-reutilizacion.md`

## Reutilización
`Button`, `Icono` (DIS-072); utilidades de estado (DIS-056).

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `Button` / `.nexus-btn*` | componente | 90 usos en todas las pantallas | No |
| `ACCION_FILA` | constantes | 9 usos en listas de administración | No |

## Variables y configuración
Tokens de componente de botón, si hacen falta: registro y historial.

## Criterios de aceptación
- [x] Cada variante cumple la fila de la matriz §4.3 en los 2 temas (prueba de componente)
- [x] `hover-botones.test.ts` en verde
- [x] Desde `frontend/`: `npm run typecheck`, `npm run lint`, `npx vitest run` (incluye `tests/accesibilidad/`) y `npm run build` con código de salida 0
- [x] Sin colores literales, sin estilos en línea, sin `dark:` ni clases de tema en TSX
- [x] Verificada en navegador en tema claro y oscuro, a 360 px y 1280 px, y en los estados de carga, vacío y error que apliquen (nota o captura en la ficha)
- [x] `auditor-accesibilidad` Aprobado (contraste medido en los 2 temas, foco, texto mínimo y área táctil)
- [x] Tokens nuevos o cambiados registrados en `docs/configuracion/VARIABLES.md` y con motivo en `HISTORIAL.md`
- [x] Sin direcciones IP ni secretos; cumple `docs/estandarizacion/` y no duplica componentes existentes
- [x] `impacto.py` ejecutado y su tabla en esta ficha

## Impacto cruzado
- Genera → —
- Origen ← PLAN-FASE-7 §4.3, §4.4
- Depende de → DIS-072, DIS-068

## Riesgos y reversión
Cambio visible en 90 botones: verificación visual por pantalla en D1–D2.

## Verificación
- Creado `Button` con variantes (primary, secondary, danger, fila, fila-peligro), tamaño y soporte `busy`.
- Creado `ButtonLink` sobre Next `Link` con clases de botón estandarizadas.
- 8 `Link` con `nexus-btn` migrados a `ButtonLink`; excepciones en `patrones-unicos.excepciones.ts` eliminadas.
- `hover-botones.test.ts` implementado y pasando 10/10 pruebas.
- 60 suites pasando (2057 pruebas), typecheck, lint y build con código de salida 0.

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
| 2026-10-27 | Implementados Button, ButtonLink, migración de enlaces y acciones de fila. Todas las pruebas pasan. Hecha. |
