# DIS-052 — Dividir el monolito `RequestCatalog`

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | catalogo |
| **Prioridad** | Baja |
| **Estatus** | Hecha |
| **Creada** | 2026-10-27 |

## Contexto
- `access/request-catalog.tsx` pasó de unas 50 a unas 175 líneas en `RequestCatalog` (carga, cruce, filtro, aviso, modal y lista en una función)
- Observación del revisor de DIS-030; no se refactoriza de paso

## Objetivo
- Separar filtro, lista, aviso de solicitud y estado de carga en unidades con una responsabilidad, sin cambiar el comportamiento
- Las pruebas existentes deben pasar sin cambios

## Impacto cruzado
- Origen ← DIS-030

## Decisiones (decisión del orquestador, pendiente de validar en la prueba de concepto)
- Aprobada en modo autónomo; `RequestCatalog` (230 → 122 líneas) solo orquesta estado de modal y aviso
- Nuevos en `frontend/src/components/access/`: `use-catalogo-solicitable.ts` (carga, unión, solicitadas, áreas; exporta `MisPlataformas`, reexportado por `request-catalog.tsx`), `catalog-filters.tsx` (`CatalogFilters`, `filtrarCatalogo`, `BUSCADOR_ID`), `catalog-grid.tsx` (carga, errores, vacío, tarjetas), `catalog-notice.tsx` (región `status`)
- «Abrir» duplicado: usos en `request-catalog-card.tsx` (botón «Abrir») y `platform-card.tsx` (nombre como enlace, DIS-051); `favorites-list.tsx` solo usa `PlatformCard`. No se extrae: marcado, etiqueta y clases distintos; extraerlo cambiaría nombres accesibles o aspecto. Propuesta futura: helper común de `registerVisit` si se unifican

## Impacto en elementos compartidos
- Ninguno modificado: `PlatformCard`, `FavoriteButton`, `RequestCatalogCard`, `unirCatalogo` y `PlatformsView` sin cambios; `MisPlataformas` se sigue exportando desde `request-catalog.tsx`
- Único consumidor de `RequestCatalog`: `PlatformsView` (`/platforms`)

## Verificación
- `tsc --noEmit`: 0; `eslint .`: 0; `vitest run`: 0 (52 archivos, 1692 pruebas, incluidas las de accesibilidad, sin cambios); `npm run build`: 0
- No verificado: navegador, tema claro/oscuro y móvil (refactor sin cambios de clases ni tokens)
- Pendientes: `revisor` y `auditor-accesibilidad` (no lanzables desde el subagente)

## Bitácora
- 2026-10-27: división hecha; sin cambio de comportamiento
- `impacto.py` lista `RequestCatalog` y funciones locales (`coincide`, `motivo`, `creada`, `cerrarAviso`) por coincidencia de nombre; son internas, el único consumidor real es `PlatformsView`

- 2026-10-27: `auditor-accesibilidad` Aprobado (semántica, ids, estados, aviso y foco conservados). Menor: `EstadoCarga.data` es `unknown`. Hecha (decisión del orquestador, pendiente de validar en la prueba de concepto). Sin verificar en navegador.
