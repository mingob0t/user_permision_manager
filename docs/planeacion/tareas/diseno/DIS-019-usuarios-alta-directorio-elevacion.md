# DIS-019 — Usuarios: alta en el directorio y elevación a admin

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | usuarios |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Commit local en la rama, sin push |
| **Rama** | `dis/DIS-019-alta-directorio-elevacion` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- El alta actual crea cuentas locales con rol libre; RF-04 y F-USR-02 piden alta en OpenLDAP y que solo el superadmin eleve y asigne áreas administradas
- Requerimientos: F-USR-02, F-USR-03, F-AREA-02, RF-04

## Objetivo
- Formulario de alta en el directorio (campos de ADR-004) y, solo para el superadmin, acciones "Hacer admin" con selección de áreas administradas y "Quitar admin"

## Alcance
- **Incluye:**
  - Formulario en componente propio
  - Acciones de rol solo visibles al superadmin
  - Mensajes de 409 (identificador existente)
- **No incluye:**
  - Revocación (DIS-018)
  - Purga de inactivos (sin cambios)

## Archivos previstos
- `frontend/src/components/users/directory-account-form.tsx`
- `frontend/src/components/users/admin-role-dialog.tsx`
- `frontend/src/components/users-list.tsx` (importaciones y permisos de botones)

## Archivos reales
| Archivo | Cambio |
|---|---|
| `frontend/src/components/users/directory-account-form.tsx` | Nuevo: `DirectoryAccountForm` (`POST /users/directory`) |
| `frontend/src/components/users/directory-account-errors.ts` | Nuevo: `validarAlta`, `cuerpoAlta`, `describeDirectoryAccountError` |
| `frontend/src/components/users/admin-role-dialog.tsx` | Nuevo: `AdminAreasDialog`, `RemoveAdminDialog`, `efectoAdmin` |
| `frontend/src/components/users/admin-role-errors.ts` | Nuevo: `describeRoleError` |
| `frontend/src/components/users/area-checklist.tsx` | Nuevo: `AreaChecklist` (casillas de áreas con estados) |
| `frontend/src/components/users-list.tsx` | "Nuevo usuario" abre el alta en el directorio; `UserForm` sin rol, áreas administradas ni contraseña (salvo emergencia); botones de rol del superadmin; aviso `status` con foco |
| `frontend/tests/components/users/directory-account-form.test.tsx`, `admin-role-dialog.test.tsx` | Nuevas (33 pruebas) |
| `frontend/tests/components/users-list.test.tsx` | Reescritas las 2 pruebas del alta local con rol (comportamiento retirado); +1 cuenta de emergencia |
| `frontend/tests/accesibilidad/pares-contraste.ts` | Par `checkbox-marcada/panel` |

## Reutilización
- `Modal`, `Field`, `TextInput`, `Checkbox`, `Button` (`form.tsx`); `FieldHint`, `FieldErrorNote`, `describedBy`, `focusFirstError` (`platforms/field-notes.tsx`); `ErrorNote`, `Spinner`, `Card` (`ui.tsx`); `usersApi.createDirectoryAccount` y `setManagedAreas` (FNC-069); `api.updateUser`
- Patrón de diálogo de `ApproveDialog`/`RevokeAccessDialog` (DIS-015, DIS-018): botón primario, `aria-disabled` al enviar, aviso `role="status"` con foco
- No se usó `Select` (no hay selector de rol) ni `ConfirmDialog` (dice "Eliminando…" y usa `danger`, que falla AA hasta DIS-004)
- Nuevo reutilizable: `AreaChecklist`, agregado al catálogo

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `users-list.tsx` (`UsersList`, `UserForm`) | Pantalla | `/users` (`app/users/page.tsx`); `tests/components/users/user-access-panel.test.tsx` (sigue en verde) | Pendiente |

Salida de `impacto.py` (contra `develop`):

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `UsersList` | función | `frontend/src/components/users-list.tsx` | `frontend/src/app/users/page.tsx`, `frontend/tests/components/users/user-access-panel.test.tsx` | frontend/src, frontend/tests | ☐ |
| `dialogo` | función | `frontend/tests/components/users-list.test.tsx` | `approvals-inbox.test.tsx`, `request-catalog.test.tsx`, `areas-list.test.tsx`, `audit-log.test.tsx`, `platform-admin.test.tsx`, `user-access-panel.test.tsx` | frontend/tests | ☐ |
| `remove` | función | `frontend/src/components/users-list.tsx` | `app/modules/api/routes.py`, `areas-list.tsx`, `platform-admin.tsx`, `lib/access/connectors.ts`, … (+5) | app/modules, frontend/src, frontend/tests, tests, tests/audit | ☐ |
| `save` | función | `frontend/src/components/users-list.tsx` | `auth/routes.py`, `notifications/routes.py`, `settings/routes.py`, `area-form.tsx`, `platform-admin.tsx`, … (+7) | app/modules, frontend/src, frontend/tests, tests | ☐ |
| `tinte` | función/componente | `frontend/tests/accesibilidad/pares-contraste.ts` | `frontend/src/styles/tokens.css` | frontend/src | ☐ |

- Real: solo `UsersList`/`UserForm` (pantalla `/users`). `dialogo`, `remove`, `save` y `tinte` son coincidencias de nombre con funciones locales de otros archivos (no se importan); `tinte` no cambió (se agregó un par junto a él)
- Sin cambios en `form.tsx`, `ui.tsx`, `field-notes.tsx`, tokens ni CSS

