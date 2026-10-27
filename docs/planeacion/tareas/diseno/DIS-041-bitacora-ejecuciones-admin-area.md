# DIS-041 — Bitácora de ejecuciones para el admin de área

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | configuracion-conectores |
| **Prioridad** | Media |
| **Estatus** | Hecha |
| **Creada** | 2026-10-21 |

## Contexto
- El contrato `conectores-y-ejecuciones.md` 1.1 da `GET /provisioning/jobs` al admin de área (sus áreas, lectura)
- DIS-022 dejó la bitácora en `/admin/connectors`, con guarda `admin` (solo superadmin, FNC-070): el admin de área no la ve

## Objetivo
- Mostrar `JobsLog` (ya reutilizable; oculta "Reintentar" sin superadmin) al admin de área en una ruta o entrada propia, sin la configuración de conectores

## Impacto cruzado
- Origen ← DIS-022
- Menú `NAV` de `app-shell.tsx` (compartido) si se agrega una entrada

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-21 | Creada como Propuesta desde DIS-022 |
| 2026-10-27 | En curso por aprobación en modo autónomo. Decisión del orquestador (pendiente de validar en la prueba de concepto): ruta nueva `/admin/jobs` con guarda `any_admin` y entrada «Ejecuciones» en el menú para admin de área y superadmin (el superadmin conserva la bitácora en Conectores); título «Ejecuciones» |
| 2026-10-27 | Hecha: página `app/admin/jobs/page.tsx` reutilizando `JobsLog` sin cambios (DataTable/filtros/`usePolling`/`SuccessNote` ya dentro). El backend ya filtra por áreas (`any_admin_required`, prueba `test_admin_solo_ve_las_de_sus_areas`): no se crea FNC |

## Impacto en elementos compartidos
- `NAV` de `components/app-shell.tsx`: entrada nueva «Ejecuciones» (`any_admin`); la ven admin de área y superadmin en barra lateral y menú móvil
- `JobsLog` y `RequireRole`: reutilizados sin modificar
- Pruebas actualizadas por la entrada nueva: `navegacion-por-rol.test.tsx` y `menu-movil.test.tsx` (12 a 13 entradas)

## Verificación
- En `frontend/`: typecheck 0, lint 0, vitest 0 (1568 pruebas, accesibilidad incluida 0 fallas), build 0
- Prueba nueva `tests/components/connectors/jobs-page.test.tsx`: por rol y estados carga, vacío y error
- No verificado en navegador (temas y móvil); revisor y auditor-accesibilidad pendientes

- 2026-10-27: `auditor-accesibilidad` Aprobado. Observación aplicada por el orquestador: la descripción de `/admin/jobs` dice «en tu alcance» (el superadmin ve todas). Hecha (decisión del orquestador, pendiente de validar en la prueba de concepto). Sin verificar en navegador.
