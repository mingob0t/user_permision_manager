# DIS-056 — Tokens de interacción y estado: hover, presionado, seleccionado, foco, deshabilitado, inválido, solo lectura y movimiento

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
| **Rama** | `dis/DIS-056-tokens-de-interaccion-y-estado` |
| **Commits / PR** | |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- Estados sin token: foco copiado 38 veces, 4 opacidades de deshabilitado, `aria-invalid` sin estilo, solo lectura sin diseño, sin `prefers-reduced-motion` (plan §2.4).
- Plan: [PLAN-FASE-7](../../PLAN-FASE-7-diseno-visual.md).

## Objetivo
Definir los tokens de interacción y movimiento de la matriz (plan §4.2-4.3) en los 2 temas, con utilidades para usarlos.

## Alcance
- **Incluye:**
  - Tokens: `foco-anillo/-ancho/-separacion`, `hover-capa`, `presionado-capa`, `seleccionado-fondo/-borde`, `deshabilitado-fondo/-texto/-borde`, `invalido-borde`, `solo-lectura-fondo`, `duracion-*`, `curva`
  - Utilidades: `foco-visible` (anillo único), `estado-deshabilitado`, `estado-invalido` (sobre `aria-invalid`), `solo-lectura`; `prefers-reduced-motion` anula duraciones
  - Prueba nueva `estados-con-token.test.ts` (tokens en los 2 temas; sin `opacity-NN` ni `dark:` en TSX, con excepciones que solo bajan)
  - Pares: anillo de foco y borde inválido ≥ 3:1 sobre superficie y superficie hundida
  - `01-visual.md`: matriz de estados
- **No incluye:**
  - Aplicar los estados en cada componente (C1–C5)
  - Pantallas

## Archivos previstos
- `frontend/src/styles/tokens.css`
- `frontend/src/styles/components.css` (utilidades de estado)
- `frontend/tailwind.config.ts`
- `frontend/tests/accesibilidad/estados-con-token.test.ts` (nuevo), `pares-contraste.ts`
- `docs/estandarizacion/01-visual.md`

## Reutilización
Semánticos de DIS-055; `hover-botones.test.ts` como referencia de prueba de estados.

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| Utilidades de estado | CSS | todo componente interactivo (los adopta C1–C5) | No |

## Variables y configuración
Tokens de interacción nuevos: registro y historial.

## Criterios de aceptación
- [ ] Cada token de la matriz existe en los 2 temas y su par mide ≥ 3:1 (no texto) o ≥ 4.5:1 (texto)
- [ ] Con reducción de movimiento las duraciones son 0
- [ ] Desde `frontend/`: `npm run typecheck`, `npm run lint`, `npx vitest run` (incluye `tests/accesibilidad/`) y `npm run build` con código de salida 0
- [ ] Sin colores literales, sin estilos en línea, sin `dark:` ni clases de tema en TSX
- [ ] Verificada en navegador en tema claro y oscuro, a 360 px y 1280 px, y en los estados de carga, vacío y error que apliquen (nota o captura en la ficha)
- [ ] `auditor-accesibilidad` Aprobado (contraste medido en los 2 temas, foco, texto mínimo y área táctil)
- [ ] Tokens nuevos o cambiados registrados en `docs/configuracion/VARIABLES.md` y con motivo en `HISTORIAL.md`
- [ ] Sin direcciones IP ni secretos; cumple `docs/estandarizacion/` y no duplica componentes existentes
- [ ] `impacto.py` ejecutado y su tabla en esta ficha

## Impacto cruzado
- Genera → —
- Origen ← PLAN-FASE-7 §4.3
- Depende de → DIS-055

## Riesgos y reversión
Utilidades sin adoptar hasta C1–C5: la prueba las exige por excepciones con tarea.

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
