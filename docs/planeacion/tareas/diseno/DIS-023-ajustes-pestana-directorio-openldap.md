# DIS-023 — Ajustes: pestaña Directorio para OpenLDAP

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | configuracion-directorio |
| **Prioridad** | Media |
| **Estatus** | En revisión |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Commit local, sin push |
| **Rama** | `dis/DIS-023-ajustes-directorio` (worktree `pokemon-wt-d023`) |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- La pestaña Directorio de `settings-panel.tsx` (745 líneas) pide contraseña de bind, usa `sAMAccountName` por defecto y mapeos de rol que dejan de existir (FNC-042, FNC-043)
- Requerimientos: F-ACC-01, RNF-03

## Objetivo
- Pestaña que muestra la configuración efectiva y su origen, permite editar solo lo no sensible que permita ADR-004 y prueba la conexión; sin campos de contraseña ni mapeos de rol

## Alcance
- **Incluye:**
  - Pestaña extraída a `components/settings/directory-tab.tsx`; `settings-panel.tsx` solo la importa
  - Estados de conexión y origen de cada valor
- **No incluye:**
  - Las demás pestañas y la división completa de `settings-panel.tsx` (DIS-011)

## Archivos previstos
- `frontend/src/components/settings/directory-tab.tsx`
- `frontend/src/components/settings-panel.tsx` (reemplazo de la pestaña por la importación)

## Archivos tocados
| Archivo | Cambio |
|---|---|
| `frontend/src/components/settings/directory-tab.tsx` | Nuevo: pestaña solo lectura, estados y prueba de conexión |
| `frontend/src/components/settings/directory-catalog.ts` | Nuevo: campos, etiquetas, origen, estados y textos |
| `frontend/src/components/settings/directory-errors.ts` | Nuevo: mensajes propios de carga y prueba |
| `frontend/src/components/settings-panel.tsx` | Quita `LdapTab` (−140 líneas), importa `DirectoryTab`; pestañas con teclado, `tabpanel` y 48 px (DIS-034) |
| `frontend/src/lib/api.ts`, `lib/types.ts` | Retira `authConfig`/`saveAuthConfig`/`testAuthConfig` y `AuthConfig` (forma heredada) |
| `frontend/src/lib/access/directory.ts` | Solo el comentario de cabecera |
| `frontend/tests/components/settings/directory-tab.test.tsx` | Nuevo: 10 pruebas |
| `frontend/tests/accesibilidad/pares-contraste.ts` | Pares nuevos (aviso de origen e insignias de estado) |
| Docs | `docs/frontend/README.md`, `docs/estandarizacion/03-reutilizacion.md`, `CHANGELOG.md`, tablero, log, fichas DIS-023 y DIS-034 |

## Reutilización
- `Field`, `TextInput`, `Button`, `ErrorNote`
- Usados: `Card`, `Badge`, `Spinner`, `EmptyNote`, `ErrorNote`, `Button`, `Dato` (DIS-022), `useAsync`, `directoryApi` (FNC-069), `destinoPorTecla` (DIS-014); avisos `status`/`alert` con foco y `aria-disabled` de DIS-021/022; recuadro de aviso `border-primary/40 bg-primary/10` de la pestaña Correo
- No se usan `Field`/`TextInput`/`Select`: la API no expone ningún campo editable (`editable: false`, `PUT` sin campos)

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `settings-panel.tsx` (`SettingsPanel`) | Pantalla | `/settings` (todas las pestañas): pestañas con teclado, `tabpanel` con foco y 48 px de alto | Pendiente (visual) |
| `api.authConfig`/`saveAuthConfig`/`testAuthConfig`, tipo `AuthConfig` (TS) | Cliente API | Solo los usaba `LdapTab` (retirada); sin otros usos en `frontend/` | Sí (grep, typecheck) |
| `pares-contraste.ts` | Prueba | `contraste.test.ts` | Sí (vitest) |

Salida de `impacto.py` (contra `develop`). Falsos positivos por coincidencia de nombre: `AuthConfig` del backend es el modelo Python (no se tocó `app/`); `save`, `alPulsar`, `tabId`, `panelId` son funciones locales homónimas; `tinte` no cambió.

**⚠ Impacto en elementos compartidos** (comparado contra `develop`): este cambio toca 7 elemento(s) usados en otras secciones: app, app/modules, frontend/src, frontend/tests, tests, tests/audit, tests/directory, utils. Valida cada una antes de integrar.

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `AuthConfig` | tipo | `frontend/src/lib/types.ts` | `app/__init__.py`, `app/modules/api/admin.py`, `app/modules/auth/models.py`, `tests/audit/test_registro_ampliado.py`, `tests/directorio_falso.py`, `tests/directory/test_api.py`, `tests/test_login_directorio.py`, `tests/test_respaldo.py` (+3) | app, app/modules, tests, tests/audit, tests/directory, utils | ☐ |
| `SettingsPanel` | función | `frontend/src/components/settings-panel.tsx` | `frontend/src/app/settings/page.tsx` | frontend/src | ☐ |
| `alPulsar` | función | `frontend/src/components/settings-panel.tsx` | `frontend/src/components/access/my-requests-view.tsx` | frontend/src | ☐ |
| `panelId` | función/componente | `frontend/src/components/settings-panel.tsx` | `frontend/src/components/access/my-requests-view.tsx`, `frontend/src/components/mobile-menu.tsx`, `frontend/tests/components/menu-movil.test.tsx` | frontend/src, frontend/tests | ☐ |
| `save` | función | `frontend/src/components/settings-panel.tsx` | `app/modules/auth/routes.py`, `app/modules/notifications/routes.py`, `app/modules/settings/routes.py`, `frontend/src/components/areas/area-form.tsx`, `frontend/src/components/connectors/connector-form.tsx`, `frontend/src/components/platform-admin.tsx`, `frontend/src/components/platforms/platform-form.tsx`, `frontend/src/components/users-list.tsx` (+6) | app/modules, frontend/src, frontend/tests, tests | ☐ |
| `tabId` | función/componente | `frontend/src/components/settings-panel.tsx` | `frontend/src/components/access/my-requests-view.tsx` | frontend/src | ☐ |
| `tinte` | función/componente | `frontend/tests/accesibilidad/pares-contraste.ts` | `frontend/src/styles/tokens.css` | frontend/src | ☐ |

