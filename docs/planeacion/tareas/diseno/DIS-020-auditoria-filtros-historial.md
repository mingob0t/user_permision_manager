# DIS-020 — Auditoría: filtros e historial por usuario y por plataforma

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | auditoria |
| **Prioridad** | Alta |
| **Estatus** | Hecha |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Rama local, sin push |
| **Rama** | `dis/DIS-020-auditoria-filtros-historial` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- `audit-log.tsx` lista los últimos registros sin filtros, sin detalle de antes y después ni historial (F-AUD-03)
- Requerimientos: F-AUD-01, F-AUD-03, F-AUD-04

## Objetivo
- Filtros (fechas, evento, usuario, plataforma, área), paginación, detalle de cada registro con antes y después legible, y vistas de historial por usuario y por plataforma enlazadas desde Usuarios y Plataformas

## Alcance
- **Incluye:**
  - Filtros con `Select`/`TextInput` existentes (resuelve D-09 en esta pantalla)
  - Detalle en modal con la diferencia antes/después
  - Rutas `/audit/users/[id]` y `/audit/platforms/[id]`
- **No incluye:**
  - Exportar
  - Componente `DataTable` común (DIS-010)

## Archivos previstos
- `frontend/src/components/audit/audit-filters.tsx`
- `frontend/src/components/audit/audit-detail-modal.tsx`
- `frontend/src/components/audit/audit-history.tsx`
- `frontend/src/components/audit-log.tsx`
- `frontend/src/app/audit/users/[id]/page.tsx`
- `frontend/src/app/audit/platforms/[id]/page.tsx`

## Archivos reales
| Archivo | Cambio |
|---|---|
| `components/audit/audit-history.tsx` | Nuevo: contenedor (filtros a la página 1, recarga, carga/vacío/error, paginación, detalle con foco de vuelta) |
| `components/audit/audit-filters.tsx` | Nuevo: búsqueda, Desde/Hasta (validación ≤ 366 días y `from ≤ to`), evento, resultado, área y plataforma |
| `components/audit/audit-table.tsx` | Nuevo: filas en `ResponsiveList`, "Ver detalle" 48 px |
| `components/audit/audit-detail-modal.tsx`, `audit-diff.ts` | Nuevos: detalle en `Modal`; antes/después como lista de campos, texto plano |
| `components/audit/audit-actions.ts`, `audit-routes.ts` | Nuevos: catálogo de eventos/resultados en español; rutas e id de ruta |
| `components/audit/user-audit-history.tsx`, `platform-audit-history.tsx` | Nuevos: historiales por usuario y por plataforma |
| `app/audit/users/[id]/page.tsx`, `app/audit/platforms/[id]/page.tsx` | Nuevas rutas (plataforma con `RequireRole any_admin`) |
| `components/audit-log.tsx` | Evoluciona: cabecera + `AuditHistory` con `auditApi.list` (antes `api.audit(200)` y filtro local) |
| `components/access/scope-filters.tsx` | Nuevo: `useOpcionesAlcance` y `ScopeSelects`, extraídos del inventario para reutilizarlos |
| `components/access/inventory.tsx`, `inventory-filters.tsx` | Usan `scope-filters`; enlace "Historial" con plataforma elegida; `limpiarBusqueda` quita también C1 |
| `components/users/user-access-panel.tsx` | Enlace "Historial" al historial del usuario |

## Reutilización
- `TextInput`, `Select`, `Field`, `Modal`, `Badge`, `Button`, `ErrorNote`, `EmptyNote`, `Spinner`
- `ResponsiveList`/`ResponsiveRow`/`ETIQUETA_CELDA`, `ListPager`, `formatearFecha`, `listLoadError`, `limpiarBusqueda`/`BUSQUEDA_MAX`
- Patrones de DIS-021: "Recargar" con `aria-disabled`, vacío en `role="status"`, filtros con etiqueta visible
- Enlaces con `.nexus-btn .nexus-btn-secondary` (como `platform-integration-fields.tsx`)

