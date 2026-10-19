# DIS-016 — Áreas: alta por el admin y asignación de admins por el superadmin

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | areas |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Commit local, sin push |
| **Rama** | `dis/DIS-016-pantalla-areas` (worktree `pokemon-wt-d016`) |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- En `/areas` (`areas-list.tsx`) solo el superadmin crea áreas; no hay forma explícita de asignar admins (F-AREA-01/02)
- Requerimientos: F-AREA-01, F-AREA-02, RF-04

## Objetivo
- Permitir al admin crear sus áreas y al superadmin asignar o quitar admins de un área

## Alcance
- **Incluye:**
  - Botón y formulario de alta visibles para `admin_area`
  - Panel "Administradores del área" solo para el superadmin, con búsqueda de usuarios
  - Lo nuevo en archivos propios; `areas-list.tsx` solo los importa
- **No incluye:**
  - Rediseño de la lista de áreas
  - Estilos inline existentes de `areas-list.tsx` (DIS-012)

## Archivos previstos
- `frontend/src/components/areas/area-admins-panel.tsx`
- `frontend/src/components/areas/area-form.tsx` (si se extrae el existente)
- `frontend/src/components/areas-list.tsx` (importaciones y permiso del botón)

## Archivos modificados
| Archivo | Cambio |
|---|---|
| `frontend/src/components/areas/area-form.tsx` (nuevo) | `AreaForm` extraído; errores por campo (`fields`, `aria-invalid`/`aria-describedby`) y mensajes 409; el alta no envía color si no se elige |
| `frontend/src/components/areas/area-admins-panel.tsx` (nuevo) | Panel "Administradores de <área>": cuentas `admin_area`, búsqueda, casillas, `usersApi.setManagedAreas`; quitar se confirma; carga, vacío, error y "Cambios guardados" |
| `frontend/src/components/areas/area-errors.ts` (nuevo) | `MENSAJES_AREAS` (tabla de errores del contrato), `mensajeDeError`, `erroresDeCampo` |
| `frontend/src/components/areas-list.tsx` | Importa lo anterior; `RequireRole any_admin`; "Nueva área" para admin de área; "Eliminar" en las áreas propias; "Administradores" solo superadmin; áreas creadas en la visita quedan gestionables; error de baja con mensaje del contrato |
| `frontend/tests/components/areas-list.test.tsx` (nuevo) | 15 pruebas: por rol, panel, 422, 409 y estados |
| `frontend/tests/accesibilidad/colores-literales.excepciones.ts` | Tope de `areas-list.tsx`: `hex` 2 → 0 (se quitó el literal) |

## Reutilización
- Reutilizados: `Modal`, `ConfirmDialog`, `Field`, `TextInput`, `TextArea`, `Checkbox`, `Button` (`form.tsx`); `Badge`, `Card`, `EmptyNote`, `ErrorNote`, `Spinner` (`ui.tsx`); `RequireRole`, `meetsRequirement`; `useAsync`, `api`, `ApiError`, `usersApi`
- `Select` no se usó

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `areas-list.tsx` (`AreasList`) | Pantalla | `/areas` (`app/areas/page.tsx`) | Pruebas Vitest; visual pendiente |
| `colores-literales.excepciones.ts` | Datos de prueba | `colores-literales.test.ts` | `npm test` en verde |

Componentes compartidos (`form.tsx`, `ui.tsx`, `require-role.tsx`, `lib/`) reutilizados sin modificar.

Salida real completa de `impacto.py` (contra `develop`, tras las correcciones de revisión):

