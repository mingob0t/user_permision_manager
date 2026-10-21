# DIS-021 — Inventario de permisos

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | inventario |
| **Prioridad** | Alta |
| **Estatus** | Hecha |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Commit local en `dis/DIS-021-inventario-permisos`, sin push |
| **Rama** | `dis/DIS-021-inventario-permisos` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- F-AUD-02 pide ver quién tiene qué plataforma, nivel, desde cuándo y quién aprobó
- Requerimientos: F-AUD-02, F-AUD-04

## Objetivo
- Pantalla `/inventory` con filtros (área, plataforma, usuario, nivel, estado, origen) y paginación, con alcance por rol

## Alcance
- **Incluye:**
  - Tabla responsive con las columnas del contrato
  - Enlaces al historial (DIS-020)
- **No incluye:**
  - Exportar (sugerencia)

## Archivos previstos
- `frontend/src/components/access/inventory-table.tsx`
- `frontend/src/components/access/inventory-filters.tsx`
- `frontend/src/app/inventory/page.tsx`

## Archivos cambiados
| Archivo | Cambio |
|---|---|
| `frontend/src/components/access/inventory.tsx` | Nuevo: contenedor (datos, filtros a la página 1, recarga, estados) |
| `frontend/src/components/access/inventory-filters.tsx` | Nuevo: selectores y buscador; `limpiarBusqueda`, `ORIGENES_INVENTARIO` |
| `frontend/src/components/access/inventory-table.tsx` | Nuevo: filas en `ResponsiveList` |
| `frontend/src/app/inventory/page.tsx` | Contenido y guarda `any_admin` |
| `frontend/src/components/app-shell.tsx` | Compartido: `/inventory` con `requires: 'any_admin'` (1 línea) |
| `frontend/tests/components/access/inventory.test.tsx` | Nuevo: 17 pruebas |
| `frontend/tests/components/navegacion-por-rol.test.tsx` | Menú esperado: Inventario solo para admins |
| `frontend/tests/accesibilidad/pares-contraste.ts` | 2 pares nuevos (filtros sobre el fondo de página) |

## Reutilización
- `access-status-badge.tsx`, `Select`, `TextInput`, estados de `ui.tsx`

## Impacto en elementos compartidos
| Elemento | Cambio | Quién lo usa | Validar |
|---|---|---|---|
| `NAV` en `app-shell.tsx` | "Inventario" pasa de todos a `any_admin` | Menú de todas las pantallas | El rol usuario ya no ve "Inventario" |
| `pares-contraste.ts` | Solo adición de 2 pares | Prueba de contraste | — |
| `FILTROS` (`my-access.tsx`), `NIVELES`, `AccessStatusBadge`, `ResponsiveList`, `ListPager`, `formatearFecha`, `listLoadError`, `Select`, `TextInput`, `Button`, `RequireRole` | Reutilizados sin cambios | — | — |

Salida de `impacto.py` (contra `develop`). Todas las filas son coincidencias de nombre de funciones locales (`Fila`, `Page`, `buscar`, `cambiar`, `pagina`, `sesion`, `opciones`, `tinte`) o de un tipo nuevo (`FiltrosInventario`) con otros archivos; ninguna es un elemento compartido modificado. No detecta el cambio de `NAV` (listado arriba).

```
**⚠ Impacto en elementos compartidos** (comparado contra `develop`): este cambio toca 9 elemento(s) usados en otras secciones: app/modules, frontend/src, frontend/tests, migrations, migrations/versions, tests, tests/directory, tests/provisioning. Valida cada una antes de integrar.

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `Fila` | función | `frontend/src/components/access/inventory-table.tsx` | `frontend/src/components/access/approvals-inbox.tsx`, `frontend/src/components/access/my-access.tsx`, `frontend/src/components/access/my-requests.tsx`, `frontend/src/components/access/responsive-list.tsx`, `frontend/src/components/users/user-access-panel.tsx`, `tests/directory/test_api.py` | frontend/src, tests/directory | ☐ |
| `FiltrosInventario` | tipo | `frontend/src/components/access/inventory-filters.tsx`, `frontend/src/components/access/inventory.tsx` | `app/modules/access/inventario.py`, `app/modules/access/inventario_api.py` | app/modules | ☐ |
| `Page` | función | `frontend/src/app/inventory/page.tsx` | `frontend/src/app/admin/connectors/page.tsx`, `frontend/src/app/admin/platforms/page.tsx`, `frontend/src/app/approvals/page.tsx`, `frontend/src/app/areas/page.tsx`, `frontend/src/app/audit/page.tsx`, `frontend/src/app/favorites/page.tsx`, `frontend/src/app/login/page.tsx`, `frontend/src/app/logout/page.tsx` (+6) | frontend/src | ☐ |
| `buscar` | función | `frontend/src/components/access/inventory-filters.tsx` | `app/modules/platforms/grupos.py`, `frontend/src/components/access/request-catalog.tsx`, `frontend/src/components/users-list.tsx`, `tests/conftest.py`, `tests/provisioning/test_ldap_provider.py` | app/modules, frontend/src, tests, tests/provisioning | ☐ |
| `cambiar` | función | `frontend/src/components/access/inventory.tsx` | `app/modules/access/consultas.py`, `app/modules/access/models.py`, `app/modules/api/helpers.py`, `app/modules/audit/ip_cliente.py`, `app/modules/platforms/api.py`, `app/modules/platforms/estado.py`, `frontend/src/components/areas/area-form.tsx`, `frontend/src/components/platforms/platform-integration-fields.tsx` (+7) | app/modules, frontend/src, frontend/tests, migrations/versions | ☐ |
| `opciones` | función | `frontend/tests/components/access/inventory.test.tsx` | `app/modules/provisioning/ejecucion.py`, `migrations/env.py`, `tests/provisioning/test_encolado.py`, `tests/provisioning/test_worker.py` | app/modules, migrations, tests/provisioning | ☐ |
| `pagina` | función | `frontend/tests/components/access/inventory.test.tsx` | `frontend/src/components/access/request-catalog.tsx`, `frontend/tests/components/access/approvals-inbox.test.tsx`, `frontend/tests/components/access/my-requests-view.test.tsx`, `frontend/tests/components/users/user-access-panel.test.tsx`, `tests/provisioning/test_api.py` | frontend/src, frontend/tests, tests/provisioning | ☐ |
| `sesion` | función | `frontend/tests/components/navegacion-por-rol.test.tsx` | `app/modules/provisioning/queue.py`, `frontend/src/components/users/user-access-panel.tsx`, `frontend/tests/components/users/user-access-panel.test.tsx`, `tests/conftest.py`, `tests/provisioning/test_ejecucion.py` | app/modules, frontend/src, frontend/tests, tests, tests/provisioning | ☐ |
| `tinte` | función/componente | `frontend/tests/accesibilidad/pares-contraste.ts` | `frontend/src/styles/tokens.css` | frontend/src | ☐ |
```

