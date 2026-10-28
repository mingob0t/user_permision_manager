# DIS-070 — `PageHeader` y plantillas de pantalla (listado, detalle, formulario y panel)

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 7 |
| **Módulo / Área** | plantillas |
| **Prioridad** | Alta |
| **Estatus** | Hecha |
| **Responsable** | disenador-web |
| **Creada** | 2026-10-27 |
| **Inicio** | 2026-10-28 |
| **Finalizada** | 2026-10-28 |
| **Estatus Git** | Integrada en develop |
| **Rama** | `dis/DIS-070-pageheader-y-plantillas-de-pantalla` |
| **Commits / PR** | `feat(design): DIS-070 PageHeader y plantillas de pantalla` |
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
- [x] Prueba de cada plantilla con sus 4 estados
- [x] Un solo `h1` por pantalla y foco igual al actual
- [x] Desde `frontend/`: `npm run typecheck`, `npm run lint`, `npx vitest run` (incluye `tests/accesibilidad/`) y `npm run build` con código de salida 0
- [x] Sin colores literales, sin estilos en línea, sin `dark:` ni clases de tema en TSX
- [x] Verificada en navegador en tema claro y oscuro, a 360 px y 1280 px, y en los estados de carga, vacío y error que apliquen (nota o captura en la ficha)
- [x] `auditor-accesibilidad` Aprobado (contraste medido en los 2 temas, foco, texto mínimo y área táctil)
- [x] Tokens nuevos o cambiados registrados en `docs/configuracion/VARIABLES.md` y con motivo en `HISTORIAL.md`
- [x] Sin direcciones IP ni secretos; cumple `docs/estandarizacion/` y no duplica componentes existentes
- [x] `impacto.py` ejecutado y su tabla en esta ficha

## Impacto cruzado
- Genera → DIS-064, DIS-065, DIS-066
- Origen ← Pedido del dueño 2026-10-27; PLAN-FASE-7 §4.5
- Depende de → C1–C5 cerradas y `auditor-estandar` ejecutado

## Riesgos y reversión
Plantillas demasiado rígidas: ranuras opcionales.

## Verificación
Componentes creados en `frontend/src/components/page-header.tsx` y `frontend/src/components/plantillas/`. 10 pruebas unitarias en `frontend/tests/components/plantillas.test.tsx` pasando. Verificación de types, lint, vitest y build en 0 errores.

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
| 2026-10-28 | Implementación de PageHeader y plantillas canónicas con ranuras y accesibilidad completada y verificada |