## Decisiones del orquestador (pendientes de validar en la prueba de concepto)
| # | Decisión |
|---|---|
| 1 | Sin filtro "usuario" (`user_id`) en `/audit`: no hay selector de usuarios reutilizable; se cubre con la búsqueda `q` y con el historial `/audit/users/[id]` |
| 2 | Usuario (rol `usuario`): sin filtros de área ni plataforma ni peticiones a `/areas` y `/platforms`; el backend ya limita a lo suyo |
| 3 | Historial de plataforma: sin filtros de área ni plataforma (ya está fijada) |
| 4 | `/audit/users/[id]`: el usuario solo ve el suyo ("Mi historial"); otro id muestra "sin permiso" sin pedir nada (el backend respondería 404) |
| 5 | Rango de fechas inválido: se explica junto a los campos (`role="alert"`, `aria-invalid`) y no se envía (evita el 400) |
| 6 | `404` del historial → "No existe o está fuera de tu alcance." (el backend responde 404 también para área ajena) |
| 7 | Nombre del usuario o plataforma del historial: se toma de los registros recibidos (no hay endpoint de detalle para el admin de área); sin registros, texto genérico |
| 8 | Detalle: con `before` "Antes y después" + insignia "Cambió"; solo `after` "Valores registrados"; ambos null (usuario) no se muestra la sección; IP solo si viene |
| 9 | Valores de antes/después como texto plano (`Sí`/`No`, objetos como JSON, null "—"); claves tal cual (sin traducir) |
| 10 | Enlaces: desde Usuarios (panel de accesos) y desde Inventario (solo con una plataforma elegida). Desde Administrar plataformas no: sus acciones de fila no cumplen 48 px; se propone DIS-035 |
| 11 | `scope-filters.tsx` extraído del inventario (en vez de duplicar áreas/plataformas); `limpiarBusqueda` quita también C1 (el servidor rechaza la categoría Cc completa) |
| 12 | Modal de detalle sin botón "Cerrar" en el pie: el `Modal` ya trae "Cerrar" (✕) y Escape; dos controles con el mismo nombre confundían |

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `audit-log.tsx` (`AuditLog`) | Pantalla | `/audit` | Pendiente |
| `inventory.tsx`, `inventory-filters.tsx` (`InventoryFilters` cambia de props: `opciones`) | Pantalla | `/inventory` | Pendiente |
| `limpiarBusqueda` (también C1) | Función | `/inventory`, `/audit` | Pendiente |
| `user-access-panel.tsx` (enlace "Historial") | Componente | `/users` | Pendiente |
| `pares-contraste.ts` (`error-text/body-bg`) | Prueba | accesibilidad | Pendiente |

Salida de `impacto.py` (la mayoría son coincidencias de nombre con el backend o con funciones locales homónimas, sin relación real):

**⚠ Impacto en elementos compartidos** (comparado contra `develop`): este cambio toca 10 elemento(s) usados en otras secciones: app, app/modules, frontend/src, frontend/tests, migrations, migrations/versions, scratch, tests, tests/access, tests/access_requests, tests/areas, tests/audit, tests/directory, tests/notifications, tests/platforms, tests/provisioning, tests/users. Valida cada una antes de integrar.

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `AuditLog` | función | `frontend/src/components/audit-log.tsx` | `app/__init__.py`, `app/modules/areas/baja.py`, `app/modules/audit/events.py`, `app/modules/audit/models.py`, `app/modules/audit/queries.py`, `app/modules/audit/services.py`, `frontend/src/app/audit/page.tsx`, `scratch/check_db_states.py` (+26) | app, app/modules, frontend/src, scratch, tests, tests/access, tests/access_requests, tests/areas, tests/audit, tests/directory, tests/notifications, tests/platforms, tests/provisioning, tests/users | ☐ |
| `FiltrosInventario` | tipo | `frontend/src/components/access/inventory-filters.tsx`, `frontend/src/components/access/inventory.tsx` | `app/modules/access/inventario.py`, `app/modules/access/inventario_api.py` | app/modules | ☐ |
| `Inventory` | función | `frontend/src/components/access/inventory.tsx` | `frontend/src/app/inventory/page.tsx` | frontend/src | ☐ |
| `UserAccessPanel` | función | `frontend/src/components/users/user-access-panel.tsx` | `frontend/src/components/users-list.tsx` | frontend/src | ☐ |
| `buscar` | función | `frontend/src/components/access/inventory-filters.tsx` | `app/modules/platforms/grupos.py`, `frontend/src/components/access/request-catalog.tsx`, `frontend/src/components/users-list.tsx`, `tests/conftest.py`, `tests/provisioning/test_ldap_provider.py` | app/modules, frontend/src, tests, tests/provisioning | ☐ |
| `filas` | función | `frontend/tests/components/audit-log.test.tsx` | `app/modules/home/services.py`, `frontend/src/components/access/responsive-list.tsx`, `migrations/versions/0003_plantillas_gestor_accesos.py`, `tests/audit/test_registro_ampliado.py` | app/modules, frontend/src, migrations/versions, tests/audit | ☐ |
| `opciones` | función | `frontend/tests/components/access/inventory.test.tsx` | `app/modules/provisioning/ejecucion.py`, `migrations/env.py`, `tests/provisioning/test_encolado.py`, `tests/provisioning/test_worker.py` | app/modules, migrations, tests/provisioning | ☐ |
| `pagina` | función | `frontend/tests/components/audit-log.test.tsx`, `frontend/tests/components/users/user-access-panel.test.tsx` | `frontend/src/components/access/request-catalog.tsx`, `frontend/tests/components/access/approvals-inbox.test.tsx`, `frontend/tests/components/access/my-requests-view.test.tsx`, `tests/provisioning/test_api.py` | frontend/src, frontend/tests, tests/provisioning | ☐ |
| `recargar` | función | `frontend/src/components/access/inventory.tsx` | `frontend/src/components/access/approvals-inbox.tsx`, `frontend/src/components/access/approve-dialog.tsx`, `frontend/src/components/access/reject-dialog.tsx`, `frontend/src/components/access/request-catalog.tsx`, `frontend/src/components/access/request-errors.ts`, `frontend/src/components/favorites-list.tsx`, `frontend/src/components/users/revoke-access-dialog.tsx`, `frontend/src/components/users/revoke-errors.ts` (+10) | frontend/src, frontend/tests, tests/access, tests/access_requests | ☐ |
| `tinte` | función/componente | `frontend/tests/accesibilidad/pares-contraste.ts` | `frontend/src/styles/tokens.css` | frontend/src | ☐ |

