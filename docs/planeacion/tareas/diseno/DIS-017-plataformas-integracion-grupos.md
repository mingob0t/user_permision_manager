# DIS-017 — Plataformas: tipo de integración y grupos por nivel

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | plataformas |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Commit local, sin push |
| **Rama** | `dis/DIS-017-pantalla-plataformas` (worktree `pokemon-wt-d017`) |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No (cierra SEG-24 del frontend; se recomienda revisión del cambio) |

## Contexto
- `platform-admin.tsx` (327 líneas) no tiene tipo de integración ni grupos (F-PLAT-01); la asignación directa de usuarios ya no está en la pantalla
- `POST /platforms` exige `integration_type` desde FNC-046: el alta actual responde `422` (bloquea staging)
- SEG-24 del frontend: `platform-card.tsx` pintaba `direct_link` en `href` sin validar
- Requerimientos: F-PLAT-01, RF-02

## Objetivo
- Agregar al formulario de plataforma el tipo (`ldap`/`conector`), los grupos de nivel usuario y admin con ayuda de formato, y el enlace a la configuración del conector (superadmin); retirar la asignación directa de usuarios si FNC-065 se aprueba

## Alcance
- **Incluye:**
  - Sección "Integración" en un componente propio
  - Mensajes de validación del backend (DN fuera de base, grupos iguales)
  - Aviso de que cambiar grupos con accesos activos no está permitido
- **No incluye:**
  - Dividir `platform-admin.tsx` (DIS-011)
  - Estilos inline existentes (DIS-012)
  - Título "Plataformas" del catálogo (lo cubre DIS-013)

## Archivos
| Archivo | Cambio |
|---|---|
| `frontend/src/components/platforms/platform-integration-fields.tsx` | Nuevo: sección Integración (tipo, DN por nivel, enlace a conectores, bloqueo por accesos) |
| `frontend/src/components/platforms/platform-save-errors.ts` | Nuevo: `describeSaveError` (422 por campo, 403/404/409 con mensaje del contrato) |
| `frontend/src/components/platforms/platform-save-notice.tsx` | Nuevo: aviso de guardado con `warnings` |
| `frontend/src/lib/enlace-seguro.ts` | Nuevo: `enlaceSeguro` (solo `https://`, SEG-24) |
| `frontend/src/components/platform-admin.tsx` | Validación previa, cuerpo por rol, errores por campo, aviso, error al eliminar, `RequireRole any_admin`, enlaces solo https en la tabla |
| `frontend/src/components/platform-card.tsx` | `href` solo con `enlaceSeguro` |
| `frontend/tests/components/platform-admin.test.tsx`, `platform-card.test.tsx` | Nuevas pruebas |

## Reutilización
- `Field`, `TextInput`, `Select`, `Button`, `Modal` de `form.tsx`; `Card`, `Badge`, `ErrorNote`, `EmptyNote` de `ui.tsx`; `RequireRole`; `api.createPlatform`/`updatePlatform` y `ApiError` (`code`, `fields`) de FNC-069
- Sin componentes, clases ni tokens nuevos; el error por campo es `ErrorNote` dentro del `Field`
- Al catálogo: `enlaceSeguro`, `PlatformIntegrationFields`, `describeSaveError`, `PlatformSaveNotice`

## Comportamiento por rol
| Caso | Admin de área | Superadmin |
|---|---|---|
| Alta: tipo | Obligatorio | Obligatorio |
| Alta: DN | No los ve ni los envía | Opcionales; vacío = convención del directorio |
| Edición: tipo | Solo lectura | "Sin cambiar" (no se envía) o nuevo tipo |
| Edición: DN | No | Solo se envían si cambian y no están vacíos |
| `conector` | Texto explicativo | Además, botón "Configurar conectores" (`/admin/connectors`) |
| `active_grants > 0` | Tipo, DN y área deshabilitados con aviso | Igual |

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `PlatformCard` (`platform-card.tsx`) | Componente | Catálogo `/platforms` (`platform-catalog.tsx`), Favoritos (`favorites-list.tsx`) | Pruebas de componente; visual no revisado en esas vistas |
| `PlatformAdmin` (`platform-admin.tsx`) | Pantalla | `/admin/platforms` (`app/admin/platforms/page.tsx`); firma sin cambios | Pruebas y capturas |

Salida real de `impacto.py` (contra `develop`):

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `PlatformAdmin` | función | `frontend/src/components/platform-admin.tsx` | `frontend/src/app/admin/platforms/page.tsx` | frontend/src | ☑ |
| `body` | función/componente | `frontend/src/components/platform-card.tsx` | `app/modules/api/admin.py`, `app/modules/notifications/models.py`, `app/modules/notifications/services.py`, `frontend/src/app/layout.tsx`, `frontend/src/components/app-shell.tsx`, `frontend/src/components/form.tsx`, `frontend/src/components/settings-panel.tsx`, `frontend/src/components/users-list.tsx` (+18) | app/modules, frontend, frontend/src, frontend/tests, migrations/versions, tests, tests/notifications | ☑ homónimo |
| `registerVisit` | función | `frontend/src/components/platform-card.tsx` | `frontend/src/lib/api.ts` | frontend/src | ☑ sin cambio |
| `remove` | función | `frontend/src/components/platform-admin.tsx` | `app/modules/api/routes.py`, `frontend/src/components/areas-list.tsx`, `frontend/src/components/users-list.tsx`, `frontend/src/lib/access/connectors.ts`, `frontend/tests/lib/access/peticiones.test.ts`, `tests/audit/test_inmutabilidad.py`, `tests/conftest.py`, `tests/test_arranque.py` | app/modules, frontend/src, frontend/tests, tests, tests/audit | ☑ homónimo |
| `save` | función | `frontend/src/components/platform-admin.tsx` | `app/modules/auth/routes.py`, `app/modules/notifications/routes.py`, `app/modules/settings/routes.py`, `frontend/src/components/areas-list.tsx`, `frontend/src/components/settings-panel.tsx`, `frontend/src/components/users-list.tsx`, `frontend/src/lib/access/connectors.ts`, `frontend/src/styles/global.css` (+3) | app/modules, frontend/src, frontend/tests, tests | ☑ homónimo |
| `validate` | función | `frontend/src/components/platform-admin.tsx` | `app/modules/api/admin.py`, `app/modules/directory/ldap_client.py`, `tests/directory/test_ldap_client.py` | app/modules, tests/directory | ☑ homónimo |

