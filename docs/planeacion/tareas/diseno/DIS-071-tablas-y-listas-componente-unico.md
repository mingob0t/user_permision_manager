# DIS-071 — Tablas y listas: un solo componente de datos (absorbe `ResponsiveList`), `ListPager` y `DataLabel`

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 7 |
| **Módulo / Área** | componentes |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Responsable** | |
| **Creada** | 2026-10-27 |
| **Inicio** | |
| **Finalizada** | |
| **Estatus Git** | — |
| **Rama** | `dis/DIS-071-tablas-y-listas-componente-unico` |
| **Commits / PR** | |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- `DataTable` (1 uso) y `ResponsiveList` (9) resuelven el mismo patrón; 2 listas a mano en detalles; etiqueta de dato copiada 7 veces; 10 plantillas `grid-cols-[minmax…]`; sin hover ni seleccionado en filas (plan §2.4, §2.6, §2.7).
- Plan: [PLAN-FASE-7](../../PLAN-FASE-7-diseno-visual.md).

## Objetivo
Un componente de datos adaptable (tabla en escritorio, lista en móvil) con estados de fila y columnas por props con nombre.

## Alcance
- **Incluye:**
  - Unificar `DataTable` y `ResponsiveList` (vive en `components/data-table.tsx`; responsabilidad: mostrar filas de datos y sus estados)
  - Columnas por prop con nombre en un solo lugar (retira los `grid-cols-[…]`)
  - Fila: hover (si interactiva), foco, seleccionado, error
  - `DataLabel` para la etiqueta de dato; migrar las 7 copias
  - Migrar los 9 usos de `ResponsiveList` y las listas de `audit-detail-modal.tsx:61`, `job-detail-modal.tsx:67`
  - `ListPager` con `control-alto`
  - Retirar sus excepciones
- **No incluye:**
  - Esqueletos (DIS-073)
  - Filtros (DIS-069)
  - Columnas o datos nuevos

## Archivos previstos
- `frontend/src/components/data-table.tsx`
- `frontend/src/components/access/responsive-list.tsx` (se retira o queda como alias)
- `frontend/src/components/access/list-pager.tsx`
- Listas migradas (plan §2.6)

## Reutilización
`DataTable`, `ResponsiveList`, `ListPager`, `totalPaginas`.

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| Componente de datos | componente | Mis solicitudes, Mis accesos, Aprobaciones, Inventario, Ejecuciones, Conectores, Auditoría, Accesos de usuario, Administrar plataformas | No |

## Variables y configuración
Ninguna.

## Criterios de aceptación
- [ ] Mismas columnas, orden y semántica (`th scope`, `dl`) que hoy; pruebas de cada lista en verde
- [ ] Fila seleccionada distinguible sin color
- [ ] Desde `frontend/`: `npm run typecheck`, `npm run lint`, `npx vitest run` (incluye `tests/accesibilidad/`) y `npm run build` con código de salida 0
- [ ] Sin colores literales, sin estilos en línea, sin `dark:` ni clases de tema en TSX
- [ ] Verificada en navegador en tema claro y oscuro, a 360 px y 1280 px, y en los estados de carga, vacío y error que apliquen (nota o captura en la ficha)
- [ ] `auditor-accesibilidad` Aprobado (contraste medido en los 2 temas, foco, texto mínimo y área táctil)
- [ ] Tokens nuevos o cambiados registrados en `docs/configuracion/VARIABLES.md` y con motivo en `HISTORIAL.md`
- [ ] Sin direcciones IP ni secretos; cumple `docs/estandarizacion/` y no duplica componentes existentes
- [ ] `impacto.py` ejecutado y su tabla en esta ficha

## Impacto cruzado
- Genera → —
- Origen ← PLAN-FASE-7 §4.4
- Depende de → DIS-058, DIS-062

## Riesgos y reversión
9 pantallas cambian de componente: pruebas existentes por lista.

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
