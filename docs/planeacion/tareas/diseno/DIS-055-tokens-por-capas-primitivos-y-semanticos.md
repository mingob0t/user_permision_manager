# DIS-055 — Tokens por capas: primitivos (paleta) y semánticos por rol, con alias de los heredados

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 7 |
| **Módulo / Área** | tokens |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Responsable** | |
| **Creada** | 2026-10-27 |
| **Inicio** | |
| **Finalizada** | |
| **Estatus Git** | — |
| **Rama** | `dis/DIS-055-tokens-por-capas-primitivos-y-semanticos` |
| **Commits / PR** | |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- 99 tokens con nombres por pantalla (`bi-*`, `ntf-*`, `tab-*`), 23 sin uso y roles duplicados (plan §2.1).
- El oscuro hereda 22 tokens del claro (p. ej. `--color-button-disabled-bg`).
- Dos formatos de valor (hex y canales).
- Plan: [PLAN-FASE-7](../../PLAN-FASE-7-diseno-visual.md).

## Objetivo
Modelo primitivos → semánticos (plan §4.1-4.2) con la paleta del dueño o la propuesta neutra; los nombres heredados quedan como alias con el mismo valor.

## Alcance
- **Incluye:**
  - Primitivos (neutro, marca, rojo, verde, ámbar, azul) solo en `tokens.css`
  - Semánticos de superficie, texto, borde, acento/acción y estado en claro y oscuro, todos en canales `R G B`
  - Alias: cada token heredado apunta a su semántico (`--color-label-text: var(--color-texto-secundario)`)
  - Retirar los 23 tokens sin uso
  - `tailwind.config.ts`: utilidades de los semánticos
  - Pares de contraste de cada semántico; prueba de completitud (todo semántico en los 2 temas; primitivos solo en `tokens.css`)
  - `docs/estandarizacion/01-visual.md` (capas, roles, regla de uso)
- **No incluye:**
  - Tokens de interacción (DIS-056), escalas (DIS-057, DIS-072)
  - Cambiar componentes o pantallas
  - Retirar alias (DIS-067)

## Archivos previstos
- `frontend/src/styles/tokens.css`
- `frontend/tailwind.config.ts`
- `frontend/tests/accesibilidad/pares-contraste.ts`, prueba nueva de completitud
- `docs/estandarizacion/01-visual.md` (nuevo), `VARIABLES.md`, `HISTORIAL.md`

## Reutilización
`tests/utils/tokens-css.ts` y `medir.ts` para medir; reglas DIS-001/DIS-002 (texto de marca y estado) se conservan con los nombres nuevos.

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| Todos los tokens de color | tokens | todas las pantallas (sin cambio visual salvo la paleta aprobada) | No |
| `tailwind.config.ts` | configuración | todas las utilidades de color | No |

## Variables y configuración
Tokens semánticos nuevos y retirados: registro y historial (motivo: plan de fase 7).

## Criterios de aceptación
- [ ] Sin cambio visual con la paleta neutra salvo los 22 tokens que el oscuro heredaba del claro (medidos)
- [ ] Cada semántico de texto ≥ 4.5:1 y de borde de control ≥ 3:1 en los 2 temas
- [ ] Desde `frontend/`: `npm run typecheck`, `npm run lint`, `npx vitest run` (incluye `tests/accesibilidad/`) y `npm run build` con código de salida 0
- [ ] Sin colores literales, sin estilos en línea, sin `dark:` ni clases de tema en TSX
- [ ] Verificada en navegador en tema claro y oscuro, a 360 px y 1280 px, y en los estados de carga, vacío y error que apliquen (nota o captura en la ficha)
- [ ] `auditor-accesibilidad` Aprobado (contraste medido en los 2 temas, foco, texto mínimo y área táctil)
- [ ] Tokens nuevos o cambiados registrados en `docs/configuracion/VARIABLES.md` y con motivo en `HISTORIAL.md`
- [ ] Sin direcciones IP ni secretos; cumple `docs/estandarizacion/` y no duplica componentes existentes
- [ ] `impacto.py` ejecutado y su tabla en esta ficha

## Impacto cruzado
- Genera → —
- Origen ← PLAN-FASE-7 §4
- Depende de → DIS-054; insumos de referencia y paleta (o propuesta neutra aceptada); ADR-007

## Riesgos y reversión
Regresión de contraste al cambiar paleta: pares por semántico. Reversión: los alias permiten revertir solo la paleta.

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
