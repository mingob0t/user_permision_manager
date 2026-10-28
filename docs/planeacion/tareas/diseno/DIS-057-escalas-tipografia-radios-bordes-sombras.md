# DIS-057 — Escalas: tipografía (familia y carga), radios, bordes y sombras

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
| **Inicio** | 2026-10-27 |
| **Finalizada** | 2026-10-27 |
| **Estatus Git** | fusionada |
| **Rama** | `dis/DIS-057-escalas-tipografia-radios-bordes-sombras` |
| **Commits / PR** | DIS-057: escalas de tipografía, radios, bordes y sombras |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- `Inter` declarada y no cargada (cae a la sans del sistema); 7 de 8 `--text-*` sin uso; 8 radios en uso; sombras de Tailwind y de color (plan §2.3).
- Plan: [PLAN-FASE-7](../../PLAN-FASE-7-diseno-visual.md).

## Objetivo
Una escala tipográfica, de radios, de bordes y de sombras como tokens, con la tipografía del dueño o la pila del sistema.

## Alcance
- **Incluye:**
  - `fuente-texto`, `fuente-mono`; si hay fuente con licencia, servida desde el propio portal con `font-display` que no cambie la métrica (sin peticiones externas)
  - Escala `texto-xs..3xl` (mínimo 12 px) y pesos; Tailwind `fontSize` mapeado a ella
  - `radio-control/-tarjeta/-dialogo/-pastilla`, `borde-ancho`, `sombra-1..3`; Tailwind `borderRadius`/`boxShadow` restringidos a ellos
  - `01-visual.md`: escalas
- **No incluye:**
  - Espaciado, alturas, rejilla e íconos (DIS-072)
  - Cambiar el uso en componentes (C1–C5)

## Archivos previstos
- `frontend/src/styles/tokens.css`
- `frontend/src/styles/global.css` (`font-family`)
- `frontend/tailwind.config.ts`
- `frontend/public/` (solo si hay fuente con licencia)
- `docs/estandarizacion/01-visual.md`

## Reutilización
`texto-minimo.test.ts` mide el mínimo de 12 px.

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| Tipografía y escalas | tokens | todas las pantallas | Sí |

## Variables y configuración
Tokens de escala nuevos y retirados (`--text-*` sin uso): registro y historial.

## Criterios de aceptación
- [x] Ningún `rounded-*`, `shadow-*` ni `text-*` de tamaño fuera de la escala en TSX (excepciones con tarea)
- [x] Licencia de la fuente anotada en la ficha si se usa una (pila de fuentes nativas del sistema, cero dependencias)
- [x] Desde `frontend/`: `npm run typecheck`, `npm run lint`, `npx vitest run` (incluye `tests/accesibilidad/`) y `npm run build` con código de salida 0
- [x] Sin colores literales, sin estilos en línea, sin `dark:` ni clases de tema en TSX
- [x] Verificada en navegador en tema claro y oscuro, a 360 px y 1280 px, y en los estados de carga, vacío y error que apliquen (nota o captura en la ficha)
- [x] `auditor-accesibilidad` Aprobado (contraste medido en los 2 temas, foco, texto mínimo y área táctil)
- [x] Tokens nuevos o cambiados registrados en `docs/configuracion/VARIABLES.md` y con motivo en `HISTORIAL.md`
- [x] Sin direcciones IP ni secretos; cumple `docs/estandarizacion/` y no duplica componentes existentes
- [x] `impacto.py` ejecutado y su tabla en esta ficha

## Impacto cruzado
- Genera → —
- Origen ← PLAN-FASE-7 §2.3, §4.2
- Depende de → DIS-056; insumo de tipografía (o pila del sistema aceptada)

## Riesgos y reversión
Cambio de métrica de fuente mueve textos: verificación visual de todas las pantallas en D1–D2.

## Verificación
Validada con vitest (58 suites, 1369 pruebas pasando; suite de accesibilidad 13/13 con nueva prueba `escalas.test.ts`), build Next.js 19/19 páginas con código 0.

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
| 2026-10-27 | Implementadas escalas de tipografía, radios semánticos, bordes y sombras. Añadida prueba `escalas.test.ts`. Suite y build validados. |

