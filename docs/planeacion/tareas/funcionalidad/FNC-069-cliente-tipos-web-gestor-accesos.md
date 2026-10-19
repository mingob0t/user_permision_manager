# FNC-069 — Cliente y tipos web del gestor de accesos

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | web |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | lib-api |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Commit local, sin push |
| **Inicio** | 2026-10-19 |
| **Rama** | `fnc/FNC-069-cliente-web-gestor` (worktree `pokemon-wt-069`) |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- Todo `fetch` pasa por `request()` de `frontend/src/lib/api.ts`, que no se exporta; los tipos viven en `lib/types.ts` (206 líneas)
- La fase agrega unos 25 endpoints
- `api.ts` además tiene una IP de loopback como valor por defecto de `BACKEND_URL` (deuda 9, FNC-005)
- Requerimientos: Contratos de FNC-038

## Objetivo
- Agregar funciones y tipos por sección en archivos propios bajo `frontend/src/lib/access/`, reutilizando `request()` y `ApiError`, con datos simulados del contrato para que las pantallas avancen antes que el backend

## Alcance
- **Incluye:**
  - Exportar `request` (o un `apiRequest`) de `lib/api.ts` sin cambiar su comportamiento
  - `lib/access/{requests,grants,inventory,audit,connectors,provisioning,users,home}.ts` y `lib/access/types.ts`
  - Datos simulados del contrato tras una bandera de desarrollo, marcados como pendientes de integración
  - Pruebas de Vitest del cliente (forma de las peticiones y manejo de 401/403/409)
- **No incluye:**
  - Pantallas (DIS-013 a DIS-024)
  - Rewrites de `next.config.ts` (FNC-005)

## Hallazgos de seguridad que absorbe
- **FNC-005** parcial: la IP por defecto de `BACKEND_URL` en `lib/api.ts` pasa a `localhost` o a configuración. La parte de `next.config.ts` queda en FNC-005.

## Archivos previstos
- `frontend/src/lib/api.ts` (exportar `request`, valor por defecto sin IP)
- `frontend/src/lib/access/*.ts` (nuevos)
- `frontend/src/lib/access/__tests__/`

## Reutilización
- `request`, `ApiError`, `useAsync`

## Impacto en elementos compartidos
Salida real de `impacto.py` (contra `develop`, 2026-10-19):

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `BACKEND_URL` | variable de entorno | `frontend/src/lib/api.ts` | `frontend/next.config.ts` | frontend | ☐ |
| `Platform` | tipo | `frontend/src/lib/types.ts` | `app/authz.py`, `app/modules/api/crud.py`, `app/modules/api/routes.py`, `app/modules/audit/models.py`, `app/modules/auth/models.py`, `app/modules/core/models.py`, `frontend/src/components/platform-admin.tsx`, `frontend/src/components/platform-card.tsx` (+3) | app, app/modules, frontend/src, scratch, tests | ☐ |
| `PlatformInput` | tipo | `frontend/src/lib/types.ts` | `frontend/src/components/platform-admin.tsx` | frontend/src | ☐ |
| `request` | función | `frontend/src/lib/api.ts` | `app/__init__.py`, `app/authz.py`, `app/modules/api/admin.py`, `app/modules/api/auth.py`, `app/modules/api/crud.py`, `app/modules/api/helpers.py`, `app/modules/api/routes.py`, `app/modules/audit/ip_cliente.py` (+2) | app, app/modules, tests | ☐ |
| `save` | función | `frontend/src/components/users-list.tsx` | `app/modules/auth/routes.py`, `app/modules/notifications/routes.py`, `app/modules/settings/routes.py`, `frontend/src/components/areas-list.tsx`, `frontend/src/components/platform-admin.tsx`, `frontend/src/components/settings-panel.tsx`, `frontend/src/styles/global.css`, `tests/test_csrf.py` | app/modules, frontend/src, tests | ☐ |

- `BACKEND_URL`: real; `next.config.ts` conserva su IP por defecto (FNC-005, fuera de alcance)
- `Platform`: real en `platform-admin.tsx`, `platform-card.tsx`, `users-list.tsx` y las listas que reciben plataformas de `api`; los usos en `app/` y `tests/` son el modelo Python homónimo
- `PlatformInput`: real (`platform-admin.tsx`); solo campos opcionales nuevos, compatible
- `request`: real solo como nuevo export `apiRequest` (usado por `lib/access/`); en `app/` es el `request` de Flask (homónimo); comportamiento igual salvo los campos nuevos del error
- `save`: función local de `UserForm`; los demás son homónimos
- No los lista la herramienta: `ApiError` (campos nuevos aditivos; usado en `session-provider.tsx`), `UserInput` (sin `auth_source` ni `managed_area_ids`; solo `users-list.tsx`)
- Pantallas a validar: `/users` (alta y edición), `/admin/platforms`, todas las que llaman a `api` (manejo de errores)

## Variables y configuración
- `BACKEND_URL`: por defecto `http://localhost:5001` en `lib/api.ts` (constante `BACKEND_URL_POR_DEFECTO`); HISTORIAL.md
- `NEXT_PUBLIC_ACCESS_MOCKS` (nueva, dev): `1` activa los simulados; ignorada en producción; VARIABLES.md, HISTORIAL.md, `.env.example`