## Criterios de aceptación
- [x] Un admin de área no ve opciones de rol (prueba "admin de área: no ve opciones de rol"; sin selector Rol en Editar)
- [ ] Criterios comunes de diseño (FNC-037): tokens y clases existentes, sin inline ni literales, estados de carga, vacío y error, AA medido en pares; falta verificación en navegador (claro/oscuro, móvil/escritorio)

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-024, FNC-025, FNC-069, FNC-064, FNC-044, DIS-018 (mismo archivo, en secuencia)
- Contrato → docs/contratos/usuarios-directorio.md y areas-y-roles.md

## Riesgos y reversión
- Puede avanzar con los datos simulados de FNC-069; se integra después del backend.
- Reversión: revertir la rama.

## Decisiones del orquestador (pendientes de validar en la prueba de concepto)
| # | Decisión | Motivo (valor más seguro) |
|---|---|---|
| 1 | "Nuevo usuario" abre el alta en el directorio (`POST /users/directory`) y deja de crear cuentas locales | RF-04/F-USR-02; `POST /users` con contraseña ya es `400` (FNC-077) |
| 2 | `UserForm` (Editar) ya no tiene selector de rol ni "Áreas que administra"; el rol solo cambia con las acciones del superadmin | Criterio de aceptación; ofrecía `administrador` (siempre `rol_reservado`) y `admin_area` al admin de área (`403`); un patrón, una solución |
| 3 | Contraseña en Editar solo para la cuenta de emergencia (`role=administrador` y `auth_source=local`); ya no en el alta | Contrato areas-y-roles v2 (FNC-077); P8: el portal no maneja contraseñas de directorio |
| 4 | Hacer admin exige al menos un área; para dejar ninguna, "Quitar admin" | Un admin de área sin áreas no tiene efecto y confunde; el contrato permite 0 en `managed-areas` |
| 5 | Hacer admin en dos pasos (`PUT /users/<id>` `admin_area` → `managed-areas`); si falla el segundo, se explica que ya es admin sin áreas y se recarga; reintentar es seguro (mismo rol se ignora) | No hay endpoint atómico; mejor informar el estado real que ocultarlo |
| 6 | Botones de confirmar primarios (no `danger`) en Hacer/Quitar admin | `danger` falla AA hasta DIS-004 (mismo criterio que DIS-018) |
| 7 | El efecto se explica en el propio diálogo (áreas concretas, permisos y accesos automáticos de FNC-055) y ese diálogo es la confirmación | Acción sensible; evita dos diálogos anidados |
| 8 | Admin de área: el alta solo ofrece sus áreas (`session.managed_areas`) y exige una; superadmin: todas (`GET /areas`), opcional | Contrato: `area_ids` obligatorio para admin, ajenas → `404` |
| 9 | Errores sin texto del servidor: 409 en su campo; 422 con mensaje propio por campo | Lineamiento de mensajes (DIS-015/DIS-018) |
| 10 | "Buscar en directorio" → "Dar de alta" sigue bloqueado con su aviso | Importar cuentas existentes es FNC-079 (Propuesta) |
| 11 | No se agregó el par del borde de `.nexus-checkbox` (falla 3:1 en los 7 temas): se propone DIS-039 | Subiría las fallas conocidas de 25 a 32; el componente es compartido y fuera de alcance |
| 12 | Etiqueta "Áreas admin" en la fila (nombre accesible completo "Áreas que administra …") | Texto corto para no romper la fila; `aria-label` explica |

## Verificación
| Comando (en `frontend/`) | Resultado real |
|---|---|
| `npm run typecheck` | salida 0 |
| `npm run lint` | salida 0, sin avisos |
| `npx eslint tests/components/users tests/components/users-list.test.tsx tests/accesibilidad/pares-contraste.ts` | salida 0 |
| `npx vitest run` | 1.ª corrida: salida 1 (1 falla en `areas-list.test.tsx`, ajena, intermitente → DIS-040); 2.ª y 3.ª: salida 0, 850 passed + 25 expected fail (875) |
| `npx vitest run tests/components/areas-list.test.tsx` ×3 | 18 passed las 3 veces |
| `npx next build` | salida 0 (`/users` 11.7 kB) |
| `grep` de `style=`, `<style`, `.style.`, `style={{`, `#hex`, `rgb(`, IPs y `text-red/white/black/gray` en los archivos tocados | sin coincidencias |

- Fallas de contraste conocidas: 25 (sin cambio). Par nuevo `checkbox-marcada/panel` pasa en los 7 temas
- **No verificado en navegador**: tema claro y oscuro, móvil y escritorio y estados no se vieron en pantalla (no se levantó la app con backend). Solo pruebas jsdom y medición de tokens
- Sin `revisor`, `tester`, `auditor-accesibilidad` ni `auditor-seguridad` (instrucción del orquestador); el cambio toca datos de usuarios y roles: pendiente `auditor-seguridad` en modo cambio y `auditor-accesibilidad` antes de cerrar

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-21 | Aprobada en modo autónomo (autorizado por el dueño) y En curso |
| 2026-10-21 | Implementada: alta en el directorio, Hacer/Quitar admin y áreas administradas (solo superadmin), Editar sin rol ni contraseña; 33 pruebas nuevas (+1 en users-list); typecheck, lint, Vitest y build en 0; En revisión. Genera DIS-039 y DIS-040 |
