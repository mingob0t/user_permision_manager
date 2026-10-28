# DIS-054 — Tema: retirar los 5 temas extra y unificar el oscuro (claro, oscuro y «Según el sistema»)

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 7 |
| **Módulo / Área** | tema |
| **Prioridad** | Alta |
| **Estatus** | Hecha |
| **Responsable** | disenador-web |
| **Creada** | 2026-10-27 |
| **Inicio** | 2026-10-27 |
| **Finalizada** | 2026-10-27 |
| **Estatus Git** | Merge a develop |
| **Rama** | `dis/DIS-054-dos-temas` |
| **Commits / PR** | `6f2b10d` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- `tokens.css` tiene 7 contextos; 4 temas `theme-*` (líneas 364-731) y dos oscuros distintos (`@media` y `html.dark` difieren en 7 tokens).
- `lib/tema.ts` lista 7 opciones; `global.css:69-70` declara `color-scheme` para los 4 `theme-*`.
- 10 archivos de prueba y la documentación hablan de «7 temas».
- Plan: [PLAN-FASE-7](../../PLAN-FASE-7-diseno-visual.md).

## Objetivo
Dejar 2 temas (claro y oscuro) y «Según el sistema» como opción por defecto que elige entre ellos (ADR-007).

## Alcance
- **Incluye:**
  - Borrar los 4 bloques `html.theme-*` de `tokens.css`; igualar el bloque `@media (prefers-color-scheme: dark)` a `html.dark` (los 7 tokens que difieren toman el valor de `html.dark`, medido)
  - `lib/tema.ts`: `TEMAS` = sistema, claro, oscuro; mapa `TEMAS_RETIRADOS` (esmeralda/rosa → claro, obsidiana/violeta → oscuro) aplicado en `leerTema`, `aplicarTemaDeCuenta` y en `SCRIPT_RESTAURAR_TEMA`
  - `global.css`: `color-scheme` solo para `:root`, `html.light`, `html.dark`
  - Pruebas: `tests/utils/tokens-css.ts` (`CONTEXTOS` a 3), `contraste`, `velo`, `fallas-contraste-conocidas`, `chips-contraste`, `tema.test.tsx`, `tema-diseno.test.ts`, `theme-selector-cuenta.test.tsx`; nueva prueba de igualdad SO oscuro = `html.dark`
  - Docs: `estandarizacion/README.md`, `03-reutilizacion.md`, `docs/frontend/README.md` §6, `VARIABLES.md`/`HISTORIAL.md` (tokens retirados)
- **No incluye:**
  - Cambiar valores del claro o del oscuro más allá de unificar los 7 tokens
  - Renombrar tokens (DIS-055)
  - Backend (FNC-132)
  - El archivo sin versionar `tests/lib/color-legible-hex.PENDIENTE.test.tsx`

## Archivos previstos
- `frontend/src/styles/tokens.css`
- `frontend/src/styles/global.css`
- `frontend/src/lib/tema.ts`
- `frontend/tests/utils/tokens-css.ts` y las pruebas listadas
- Docs listadas

## Reutilización
`TEMAS`, `esTemaValido`, `aplicarTemaDeCuenta` y el selector de FNC-032/FNC-123 se conservan; `ThemeSelector` no cambia de código.

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `tokens.css` (bloques de tema) | tokens | todas las pantallas | No |
| `lib/tema.ts` (`TEMAS`, script de `<head>`) | módulo | `ThemeSelector` (cabecera de `AppShell`), `app/layout.tsx` | No |
| `global.css` (`color-scheme`) | CSS | controles nativos de todas las pantallas | No |
| `tests/utils/tokens-css.ts` (`CONTEXTOS`) | utilidad de pruebas | todas las pruebas de contraste | No |

## Variables y configuración
Tokens retirados de los 4 temas: registro y historial (motivo: decisión del dueño 2026-10-27, solo 2 temas).

## Criterios de aceptación
- [ ] El selector muestra 3 opciones; elegir cada una aplica la clase correcta y se guarda
- [ ] Un `localStorage` o `preferences.theme` con un tema retirado aplica su equivalente, sin destello
- [ ] Prueba de igualdad SO oscuro = `html.dark` en verde; contraste en verde en los 3 contextos
- [ ] Desde `frontend/`: `npm run typecheck`, `npm run lint`, `npx vitest run` (incluye `tests/accesibilidad/`) y `npm run build` con código de salida 0
- [ ] Sin colores literales, sin estilos en línea, sin `dark:` ni clases de tema en TSX
- [ ] Verificada en navegador en tema claro y oscuro, a 360 px y 1280 px, y en los estados de carga, vacío y error que apliquen (nota o captura en la ficha)
- [ ] `auditor-accesibilidad` Aprobado (contraste medido en los 2 temas, foco, texto mínimo y área táctil)
- [ ] Tokens nuevos o cambiados registrados en `docs/configuracion/VARIABLES.md` y con motivo en `HISTORIAL.md`
- [ ] Sin direcciones IP ni secretos; cumple `docs/estandarizacion/` y no duplica componentes existentes
- [ ] `impacto.py` ejecutado y su tabla en esta ficha

## Impacto cruzado
- Genera → —
- Origen ← PLAN-FASE-7 §5, FNC-032, FNC-123
- Depende de → Contrato `preferencias.md` y ADR-007 aprobados; vinculada a FNC-132 (integrar juntas)

## Riesgos y reversión
Cambio de 7 valores del oscuro del SO (fondo `#030712` → `#0f172a`): visible para quien usa el SO oscuro; medir contraste. Reversión: revertir el commit.

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