- **Real:** `PlatformAdmin` (misma exportación y firma; ahora con guarda `any_admin`)
- **Homónimos:** `body`, `remove`, `save`, `validate` son variables o funciones locales del componente; los usos listados son otras funciones con el mismo nombre (Python, CSS, otras pantallas)
- **Sin cambio:** `registerVisit` (la herramienta lo marca por estar junto a la línea cambiada; la función local y `api.registerVisit` siguen igual)
- **No detectado por la herramienta y real:** `PlatformCard` (cambió el `href`); afecta Catálogo y Favoritos

## Criterios de aceptación
- [x] Los textos explican "grupo de acceso" sin exigir conocer LDAP más allá del DN
- [x] Criterios comunes de diseño (FNC-037): temas por tokens, sin estilos inline nuevos, estados de carga/vacío/error/sin permiso, textos en español

## Decisiones del orquestador (pendientes de validar en la prueba de concepto)
- El tipo no tiene valor por defecto en el alta: hay que elegirlo (evita un `422` de `ldap` sin directorio por omisión)
- DN vacío no se envía: el backend lo deriva en el alta y lo conserva en la edición
- En la edición el tipo empieza en "Sin cambiar" y no se envía: `GET /platforms` no expone `integration_type` (FNC-063); el superadmin solo lo envía si elige uno
- Bloqueo por `active_grants > 0` en la interfaz solo cuando el dato llega; hasta FNC-063 lo protege el `409 plataforma_con_accesos`
- Error por campo con `ErrorNote` dentro del `Field` (sin tocar `form.tsx`, compartido y en edición paralela por DIS-016)
- Enlace no https en la tabla y la tarjeta = "Sin enlace" (misma insignia existente), sin mostrar la URL
- Mensajes de `403`/`409` del contrato en el cliente; si llega otro `code`, el mensaje del backend
- `PlatformAdmin` envuelto en `RequireRole any_admin` dentro del componente (no se tocó `app/`)
- Retiro de la asignación directa de usuarios: no aplica; la pantalla ya no la tiene (FNC-065 sigue en Propuesta)

## Verificación
| Comando (en `frontend/`) | Resultado real |
|---|---|
| `npm ci` | código 0 |
| `npm test` | 12 archivos; 289 passed, 88 expected fail; código 0 |
| `npm run lint` | sin avisos ni errores; código 0 |
| `npx eslint tests vitest.config.ts` | código 0 |
| `npm run typecheck` | código 0 |
| `npm run build` | código 0 (`/admin/platforms` 6.29 kB) |
| Regresión SEG-24 con `platform-card.tsx` de `develop` | 3 pruebas fallan (`javascript:`, `http:`, `data:`); con el cambio pasan |
| `grep` de `style=`, `<style`, `.style.`, hex, `rgb(`, paleta fija, IP en lo nuevo y en el diff | sin coincidencias |

- Prueba de colores literales y de contraste: pasan sin cambiar topes (`platform-admin.tsx` conserva 4 hex y 5 de paleta existentes, DIS-012/DIS-002)
- Visual: `next dev` con backend simulado local y Chromium sin interfaz por CDP; tema claro y oscuro, 1280×900 y 390×844: lista, modal con errores por campo y aviso con `warnings`. Se vio correcto y sin desbordes (la tabla desplaza en horizontal en móvil, como antes)
- No verificado: Catálogo y Favoritos en navegador (solo pruebas de componente); lectores de pantalla reales; contra el backend real
- Contraste heredado (no nuevo): `text-error` de `ErrorNote` y `nx-badge-warning` en temas oscuros (DIS-001/DIS-002)

## Revisiones
- Pendientes: tester, revisor, auditor-accesibilidad y auditor-seguridad (SEG-24); no se lanzaron por instrucción del orquestador

## Commits / PR
- Commit local `[DIS-017]` en `dis/DIS-017-pantalla-plataformas`; sin push ni PR

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-024, FNC-025, FNC-069, FNC-046
- Cierra → SEG-24 del frontend (FNC-017)
- Relacionada → FNC-063 (exponer tipo, DN y `active_grants` en `GET /platforms` para la edición)
- Contrato → docs/contratos/plataformas-integracion.md

## Riesgos y reversión
- Hasta FNC-063 la edición no conoce el tipo ni los accesos vigentes (ver decisiones)
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-19 | Aprobada (modo autónomo, vía orquestador); implementada en `dis/DIS-017-pantalla-plataformas`; cierra SEG-24 del frontend. En revisión |