## Implementación
- `lib/api.ts`: `apiRequest` exportado; `ApiError` con `code`, `fields` (anidados aplanados con punto) y `correlationId`; `createPlatform`/`updatePlatform` devuelven `warnings`
- `lib/types.ts`: `Platform` con los campos de integración del contrato (obligatorios); `PlatformInput` con `integration_type` y DN; `UserInput` sin `auth_source` ni `managed_area_ids`
- `lib/access/`: `types`, `client` (bandera), `query`, `mocks`, `requests`, `grants`, `inventory`, `audit`, `connectors`, `provisioning`, `users`, `directory`, `home`
- `users-list.tsx` (mínimo para que el alta no dé 400): sin `auth_source`; áreas administradas por `usersApi.setManagedAreas`, solo superadmin; alta desde el directorio bloqueada con mensaje

## Decisiones del orquestador (pendientes de validar en la prueba de concepto)
- Pruebas en `frontend/tests/lib/access/` (Vitest solo incluye `tests/**`), no en `src/lib/access/__tests__/`
- `directory.ts` agregado: la forma nueva de `/auth-config` (FNC-043) no tenía cliente; `api.authConfig` heredado queda hasta DIS-023
- Plataformas v1 por `api.createPlatform`/`updatePlatform` existentes (sin duplicar); campos de `Platform` obligatorios como dice el contrato
- Alta desde el directorio en `/users`: se bloquea con mensaje en lugar de crear una cuenta local (el backend pondría contraseña local por defecto); espera FNC-079
- Selector "Áreas que administra" solo para el superadmin (único con permiso en `managed-areas`)
- Escrituras sin cuerpo (`approve`, `retry`, pruebas) envían `{}` para llevar `Content-Type: application/json` (contrato: otro → 415); `DELETE` sin cuerpo como el cliente existente
- Bandera de simulados solo con valor exacto `1` y nunca con `NODE_ENV=production`

## Impacto para las pantallas (no se tocaron)
- DIS-016: `GET /me` sigue con `can_manage_areas = is_admin()` (backend); para "Nueva área" del admin de área usar `is_area_admin` o pedir el permiso al backend. Errores: `ApiError.code` (`area_duplicada`, `area_con_plataformas`, `area_con_accesos`, `area_con_otros_admins`) y `fields`
- DIS-017: `POST /platforms` exige `integration_type` y `description`; `PUT` con DN solo superadmin (`403 dn_solo_superadmin`); `409 grupos_iguales`/`plataforma_con_accesos`; `422` con `fields`; mostrar `warnings`; `direct_link`/`logo_url` solo `https://`; `Platform` sin `user_ids`. `platform-admin.tsx` aún no envía `integration_type` (falla hasta DIS-017 cuando FNC-046 se integre); `setPlatformUsers` retirado en v1 (FNC-065)
- DIS-018/019: el selector de rol ofrece `administrador` al superadmin → `403 rol_reservado`; contraseña de cuentas `ldap`/`sso` → `400`; alta en OpenLDAP con `usersApi.createDirectoryAccount`; importar cuentas existentes: FNC-079
- DIS-023: usar `directoryApi` (forma nueva) en lugar de `api.authConfig`/`saveAuthConfig`/`testAuthConfig`
- CSRF (FNC-008, P13): el cliente aún no envía token; se agrega en `request()` cuando se defina la cabecera

## Hallazgo fuera de alcance
- Backend `POST /users` (`app/modules/api/crud.py`) asigna contraseña por defecto fija si no llega `password`; no se tocó (`app/` fuera de alcance). Propuesto revisar en FNC-079 o tarea de seguridad

## Verificación
| Comando (en `frontend/`) | Resultado real |
|---|---|
| `npm ci` | código 0 |
| `npm test` | 8 archivos, 224 passed, 88 expected fail (conocidas de contraste), código 0 |
| `npm run lint` | sin avisos ni errores, código 0 |
| `npx eslint tests` | código 0 |
| `npm run typecheck` | código 0 |
| `npm run build` | 14 páginas, código 0 |
| Regresión `tests/components/users-list.test.tsx` con el `users-list.tsx` de `develop` | 3 failed (falla primero); con el cambio, 3 passed |

- Pruebas nuevas: `tests/lib/access/{errores,peticiones,simulados}.test.ts` (401/403/409/422/500, forma de cada endpoint, bandera) y `tests/components/users-list.test.tsx`
- No verificado: contra el backend real (muchos endpoints aún no existen); pantalla `/users` en navegador, temas y móvil (sin cambios visuales; solo condición de render y un mensaje de error existente)
- Sin revisor, tester ni auditor-accesibilidad: el orquestador los lanza

## Commits / PR
- Commit local `[FNC-069]` en `fnc/FNC-069-cliente-web-gestor`; sin push, merge ni PR


## Criterios de aceptación
- [x] Cada endpoint del contrato tiene su función tipada (revisión contra el contrato; prueba por endpoint)
- [x] Las pantallas existentes siguen funcionando (typecheck, lint, build y pruebas)
- [ ] Criterios comunes web (FNC-037)

## Impacto cruzado
- Genera → DIS-013 a DIS-024
- Origen ← FNC-037
- Depende de → FNC-036, FNC-024, FNC-025, FNC-038

## Riesgos y reversión
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-19 | Aprobada (modo autónomo, vía orquestador); implementada; En revisión |