## Criterios de aceptación
- [x] En móvil cada fila se presenta como tarjeta legible (`ResponsiveList`: `dl` con etiquetas visibles bajo `md`); no verificado en navegador
- [~] Criterios comunes de diseño (FNC-037): tokens y clases existentes, sin estilos inline; carga, vacío, error y sin permiso; botones `.nexus-btn` de 48 px. Temas y responsive no verificados en navegador

## Decisiones del orquestador (pendientes de validar en la prueba de concepto)
| # | Decisión | Motivo |
|---|---|---|
| 1 | Menú y ruta solo para admin de área y superadmin (`any_admin`) | Encargo del orquestador; el backend responde 403 al usuario. Fila agregada en "Pantallas por rol" de REQUERIMIENTOS |
| 2 | Ocho datos en cinco columnas (usuario; plataforma y área; nivel y origen; desde y aprobó; estado), cada uno con su `dt` | Ocho columnas no caben en `md` con el menú lateral; mismo agrupamiento que Mis accesos |
| 3 | Sin refresco periódico; botón "Recargar" | Contrato `accesos.md`, sección Refresco |
| 4 | Usuario: búsqueda `q` por nombre o correo, aplicada al enviar; `user_id` no se expone | Evita una petición por tecla; no hay selector de usuarios con alcance por área |
| 5 | `q` sin caracteres de control y recortado a 100 antes de enviar; `maxLength` 100 | Valor más seguro: evita el 400 del servidor |
| 6 | Plataformas del filtro desde `GET /platforms`, acotadas a las áreas del admin y al área elegida; al cambiar de área se quita la plataforma ajena | Un filtro ajeno da lista vacía; así no se ofrece |
| 7 | `granted_by` null se muestra "Sistema" | Contrato: null = `sistema` |
| 8 | Origen: "Por solicitud" / "Automático (admin del área)" (no se reutiliza el texto de Mis accesos, en primera persona) | La vista es del administrador |
| 9 | Sin enlaces al historial | DIS-020 sigue en Propuesta; se agregan con ella |
| 10 | Archivo extra `inventory.tsx` (contenedor) | Una responsabilidad por archivo: datos aparte de filtros y filas |

## Verificación
| Comando (en `frontend/`) | Resultado |
|---|---|
| `npx tsc --noEmit -p .` | Salida 0 |
| `npx eslint src tests` y `npx next lint` | Salida 0, sin avisos |
| `npx vitest run` | Salida 0: 19 archivos, 723 passed + 25 expected fail (las 25 conocidas, sin aumento) |
| Tras las correcciones de accesibilidad: `npx tsc --noEmit -p .`, `npx eslint src tests`, `npx vitest run` | Ver la bitácora del 2026-10-20 (correcciones) |
| `grep` de `style=`, `<style`, `.style.`, `#hex`, `rgb(`, IPs en los archivos nuevos | Sin coincidencias |

- Pruebas nuevas: `inventory.test.tsx` (17) y 14 de contraste (2 pares × 7 temas), en verde.
- No verificado: navegador (temas claro y oscuro, móvil y escritorio). Sin revisor ni auditores (por instrucción).

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-024, FNC-025, FNC-069, FNC-070, FNC-059
- Contrato → docs/contratos/accesos.md

## Riesgos y reversión
- Puede avanzar con los datos simulados de FNC-069; se integra después del backend.
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-20 | Aprobada por el orquestador (modo autónomo) y En curso en el worktree `pokemon-wt-d023` |
| 2026-10-20 | Implementada: `inventory.tsx`, `inventory-filters.tsx`, `inventory-table.tsx`, página con guarda y menú `any_admin`; 15 pruebas y 14 de contraste. En revisión |
| 2026-10-20 | auditor-accesibilidad aprobado sin fallas nuevas; correcciones: "Recargar" con `aria-disabled` (conserva el foco, ignora el clic al cargar, "Recargando…" en la región viva), filtros con `Field` (etiqueta visible), vacío con filtros en `role="status"` (errores ya en `role="alert"` de `ErrorNote`), fila en "Pantallas por rol" de REQUERIMIENTOS. typecheck 0, lint 0, Vitest 725 passed + 25 expected fail (salida 0) |
