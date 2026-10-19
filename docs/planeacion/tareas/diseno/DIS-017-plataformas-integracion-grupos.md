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
| `frontend/src/components/platforms/platform-save-notice.tsx` | Nuevo: aviso de guardado con `warnings` (enfocable; la región `status` la monta la pantalla) |
| `frontend/src/components/platforms/platform-form.tsx` | Nuevo (revisión): `PlatformForm` extraído de `platform-admin.tsx`; en el alta los colores no se envían hasta elegirlos (el servidor aplica `POR_DEFECTO_ALTA`, los mismos valores), sin los 4 hex literales |
| `frontend/src/components/platforms/platform-payload.ts` | Nuevo (revisión): `validate` y `buildPayload` |
| `frontend/src/components/platforms/field-notes.tsx` | Nuevo (revisión): `FieldErrorNote`, `FieldHint`, `describedBy`, `focusFirstError` (patrón de `areas/area-form.tsx`) |
| `frontend/src/lib/enlace-seguro.ts` | Nuevo: `enlaceSeguro` (solo `https://`, SEG-24) |
| `frontend/src/components/platform-admin.tsx` | Validación previa, cuerpo por rol, errores por campo, aviso, error al eliminar, `RequireRole any_admin`, enlaces solo https en la tabla |
| `frontend/src/components/platform-card.tsx` | `href` solo con `enlaceSeguro` |
| `frontend/tests/components/platform-admin.test.tsx`, `platform-card.test.tsx` | Nuevas pruebas |

## Reutilización
- `Field`, `TextInput`, `Select`, `Button`, `Modal` de `form.tsx`; `Card`, `Badge`, `ErrorNote`, `EmptyNote` de `ui.tsx`; `RequireRole`; `api.createPlatform`/`updatePlatform` y `ApiError` (`code`, `fields`) de FNC-069
- Sin tokens nuevos; error y pista por campo fuera del `Field`, ligados con `aria-describedby` (mismo patrón que DIS-016)
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

Segunda ejecución (correcciones de revisión), filas nuevas:

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `TopeLiterales` | tipo | `frontend/tests/accesibilidad/colores-literales.excepciones.ts` | `frontend/tests/accesibilidad/colores-literales.test.ts` | frontend/tests | ☑ real: tope de `platform-admin.tsx` hex 4 → 0 (literales retirados; el control pre-commit no deja moverlos a un archivo nuevo) |
| `dialogo` | función | `frontend/tests/components/platform-admin.test.tsx` | `frontend/tests/components/users-list.test.tsx` | frontend/tests | ☑ homónimo (función local de cada prueba) |
| `open` | función | `frontend/src/components/platform-admin.tsx` | `app/modules/api/admin.py`, `app/modules/directory/ldap_client.py`, `frontend/src/components/settings-panel.tsx`, `frontend/src/styles/components.css`, `scripts/lineamientos/comun.py`, `tests/areas/test_alta_y_baja_por_admin.py`, `tests/test_alcance_por_area.py`, `tests/test_auditoria_crud.py` (+6) | app/modules, frontend/src, scripts/lineamientos, tests, tests/areas, tests/users, utils, utils/migrations | ☑ homónimo (función local) |
| `respuesta` | función | `frontend/tests/components/platform-admin.test.tsx` | `app/modules/api/auth.py` y otros (+30) | app/modules, frontend, tests | ☑ homónimo (función local de la prueba) |

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
- Error y pista por campo con `FieldErrorNote`/`FieldHint` fuera del `Field` (sin tocar `form.tsx`); foco al primer campo con error; al cerrar un diálogo vuelve al disparador (o al título si ya no existe); tras guardar, al aviso
- Error al eliminar: mensaje fijo por estado (403/404/409), sin el texto del servidor
- Colores en el alta: sin valor hasta elegirlos (control de color vacío con pista); el servidor aplica sus colores por omisión, como en DIS-016
- Enlace no https en la tabla y la tarjeta = "Sin enlace" (misma insignia existente), sin mostrar la URL
- Mensajes de `403`/`409` del contrato en el cliente; si llega otro `code`, el mensaje del backend
- `PlatformAdmin` envuelto en `RequireRole any_admin` dentro del componente (no se tocó `app/`)
- Retiro de la asignación directa de usuarios: no aplica; la pantalla ya no la tiene (FNC-065 sigue en Propuesta)