**⚠ Impacto en elementos compartidos** (comparado contra `develop`): este cambio toca 14 elemento(s) usados en otras secciones: app, app/modules, frontend, frontend/src, frontend/tests, migrations, migrations/versions, tests, tests/areas, tests/audit, tests/directory, tests/notifications, tests/platforms, tests/users, utils. Valida cada una antes de integrar.

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `AreasList` | función | `frontend/src/components/areas-list.tsx` | `frontend/src/app/areas/page.tsx` | frontend/src | ☑ Real: misma exportación, cambia `/areas` por rol (pruebas) |
| `Rol` | tipo | `frontend/tests/components/areas-list.test.tsx` | `app/authz.py`, `frontend/src/components/users-list.tsx`, `frontend/tests/components/navegacion-por-rol.test.tsx`, `frontend/tests/components/users-list.test.tsx`, `tests/fabricas.py`, `tests/test_proteccion_por_rol.py`, `tests/test_sso.py`, `utils/check_db.py` | app, frontend/src, frontend/tests, tests, utils | Homónimo: local no exportado |
| `TopeLiterales` | tipo | `frontend/tests/accesibilidad/colores-literales.excepciones.ts` | `frontend/tests/accesibilidad/colores-literales.test.ts` | frontend/tests | ☑ Real: el tipo no cambia; baja el tope |
| `administra` | función | `frontend/src/components/areas/area-admins-panel.tsx` | `app/authz.py`, `app/modules/api/admin.py`, `app/modules/api/crud.py`, `app/modules/api/routes.py`, `app/modules/areas/api.py`, `app/modules/auth/models.py`, `app/modules/platforms/api.py`, `app/modules/users/api.py` (+8) | app, app/modules, frontend/src, frontend/tests, tests | Homónimo: local no exportado |
| `admins` | función/componente | `frontend/src/components/areas/area-admins-panel.tsx` | `app/authz.py`, `app/modules/api/crud.py`, `app/modules/areas/baja.py`, `app/modules/auth/models.py`, `app/modules/notifications/access_notifications.py`, `tests/areas/test_alta_y_baja_por_admin.py`, `tests/directory/test_writer.py`, `tests/notifications/test_access_notifications.py` (+4) | app, app/modules, tests, tests/areas, tests/directory, tests/notifications, tests/users | Homónimo: local no exportado |
| `area` | función | `frontend/tests/components/areas-list.test.tsx` | `app/modules/api/crud.py`, `app/modules/api/routes.py`, `app/modules/areas/api.py`, `app/modules/areas/baja.py`, `app/modules/audit/models.py`, `app/modules/core/models.py`, `app/modules/directory/configuracion.py`, `app/modules/notifications/access_notifications.py` (+25) | app/modules, frontend/src, migrations/versions, tests, tests/areas, tests/audit, tests/notifications, tests/platforms, tests/users | Homónimo: local no exportado |
| `coincide` | función | `frontend/src/components/areas/area-admins-panel.tsx` | `frontend/src/components/audit-log.tsx`, `frontend/src/components/platform-catalog.tsx`, `tests/audit/test_registro_ampliado.py` | frontend/src, tests/audit | Homónimo: local no exportado |
| `dialogo` | función | `frontend/tests/components/areas-list.test.tsx` | `frontend/tests/components/users-list.test.tsx` | frontend/tests | Homónimo: local no exportado |
| `guardar` | función | `frontend/src/components/areas/area-admins-panel.tsx` | `app/modules/api/admin.py`, `app/modules/audit/sanitizar.py`, `frontend/src/components/platform-admin.tsx`, `frontend/src/components/settings-panel.tsx`, `frontend/src/components/users-list.tsx`, `frontend/tests/lib/access/peticiones.test.ts` | app/modules, frontend/src, frontend/tests | Homónimo: local no exportado |
| `marcado` | función/componente | `frontend/src/components/areas/area-admins-panel.tsx` | `app/modules/areas/validacion.py`, `frontend/src/components/favorites-list.tsx`, `frontend/src/components/form.tsx`, `frontend/src/components/ui.tsx`, `frontend/tailwind.config.ts`, `frontend/tests/lib/api.test.ts` | app/modules, frontend, frontend/src, frontend/tests | Homónimo: local no exportado |
| `remove` | función | `frontend/src/components/areas-list.tsx` | `app/modules/api/routes.py`, `frontend/src/components/platform-admin.tsx`, `frontend/src/components/users-list.tsx`, `frontend/src/lib/access/connectors.ts`, `frontend/tests/lib/access/peticiones.test.ts`, `tests/audit/test_inmutabilidad.py`, `tests/conftest.py`, `tests/test_arranque.py` | app/modules, frontend/src, frontend/tests, tests, tests/audit | Homónimo: local no exportado |
| `save` | función | `frontend/src/components/areas-list.tsx`, `frontend/src/components/areas/area-form.tsx` | `app/modules/auth/routes.py`, `app/modules/notifications/routes.py`, `app/modules/settings/routes.py`, `frontend/src/components/platform-admin.tsx`, `frontend/src/components/settings-panel.tsx`, `frontend/src/components/users-list.tsx`, `frontend/src/lib/access/connectors.ts`, `frontend/src/styles/global.css` (+3) | app/modules, frontend/src, frontend/tests, tests | Homónimo: local no exportado |
| `tarjeta` | función | `frontend/tests/components/areas-list.test.tsx` | `frontend/src/components/platform-admin.tsx`, `frontend/src/components/platform-card.tsx` | frontend/src | Homónimo: local no exportado |
| `usuario` | función | `frontend/tests/components/areas-list.test.tsx` | `app/__init__.py`, `app/authz.py`, `app/modules/api/admin.py`, `app/modules/api/auth.py`, `app/modules/api/crud.py`, `app/modules/api/helpers.py`, `app/modules/api/routes.py`, `app/modules/audit/inmutabilidad.py` (+62) | app, app/modules, frontend/src, frontend/tests, migrations, migrations/versions, tests, tests/areas, tests/audit, tests/directory, tests/notifications, tests/platforms, tests/users, utils | Homónimo: local no exportado |

