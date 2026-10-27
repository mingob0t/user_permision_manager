# DIS-073 — Sin saltos de diseño (CLS): esqueletos, zonas reservadas y diálogos que no mueven el fondo

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
| **Rama** | `dis/DIS-073-sin-saltos-de-diseno-cls` |
| **Commits / PR** | |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- `useScrollLock` oculta la barra de desplazamiento y el contenido se corre; `scrollbar-gutter` 0 usos; `Spinner` reemplaza contenido con otra altura; avisos sin zona reservada; sin `prefers-reduced-motion` (plan §2.8).
- Plan: [PLAN-FASE-7](../../PLAN-FASE-7-diseno-visual.md).

## Objetivo
CLS < 0,01 al cargar y al abrir/cerrar diálogos (plan §4.3.2).

## Alcance
- **Incluye:**
  - `scrollbar-gutter: stable` en la raíz y en `main` (`global.css`); `useScrollLock` sin cambiar ancho ni posición
  - `Modal` y `Drawer`: entrada/salida solo con opacidad y `transform`, duraciones de token, nada con reducción de movimiento
  - `Skeleton` (fila, tarjeta, contador) en `ui.tsx`; integrado en el componente de datos, `Card` y `StatTile`
  - `RegionDeAviso`: alto mínimo reservado para avisos y errores en formularios y cabeceras de lista
  - Imágenes y logos con medidas fijas
  - Medición de línea base y resultado (Lighthouse o panel de rendimiento) en las 7 pantallas principales
  - `02-comportamiento.md`: reglas de estabilidad
- **No incluye:**
  - Migrar cada pantalla a esqueletos (D1–D2 lo aplican con las plantillas)
  - Diálogo de alerta (DIS-074)

## Archivos previstos
- `frontend/src/styles/global.css`
- `frontend/src/lib/use-scroll-lock.ts`
- `frontend/src/components/form.tsx` (`Modal`), `drawer.tsx`
- `frontend/src/components/ui.tsx` (`Skeleton`, `RegionDeAviso`)
- `frontend/src/components/data-table.tsx`
- `docs/estandarizacion/02-comportamiento.md`

## Reutilización
`useScrollLock`, `Modal`, `Card`, `StatTile`, componente de datos (DIS-071).

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `useScrollLock` / `global.css` | hook/CSS | todos los diálogos y el menú móvil | No |
| `Skeleton`, `RegionDeAviso` (nuevos) | componentes | los adoptan las plantillas (DIS-070) y pantallas (D1–D2) | No |

## Variables y configuración
Tokens de movimiento (de DIS-056) usados; ninguno nuevo salvo los de componente.

## Criterios de aceptación
- [ ] Abrir y cerrar un diálogo no cambia la posición del contenido de fondo (medido: 0 px)
- [ ] `Skeleton` con el alto final (prueba de componente)
- [ ] Pruebas de bloqueo de desplazamiento (DIS-038/DIS-044) en verde
- [ ] CLS de línea base y final anotados por pantalla
- [ ] Desde `frontend/`: `npm run typecheck`, `npm run lint`, `npx vitest run` (incluye `tests/accesibilidad/`) y `npm run build` con código de salida 0
- [ ] Sin colores literales, sin estilos en línea, sin `dark:` ni clases de tema en TSX
- [ ] Verificada en navegador en tema claro y oscuro, a 360 px y 1280 px, y en los estados de carga, vacío y error que apliquen (nota o captura en la ficha)
- [ ] `auditor-accesibilidad` Aprobado (contraste medido en los 2 temas, foco, texto mínimo y área táctil)
- [ ] Tokens nuevos o cambiados registrados en `docs/configuracion/VARIABLES.md` y con motivo en `HISTORIAL.md`
- [ ] Sin direcciones IP ni secretos; cumple `docs/estandarizacion/` y no duplica componentes existentes
- [ ] `impacto.py` ejecutado y su tabla en esta ficha

## Impacto cruzado
- Genera → —
- Origen ← Pedido del dueño 2026-10-27 (sin saltos); PLAN-FASE-7 §2.8, §4.3.2
- Depende de → DIS-061, DIS-071, DIS-062

## Riesgos y reversión
`scrollbar-gutter` deja un canal vacío en páginas cortas (aceptado).

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