## Verificación
| Comando (en `frontend/`) | Resultado real |
|---|---|
| `npm ci` | código 0 |
| `npm test` | 12 archivos; 289 passed, 88 expected fail; código 0 |
| `npm test` (correcciones de revisión) | 12 archivos; 300 passed, 88 expected fail; código 0. Las 8 pruebas nuevas (aria-describedby, región status, foco, aria-label, errores de baja, href normalizado) fallaron antes del cambio |
| `npm run lint`, `npx eslint tests vitest.config.ts`, `npm run typecheck`, `npm run build` (revisión) | código 0 (`/admin/platforms` 7.03 kB) |
| `npm run lint` | sin avisos ni errores; código 0 |
| `npx eslint tests vitest.config.ts` | código 0 |
| `npm run typecheck` | código 0 |
| `npm run build` | código 0 (`/admin/platforms` 6.29 kB) |
| Regresión SEG-24 con `platform-card.tsx` de `develop` | 3 pruebas fallan (`javascript:`, `http:`, `data:`); con el cambio pasan |
| `grep` de `style=`, `<style`, `.style.`, hex, `rgb(`, paleta fija, IP en lo nuevo y en el diff | sin coincidencias |

- Prueba de colores literales y de contraste: pasan; en la revisión el tope hex de `platform-admin.tsx` baja de 4 a 0 (quedan 5 de paleta, DIS-002/DIS-012)
- Accesibilidad (auditor-accesibilidad, medido en claro y oscuro): **Con observaciones**; sin colores literales ni estilos inline nuevos. Pendientes: errores por campo sin `aria-describedby` (`form.tsx:23`, `platform-admin.tsx`, `platform-integration-fields.tsx:107,136,152`); pista `text-label/60` con 3.35:1 claro y 3.31:1 oscuro (`form.tsx:29`); `role="status"` montado junto con su contenido (`platform-save-notice.tsx:27`); sin foco devuelto al cerrar el modal; "Editar"/"Eliminar" sin nombre de plataforma (`platform-admin.tsx:420-428`).
- Visual: `next dev` con backend simulado local y Chromium sin interfaz por CDP; tema claro y oscuro, 1280×900 y 390×844: lista, modal con errores por campo y aviso con `warnings`. Se vio correcto y sin desbordes (la tabla desplaza en horizontal en móvil, como antes)
- No verificado: Catálogo y Favoritos en navegador (solo pruebas de componente); lectores de pantalla reales; contra el backend real
- Contraste heredado (no nuevo): `text-error` de `ErrorNote` y `nx-badge-warning` en temas oscuros (DIS-001/DIS-002)

## Revisiones
- auditor-seguridad: **Aprobado** con 2 Baja: `href` normalizado (corregido); IP literales e IDN en el cliente → Propuesta en la bitácora de FNC-017
- auditor-accesibilidad: **Con observaciones**; corregidas las de la tarea: `aria-describedby` en errores, pistas y notas de deshabilitado; región `status` siempre montada; foco (primer error, disparador, aviso); `aria-label` con el nombre en Editar/Eliminar. Heredadas anotadas en bitácoras: `text-label/60` → DIS-005; `text-error`/`text-primary`/badge warning/amber/red → DIS-001/DIS-002; botones de 24 px → DIS-008
- revisor: **Requiere cambios**, corregidos: `validate`/`buildPayload` a `platform-payload.ts` y `PlatformForm` a `platform-form.tsx` (`platform-admin.tsx` 258 líneas); un solo `FieldErrorNote` (`field-notes.tsx`); error de baja con mensaje fijo por código
- tester: pendiente

## Commits / PR
- `57d05a0` [DIS-017] implementación; segundo commit [DIS-017] con las correcciones de revisión; sin push ni PR

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
| 2026-10-19 | Revisión: seguridad Aprobado, accesibilidad Con observaciones, revisor Requiere cambios; corregido en un segundo commit. Sigue En revisión |