- Homónimos: funciones locales no exportadas (`administra`, `admins`, `coincide`, `guardar`, `marcado` en `area-admins-panel.tsx`; `remove`/`save` en la pantalla y el formulario) y auxiliares del archivo de prueba (`Rol`, `area`, `dialogo`, `tarjeta`, `usuario`); las coincidencias son otros símbolos con el mismo nombre
- Reales: `AreasList` (validar `/areas` por rol) y el tope de `colores-literales.excepciones.ts`

## Decisiones del orquestador (pendientes de validar en la prueba de concepto)
- "Nueva área" por rol (`any_admin`), no por `can_manage_areas` (en `/me` sigue siendo `is_admin()`, FNC-045); backend sin tocar
- Admin de área ve "Eliminar" en sus áreas (contrato: `DELETE` 200 en las suyas; `409 area_con_otros_admins` lo explica)
- Asignación por área: panel con las cuentas `admin_area`; cada cambio llama a `managed-areas` con la lista completa del usuario (agrega o quita solo esta área)
- Quitar admins se confirma (`ConfirmDialog`, "Quitar"); tras un error se recarga el estado real (lo previo al error queda aplicado)
- El panel queda abierto tras guardar con "Cambios guardados" (no hay componente de éxito estándar)
- Alta sin color elegido: no se envía y el servidor aplica su color por omisión (mismo valor que fijaba la pantalla); evita el literal hex
- Áreas creadas en la visita se tratan como propias sin pedir `/me` otra vez
- `/areas` con `RequireRole any_admin` dentro del componente (estado "sin permiso"; sin tocar `app/`)
- Error de campo con `<span class="text-error">` local (`FieldError`); `Field` compartido sin cambios

## Propuestas
- Estándar de error por campo (`Field` con `error`, `aria-invalid`) y de mensaje de éxito: sugerir tarea DIS para `docs/estandarizacion/`
- `can_manage_areas` de `/me` para `admin_area`: tarea FNC si se quiere permiso explícito

## Criterios de aceptación
- [x] Un admin de área no ve el panel de asignación (prueba)
- [ ] Criterios comunes de diseño (FNC-037): pendiente la verificación visual