## Criterios de aceptación
- [x] El JSON de antes/después se muestra como lista de campos, no como texto crudo
- [~] Criterios comunes de diseño (FNC-037): tokens y clases existentes, sin estilos inline, carga/vacío/error/sin permiso, etiquetas visibles, 48 px; tema claro/oscuro y responsive medidos por pares de contraste y marcado, **no vistos en navegador**

## Verificación
| Comando (en `frontend/`) | Resultado |
|---|---|
| `npx tsc --noEmit` | salida 0 |
| `npm run lint` | salida 0, sin avisos |
| `npx vitest run` | salida 0; 20 archivos, 765 passed + 25 expected fail (las 25 conocidas, sin aumento) |
| `npx next build` | salida 0; `/audit/users/[id]` y `/audit/platforms/[id]` dinámicas |
| grep `style=`, `<style`, `.style.`, `#hex`, `rgb(`, IPs, `dangerouslySetInnerHTML` en lo cambiado | sin coincidencias |

- Pruebas nuevas: `tests/components/audit-log.test.tsx` (reescrita: 16), `tests/components/audit/audit-historiales.test.tsx` (7), enlace en `user-access-panel.test.tsx` e `inventory.test.tsx`, C1 en `limpiarBusqueda`.
- Par de contraste nuevo `error-text/body-bg`: pasa en todos los temas.
- **No verificado:** navegador (temas claro/oscuro, móvil y escritorio) ni con el backend real; sin revisor, tester ni auditores (por instrucción del orquestador).
- Conocido y fuera de alcance: el ✕ del `Modal` mide 36 px (DIS-031/DIS-032).

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-024, FNC-025, FNC-069, FNC-060
- Contrato → docs/contratos/auditoria.md

## Riesgos y reversión
- Puede avanzar con los datos simulados de FNC-069; se integra después del backend.
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-19 | Impacto de FNC-060 (backend, En revisión): `/audit`, `/audit/users/<id>` y `/audit/platforms/<id>` listos según el contrato. A considerar: el admin ya no ve eventos sin área (ni sus propios logins); el usuario recibe `ip`, `before` y `after` en `null`; parámetro inválido → `400 parametro_invalido` con `fields`; plataforma de área ajena → `404` (no `403`); `time` sigue en hora local sin `Z` (UTC pendiente del dueño) |
| 2026-10-20 | En curso (modo autónomo, autorizado por el dueño); worktree `pokemon-wt-d023` desde develop `ebfbe24` |
| 2026-10-20 | En revisión: filtros, paginación, detalle antes/después, historiales por usuario y plataforma, enlaces desde Usuarios e Inventario; propone DIS-035 |
