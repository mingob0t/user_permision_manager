# DIS-070 — `PageHeader` y plantillas de pantalla (listado, detalle, formulario y panel)

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 7 |
| **Módulo / Área** | plantillas |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Responsable** | |
| **Creada** | 2026-10-27 |
| **Inicio** | |
| **Finalizada** | |
| **Estatus Git** | — |
| **Rama** | `dis/DIS-070-pageheader-y-plantillas-de-pantalla` |
| **Commits / PR** | |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- 17 `<h1>` a mano con 3 envoltorios y 3 márgenes de subtítulo; cada pantalla compone a su manera encabezado, filtros, contenido y estados (plan §2.6).
- Plan: [PLAN-FASE-7](../../PLAN-FASE-7-diseno-visual.md).

## Objetivo
Componentes de composición con la misma estructura en todas las pantallas (plan §4.5).

## Alcance
- **Incluye:**
  - `PageHeader` (título, descripción, acciones, volver, foco del `h1` como hoy en `favorites-list` y `platform-admin`)
  - `components/plantillas/`: `PantallaListado`, `PantallaDetalle`, `PantallaFormulario`, `PantallaPanel`, con ranuras y estados (carga con `Skeleton`, vacío, error, sin permiso)
  - Ancho `contenido-max`, rejilla y alineación de la regla de simetría
  - `02-comportamiento.md`: plantillas y cuándo usar cada una
- **No incluye:**
  - Migrar pantallas (D1–D2)

## Archivos previstos
- `frontend/src/components/page-header.tsx` (nuevo)
- `frontend/src/components/plantillas/` (nuevo)
- `frontend/tests/components/plantillas.test.tsx` (nuevo)
- `docs/estandarizacion/02-comportamiento.md`, `03-reutilizacion.md`

## Reutilización
`FilterBar`, componente de datos, `ListPager`, `Card`, `StatTile`, `Skeleton`, `RegionDeAviso`, `ErrorNote`, `EmptyNote`, `RequireRole`.

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| Plantillas (nuevas) | componentes | las adoptan DIS-064, DIS-065, DIS-066 | No |

## Variables y configuración
Ninguna.

## Criterios de aceptación
- [ ] Prueba de cada plantilla con sus 4 estados
- [ ] Un solo `h1` por pantalla y foco igual al actual
- [ ] Desde `frontend/`: `npm run typecheck`, `npm run lint`, `npx vitest run` (incluye `tests/accesibilidad/`) y `npm run build` con código de salida 0
- [ ] Sin colores literales, sin estilos en línea, sin `dark:` ni clases de tema en TSX
- [ ] Verificada en navegador en tema claro y oscuro, a 360 px y 1280 px, y en los estados de carga, vacío y error que apliquen (nota o captura en la ficha)
- [ ] `auditor-accesibilidad` Aprobado (contraste medido en los 2 temas, foco, texto mínimo y área táctil)
- [ ] Tokens nuevos o cambiados registrados en `docs/configuracion/VARIABLES.md` y con motivo en `HISTORIAL.md`
- [ ] Sin direcciones IP ni secretos; cumple `docs/estandarizacion/` y no duplica componentes existentes
- [ ] `impacto.py` ejecutado y su tabla en esta ficha

## Impacto cruzado
- Genera → DIS-064, DIS-065, DIS-066
- Origen ← Pedido del dueño 2026-10-27; PLAN-FASE-7 §4.5
- Depende de → C1–C5 cerradas y `auditor-estandar` ejecutado

## Riesgos y reversión
Plantillas demasiado rígidas: ranuras opcionales.

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