## Verificación
| Comando (en `frontend/`) | Resultado real |
|---|---|
| `npm ci` | exit 0 |
| `npm test` | exit 0; 11 archivos, 273 pasan, 88 fallas esperadas (`it.fails` de contraste ya conocidas) |
| `npx vitest run tests/components/areas-list.test.tsx` | 15/15 pasan |
| `npm run lint` | exit 0; sin avisos ni errores |
| `npx eslint tests vitest.config.ts` | exit 0 |
| `npm run typecheck` | exit 0 |
| `npm run build` | exit 0; `/areas` 4.82 kB |
| `grep` estilos inline, `#hex`, `rgb(`, IPs en lo nuevo | Sin coincidencias; queda el `style={{}}` previo de `areas-list.tsx` (DIS-012, fuera de alcance) |

- No verificado: tema claro/oscuro, móvil/escritorio y contraste en pantalla (sin backend levantado en el worktree). Solo se usan componentes y clases existentes (`Modal`, `ConfirmDialog`, `Field`, `TextInput`, `Checkbox`, `Button`, `Badge`, `EmptyNote`, `ErrorNote`, `Spinner`, `text-error`, `text-label`, `text-primary`)
- Prueba de contraste y de colores literales siguen en verde; sin fallas nuevas
- Sin integración con el backend real; sin revisores (por instrucción del orquestador)
- Accesibilidad (auditor-accesibilidad, 2026-10-19, modo cambio): **Con observaciones**. Fallas nuevas: nombre accesible de Editar/Eliminar/Administradores sin el área (`areas-list.tsx:131,139,147`); `FieldError` `text-error` 3.76:1 en claro (`area-form.tsx:25`); texto `text-primary` de "Administradores" 3.45:1 en oscuro (`areas-list.tsx:139`); sin foco al primer campo inválido ni `aria-invalid` en el error de nombre vacío (`area-form.tsx:61`); `role="status"` montado junto con su contenido (`area-admins-panel.tsx:89`). Sin estilos inline ni colores literales nuevos

## Revisión (2026-10-19)
- `auditor-accesibilidad`: **Con observaciones**. Corregido con prueba que primero falló (3 pruebas nuevas, 18/18):
  - `aria-label` con el nombre del área en Editar, Administradores y Eliminar
  - Nombre vacío: error ligado al campo (`aria-invalid`, `aria-describedby`) y foco al campo (también con `422` en `name`)
  - `role="status"` del panel siempre montado; solo cambia su texto
- Heredado de tokens, no corregido aquí: `text-error` fijo en claro (`FieldError` 3.76:1) → DIS-002; `text-primary` en oscuro (3.45:1) → DIS-001; `text-label/60` de la pista → DIS-005; borde de `nexus-checkbox` → DIS-006; botones de tarjeta de 24 px → DIS-008
- `revisor`: **Requiere cambios** (documentación): salida completa de `impacto.py` y lista real de Reutilización; corregido
- Tras las correcciones: `npm test` exit 0 (276 pasan, 88 fallas esperadas), `lint` 0, `eslint tests` 0, `typecheck` 0, `build` 0 (`/areas` 4.9 kB)

## Commits / PR
- `364b58c` `[DIS-016]` implementación; segundo commit `[DIS-016]` con las correcciones de revisión; en `dis/DIS-016-pantalla-areas`; sin push, merge ni PR

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-024, FNC-025, FNC-069, FNC-044, FNC-045
- Contrato → docs/contratos/areas-y-roles.md

## Riesgos y reversión
- Puede avanzar con los datos simulados de FNC-069; se integra después del backend.
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-19 | Aprobada (modo autónomo, vía orquestador); implementada; En revisión |
| 2026-10-19 | Revisión: accesibilidad Con observaciones y revisor Requiere cambios; corregidos; heredados de tokens a DIS-001/002/005/006/008; sigue En revisión |
