# DIS-067 — Cierre de la fase 7: retiro de alias y excepciones, registro de tokens y auditoría final

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 7 |
| **Módulo / Área** | tokens |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Responsable** | |
| **Creada** | 2026-10-27 |
| **Inicio** | |
| **Finalizada** | |
| **Estatus Git** | — |
| **Rama** | `dis/DIS-067-cierre-retiro-de-alias-y-auditoria` |
| **Commits / PR** | |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- DIS-055 deja alias de los nombres heredados; las pruebas de DIS-056, DIS-068 y DIS-072 tienen excepciones temporales.
- Plan: [PLAN-FASE-7](../../PLAN-FASE-7-diseno-visual.md).

## Objetivo
Dejar un solo juego de nombres, sin excepciones injustificadas, documentado y auditado.

## Alcance
- **Incluye:**
  - Retirar alias de tokens y claves de Tailwind sin uso
  - Vaciar (o justificar) las excepciones de `patrones-unicos`, `escala-simetria`, `estados-con-token`
  - `VARIABLES.md`/`HISTORIAL.md`, `01-visual.md`, `02-comportamiento.md`, `03-reutilizacion.md`, `docs/frontend/README.md` al día
  - `auditor-estandar` (duplicados y CSS repetido) y `auditor-accesibilidad` sobre todas las pantallas; CLS final de las 7 pantallas principales
- **No incluye:**
  - Cambios de diseño nuevos (lo que salga de las auditorías entra como tarea Propuesta)

## Archivos previstos
- `frontend/src/styles/tokens.css`
- `frontend/tailwind.config.ts`
- Archivos de excepciones de pruebas
- Docs listadas

## Reutilización
—

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| Nombres de tokens heredados | tokens | ninguna vista si D1–D2 migraron todo (verificado con `css-sin-uso` y búsqueda) | No |

## Variables y configuración
Retiro de alias: registro y historial.

## Criterios de aceptación
- [ ] Ningún token heredado referenciado
- [ ] `auditor-estandar` sin duplicados confirmados abiertos
- [ ] Desde `frontend/`: `npm run typecheck`, `npm run lint`, `npx vitest run` (incluye `tests/accesibilidad/`) y `npm run build` con código de salida 0
- [ ] Sin colores literales, sin estilos en línea, sin `dark:` ni clases de tema en TSX
- [ ] Verificada en navegador en tema claro y oscuro, a 360 px y 1280 px, y en los estados de carga, vacío y error que apliquen (nota o captura en la ficha)
- [ ] `auditor-accesibilidad` Aprobado (contraste medido en los 2 temas, foco, texto mínimo y área táctil)
- [ ] Tokens nuevos o cambiados registrados en `docs/configuracion/VARIABLES.md` y con motivo en `HISTORIAL.md`
- [ ] Sin direcciones IP ni secretos; cumple `docs/estandarizacion/` y no duplica componentes existentes
- [ ] `impacto.py` ejecutado y su tabla en esta ficha

## Impacto cruzado
- Genera → —
- Origen ← PLAN-FASE-7 §7 bloque E
- Depende de → DIS-064, DIS-065, DIS-066

## Riesgos y reversión
Un uso olvidado de un alias: prueba de referencias antes de borrar.

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
