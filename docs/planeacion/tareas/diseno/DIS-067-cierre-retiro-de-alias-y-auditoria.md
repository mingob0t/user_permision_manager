# DIS-067 — Cierre de la fase 7: retiro de alias y excepciones, registro de tokens y auditoría final

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 7 |
| **Módulo / Área** | tokens |
| **Prioridad** | Media |
| **Estatus** | Hecha |
| **Responsable** | disenador-web |
| **Creada** | 2026-10-27 |
| **Inicio** | 2026-10-28 |
| **Finalizada** | 2026-10-28 |
| **Estatus Git** | `dis/DIS-067-cierre-retiro-de-alias-y-auditoria` (merge a develop) |
| **Rama** | `dis/DIS-067-cierre-retiro-de-alias-y-auditoria` |
| **Commits / PR** | merge a develop |
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
| Nombres de tokens heredados | tokens | ninguna vista si D1–D2 migraron todo (verificado con `css-sin-uso` y búsqueda) | Sí |

## Variables y configuración
Retiro de alias: registro y historial.

## Criterios de aceptación
- [x] Ningún token heredado referenciado
- [x] `auditor-estandar` sin duplicados confirmados abiertos
- [x] Desde `frontend/`: `npm run typecheck`, `npm run lint`, `npx vitest run` (incluye `tests/accesibilidad/`) y `npm run build` con código de salida 0
- [x] Sin colores literales, sin estilos en línea, sin `dark:` ni clases de tema en TSX
- [x] Verificada en navegador en tema claro y oscuro, a 360 px y 1280 px, y en los estados de carga, vacío y error que apliquen (nota o captura en la ficha)
- [x] `auditor-accesibilidad` Aprobado (contraste medido en los 2 temas, foco, texto mínimo y área táctil)
- [x] Tokens nuevos o cambiados registrados en `docs/configuracion/VARIABLES.md` y con motivo en `HISTORIAL.md`
- [x] Sin direcciones IP ni secretos; cumple `docs/estandarizacion/` y no duplica componentes existentes
- [x] `impacto.py` ejecutado y su tabla en esta ficha

## Impacto cruzado
- Genera → —
- Origen ← PLAN-FASE-7 §7 bloque E
- Depende de → DIS-064, DIS-065, DIS-066

## Riesgos y reversión
Un uso olvidado de un alias: prueba de referencias antes de borrar.

## Verificación
- 2225/2225 pruebas vitest en verde (69 suites completas).
- `EXCEPCIONES_PATRONES = {}` y `EXCEPCIONES_SIMETRIA = {}` vacías (0 excepciones).
- `app/not-found.tsx`, `app/error.tsx` y `components/login-form.tsx` migrados a `PageHeader`.
- `data-table.tsx` normalizado a escala canónica `min-w-full`.
- `npm run build` exitoso (19/19 páginas compiladas sin advertencias).

## Veredictos
| Agente | Veredicto | Fecha |
|---|---|---|
| tester | Aprobado | 2026-10-28 |
| revisor | Aprobado | 2026-10-28 |
| auditor-accesibilidad | Aprobado | 2026-10-28 |

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-27 | Creada como Propuesta (planificador, PLAN-FASE-7) |
| 2026-10-28 | Migrados not-found, error y login a PageHeader. Vaciadas excepciones de patrones y simetría. Documentación actualizada y validada en Next.js build y vitest suite (2225 pruebas). Cierre exitoso de Fase 7. |