## Criterios de aceptación
- [ ] Las demás pestañas no cambian (verificación visual) — no verificado visualmente; solo cambia el contenedor (`tabpanel`) y el alto de las pestañas (DIS-034)
- [x] Sin campos de contraseña ni mapeos de rol (prueba Vitest)
- [x] Configuración efectiva con su origen (prueba Vitest)
- [x] Estados de carga, sin configurar, inválida, error y sin permiso (prueba Vitest)
- [x] Prueba de conexión con texto propio (`status`/`alert`) y foco (prueba Vitest)
- [x] Solo el superadmin ve la pestaña (prueba Vitest)
- [ ] Criterios comunes de diseño (FNC-037): temas y responsive no verificados visualmente

## Decisiones (decisión del orquestador, pendiente de validar en la prueba de concepto)
| # | Decisión | Motivo |
|---|---|---|
| 1 | Pestaña solo lectura, sin formulario | La API no permite editar nada (`editable: false`; `PUT` con cualquier campo → `400`) |
| 2 | No se llama `PUT /auth-config` (`directoryApi.reload`); "Reintentar" solo ante error de carga | El `PUT {}` no cambia nada y la configuración cambia solo al reiniciar el servicio |
| 3 | "Probar conexión" con `aria-disabled` si el directorio no está activo o es inválido | El servidor respondería `409`; se explica con una pista ligada por `aria-describedby` |
| 4 | Se muestran "Servidor y puerto" y "Cifrado" (deducidos de `LDAP_URL`) con el origen de `LDAP_URL` | No tienen variable propia en `origins` |
| 5 | La contraseña de bind se muestra como fila explicativa (fuente `.env` en dev, Vaultwarden con `LDAP_BIND_PASSWORD_REF` fuera de dev), sin valor ni campo | El portal nunca la pide ni la muestra (SEC-LDAP-11, FNC-068) |
| 6 | Mensajes propios para `403`, `409`, `503`, `400` y genéricos; nunca el `message` del servidor | Patrón de DIS-022 (SEG-21) |
| 7 | Se retira el cliente heredado de `/auth-config` de `lib/api.ts` y `AuthConfig` | Enviaba `ldap_pass` y mapeos que el servidor rechaza; el comentario de `directory.ts` lo preveía en DIS-023 |
| 8 | DIS-034 se cierra aquí: `destinoPorTecla` importado en `settings-panel.tsx` sin crear componente de pestañas común | Costo bajo (sin refactor de DIS-011); el componente común queda para DIS-011 |
| 9 | `Dato` con el origen en `text-label` debajo del valor | Reutiliza el par etiqueta/valor de DIS-022; el dueño hará el diseño visual final |

## Verificación
| Comando (en `frontend/`) | Resultado |
|---|---|
| `npm run typecheck` | Salida 0 |
| `npm run lint` | Salida 0, sin avisos |
| `npx vitest run` | Salida 0: 29 archivos, 1026 passed, 25 expected fail (las 25 conocidas, sin aumento) |
| `npm run build` | Salida 0; `/settings` 6,08 kB |
| `grep` de `style=`, `<style`, `.style.`, `#hex`, `rgb(`, IPs en los archivos nuevos y el diff | Sin coincidencias |

- Pares de contraste nuevos: `body-text/primary-10-sobre-body-bg` y `badge-directorio-{activo,sin_configurar,invalido}` en los 7 temas; todos pasan.
- **No verificado:** inspección visual en tema claro y oscuro, móvil y escritorio (no se levantó la app: `/settings` necesita sesión del backend). Pendiente de `auditor-accesibilidad`, `revisor` y `tester` (no lanzados por indicación del orquestador).


## Impacto cruzado
- Cierra también → DIS-034 (pestañas de Ajustes con flechas)
- Origen ← FNC-037
- Depende de → FNC-036, FNC-024, FNC-025, FNC-069, FNC-043
- Contrato → docs/contratos/usuarios-directorio.md

## Riesgos y reversión
- Puede avanzar con los datos simulados de FNC-069; se integra después del backend.
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-18 | FNC-043 (En revisión) cambia la API: `GET /auth-config` → `{active, source, editable: false, config, origins, variables, error}` (sin `ldap_*` ni clave); `PUT` y `POST /auth-config/test` sin cuerpo (cualquier campo → `400 campo_no_permitido`); `409 directorio_no_configurado` y `503 directorio_no_disponible`; búsqueda con `q` 2–64. Contrato: [usuarios-directorio.md → Configuración del directorio](../../../contratos/usuarios-directorio.md#configuración-del-directorio-fnc-043-consumidor-dis-023). La pestaña actual no funciona hasta esta tarea |
| 2026-10-26 | Aprobada y En curso (modo autónomo); rama `dis/DIS-023-ajustes-directorio` desde `develop` (1ed3508) |
| 2026-10-26 | Implementada: pestaña solo lectura en `components/settings/`, prueba de conexión, cliente heredado retirado, DIS-034 incluida; typecheck, lint, vitest y build en 0. En revisión |
