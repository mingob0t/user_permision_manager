# DIS-031 — `Modal`: atrapar el foco con Tab y devolverlo al cerrar

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | componentes |
| **Prioridad** | Media |
| **Estatus** | En revisión |
| **Aprobada** | 2026-10-26 (modo autónomo; junto con DIS-038 y DIS-043) |
| **Rama** | `dis/DIS-031-038-modal` (desde `develop`, d642e1f) |
| **Creada** | 2026-10-20 |

## Contexto
- `Modal` (`form.tsx`) enfoca el panel al abrir y cierra con Escape, pero Tab sale del diálogo y el foco no vuelve al disparador
- DIS-013 devuelve el foco desde la pantalla; las demás pantallas con modal (áreas, usuarios, plataformas, notificaciones) no

## Objetivo
- Ciclo de foco dentro del diálogo y foco de regreso al elemento que lo abrió, en el componente compartido
- Foco inicial en el primer campo del diálogo (hoy va al panel) (auditor-accesibilidad, DIS-013)
- `Modal` acepta `describedBy` (`aria-describedby` del `role="dialog"`), para ligar el texto que explica la acción, p. ej. la confirmación de aprobar (auditor-accesibilidad, DIS-015)
- `describedBy` también para los diálogos de rol de Usuarios (`AdminAreasDialog`, `RemoveAdminDialog`): ligar el texto del efecto (áreas, permisos, accesos automáticos) (auditor-accesibilidad, DIS-019)
- El efecto de `Modal` depende de `onClose` y re-enfoca el panel si cambia: enfocar solo al montar (DIS-019 lo evita con `useCallback` en `users-list.tsx`)
- El ✕ del `Modal` mide 36 px: llevarlo a 48 px (auditoría de DIS-020)
- Reutilizar la trampa local de `MobileMenu` (DIS-025) en un hook común, sin duplicarla
- `describedBy` en los diálogos que ya explican la acción: aprobar, rechazar, revocar, rol de admin, borrar conector y reintentar ejecución

## Alcance
- **Incluye:** `useFocusTrap` (nuevo, `lib/`), `Modal` y `ConfirmDialog` (`form.tsx`), `MobileMenu` (usa el hook), los 6 diálogos con `describedBy`, pruebas.
- **No incluye:** velo y bloqueo de desplazamiento (DIS-038, misma rama), botón de peligro en diálogos destructivos (DIS-043, misma rama), rediseño visual (lo hace el dueño), backend.

## Implementación
| Archivo | Cambio |
|---|---|
| `frontend/src/lib/use-focus-trap.ts` | Nuevo: `useFocusTrap(ref, { activo, focoInicial, alEscape, devolverA })`, `ENFOCABLES`, `CAMPOS`, `enfocables()`; pila de trampas (solo atiende la de arriba) |
| `frontend/src/components/form.tsx` | `Modal`: trampa con el hook, foco inicial en el primer campo del cuerpo o en el panel, `describedBy` → `aria-describedby`, ✕ `min-w-12 min-h-12`; quita el `useEffect` con `[onClose]`. `ConfirmDialog` liga su mensaje |
| `frontend/src/components/mobile-menu.tsx` | Trampa local retirada; usa `useFocusTrap` (`devolverA` = botón "Menú", foco inicial al primer enlace) |
| `access/approve-dialog.tsx`, `access/reject-dialog.tsx`, `users/revoke-access-dialog.tsx`, `users/admin-role-dialog.tsx` (los dos), `connectors/connector-delete-dialog.tsx`, `connectors/job-retry-dialog.tsx` | `describedBy` con los ids de los párrafos que explican el efecto (`useId` o constante del archivo) |
| `frontend/tests/components/modal.test.tsx` | Nuevo (16): foco inicial, panel sin campos, Tab/Mayús+Tab, foco fuera, Escape y ✕ devuelven el foco, no lo pisa si la pantalla ya lo movió, no roba el foco al re-renderizar, pila, `describedBy`, `ConfirmDialog`, velo, 48 px, clase de scroll |
| `frontend/tests/components/dialogos-descripcion.test.tsx` | Nuevo (7): descripción de cada diálogo y variante del botón |

## Decisiones
Decisión del orquestador (pendiente de validar en la prueba de concepto), en todas:
| # | Decisión | Motivo |
|---|---|---|
| 1 | Hook en `src/lib/use-focus-trap.ts` | Mismo lugar que `use-async` y `use-polling`; lo usan dos componentes |
| 2 | Foco inicial: primer `input`/`select`/`textarea` del cuerpo (no el ✕ ni los botones del pie); sin campos, el panel | Lo pide la ficha; en confirmaciones el lector anuncia título y descripción desde el panel |
| 3 | Si el foco ya está dentro al abrir (`autoFocus`, p. ej. "Buscar en el directorio" de Usuarios), no se mueve | Respeta la decisión de la pantalla |
| 4 | El foco vuelve al elemento que lo tenía al montar el `Modal`, solo si nadie lo movió fuera (sigue en el diálogo o en `body`) | Las pantallas de DIS-013/015/018/022 ya mueven el foco al aviso o al filtro; no se pisan |
| 5 | `focoInicial` y `alEscape` se leen de referencias; el efecto depende solo de `activo` | El panel se enfoca solo al abrir aunque `onClose` cambie (auditoría de DIS-019) |
| 6 | Pila de trampas: con dos diálogos, solo el de arriba atiende Tab y Escape | Evita que Escape cierre los dos |
| 7 | `ConfirmDialog` también liga su mensaje con `describedBy` | Misma necesidad que los 6 diálogos, mismo archivo; sin cambio visual |
| 8 | Un solo commit de código para DIS-031, DIS-038 y DIS-043 | Los tres tocan las mismas líneas de `form.tsx`, `mobile-menu.tsx` y los diálogos; `git add -p` no está disponible. Documentación en commits `[DIS-038]` y `[DIS-043]` |

## Impacto en elementos compartidos
`Modal` y `ConfirmDialog` (`form.tsx`), `MobileMenu`. Pantallas que los usan, a validar:
| Elemento | Componente que lo monta | Pantalla |
|---|---|---|
| `Modal` | `RequestFormModal` (`access/request-form-modal.tsx`, desde `request-catalog.tsx`) | `/platforms` (Catálogo) |
| `Modal` | `ApproveDialog`, `RejectDialog` (desde `approvals-inbox.tsx`) | `/approvals` |
| `Modal` | `AreaForm`, `AreaAdminsPanel` (desde `areas-list.tsx`) | `/areas` |
| `Modal` | `PlatformForm` (`platforms/platform-form.tsx`, desde `platform-admin.tsx`) | `/admin/platforms` |
| `Modal` | Editar/Nuevo usuario y "Buscar en el directorio" (`users-list.tsx`), `DirectoryAccountForm`, `AdminAreasDialog`, `RemoveAdminDialog`, `RevokeAccessDialog` (desde `user-access-panel.tsx`) | `/users` |
| `Modal` | `AuditDetailModal` (desde `audit-history.tsx`) | `/audit`, `/audit/users/[id]`, `/audit/platforms/[id]` |
| `Modal` | `ConnectorDeleteDialog` (`connector-panel.tsx`), `JobDetailModal` y `JobRetryDialog` (`jobs-log.tsx`) | `/admin/connectors` |
| `ConfirmDialog` | `areas-list.tsx`, `areas/area-admins-panel.tsx`, `platform-admin.tsx`, `notifications-list.tsx`, `users-list.tsx` (2) | `/areas`, `/admin/platforms`, `/notifications`, `/users` |
| `MobileMenu` | `AppShell` | Todas las autenticadas, bajo `md` |

Cambio visible en todas: ✕ de 48 px (cabecera del diálogo algo más alta), velo por token (DIS-038), foco inicial en el primer campo.

Salida de `impacto.py` (contra `develop`): ver *Reporte de impacto* abajo.

## Verificación
| Comando (en `frontend/`) | Resultado |
|---|---|
| `npm run typecheck` | salida 0 |
| `npm run lint` | salida 0, sin avisos |
| `npx vitest run` | salida 0: 32 archivos, 1194 pruebas pasan; fallas de contraste conocidas: 0 |
| `npx next build` | salida 0; CSS generado con `.bg-overlay` y `html.scroll-bloqueado` |
| `modal.test.tsx` contra el `Modal` anterior | 13 de 16 fallan (incluida "no roba el foco al re-renderizar"): las pruebas detectan la regresión |
| `grep` de `style=`, `<style`, `.style.`, `style={{`, `#hex`, `rgb(` numérico e IPs en lo agregado | sin coincidencias |

No verificado: navegador real (temas claro y oscuro, móvil y escritorio, lector de pantalla). No se levantó la app en esta sesión. Sin auditores (por instrucción del orquestador); revisor y tester quedan para el orquestador.

## Reporte de impacto
**⚠ Impacto en elementos compartidos** (comparado contra `develop`): este cambio toca 17 elemento(s) usados en otras secciones: app/modules, frontend/src, frontend/tests, tests, tests/access_requests, tests/connectors. Valida cada una antes de integrar.

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `--color-panel-fill` | token CSS | `frontend/src/styles/tokens.css` | `frontend/src/styles/components.css`, `frontend/tests/accesibilidad/pares-contraste.ts` | frontend/src, frontend/tests | ☐ |
| `AdminAreasDialog` | función | `frontend/src/components/users/admin-role-dialog.tsx` | `frontend/src/components/users-list.tsx`, `frontend/tests/components/users/admin-role-dialog.test.tsx` | frontend/src, frontend/tests | ☐ |
| `ApproveDialog` | función | `frontend/src/components/access/approve-dialog.tsx` | `frontend/src/components/access/approvals-inbox.tsx` | frontend/src | ☐ |
| `Button` | función | `frontend/src/components/form.tsx` | `frontend/src/components/access/approvals-inbox.tsx`, `frontend/src/components/access/inventory-filters.tsx`, `frontend/src/components/access/inventory.tsx`, `frontend/src/components/access/list-pager.tsx`, `frontend/src/components/access/my-access.tsx`, `frontend/src/components/access/my-requests.tsx`, `frontend/src/components/access/request-catalog-card.tsx`, `frontend/src/components/access/request-catalog.tsx` (+24) | frontend/src | ☐ |
| `ConfirmDialog` | función | `frontend/src/components/form.tsx` | `frontend/src/components/areas-list.tsx`, `frontend/src/components/areas/area-admins-panel.tsx`, `frontend/src/components/notifications-list.tsx`, `frontend/src/components/platform-admin.tsx`, `frontend/src/components/users-list.tsx` | frontend/src | ☐ |
| `ConnectorDeleteDialog` | función | `frontend/src/components/connectors/connector-delete-dialog.tsx` | `frontend/src/components/connectors/connector-panel.tsx` | frontend/src | ☐ |
| `JobRetryDialog` | función | `frontend/src/components/connectors/job-retry-dialog.tsx` | `frontend/src/components/connectors/jobs-log.tsx` | frontend/src | ☐ |
| `MobileMenu` | función | `frontend/src/components/mobile-menu.tsx` | `frontend/src/components/app-shell.tsx` | frontend/src | ☐ |
| `Modal` | función | `frontend/src/components/form.tsx` | `frontend/src/components/access/approvals-inbox.tsx`, `frontend/src/components/access/request-catalog.tsx`, `frontend/src/components/access/request-form-modal.tsx`, `frontend/src/components/areas/area-admins-panel.tsx`, `frontend/src/components/areas/area-form.tsx`, `frontend/src/components/audit/audit-detail-modal.tsx`, `frontend/src/components/connectors/connector-panel.tsx`, `frontend/src/components/connectors/job-detail-modal.tsx` (+4) | frontend/src | ☐ |
| `RemoveAdminDialog` | función | `frontend/src/components/users/admin-role-dialog.tsx` | `frontend/src/components/users-list.tsx`, `frontend/tests/components/users/admin-role-dialog.test.tsx` | frontend/src, frontend/tests | ☐ |
| `TopeLiterales` | tipo | `frontend/tests/accesibilidad/colores-literales.excepciones.ts` | `frontend/tests/accesibilidad/colores-literales.test.ts` | frontend/tests | ☐ |
| `abrir` | función | `frontend/tests/components/menu-movil.test.tsx` | `app/modules/api/routes.py`, `app/modules/connectors/bd_motores.py`, `app/modules/connectors/http_transporte.py`, `app/modules/directory/errors.py`, `app/modules/notifications/services.py`, `app/modules/secretos/vaultwarden.py`, `frontend/src/app/platforms/page.tsx`, `frontend/src/components/access/approvals-inbox.tsx` (+10) | app/modules, frontend/src, frontend/tests, tests, tests/connectors | ☐ |
| `aprobar` | función | `frontend/src/components/access/approve-dialog.tsx` | `app/modules/access_requests/__init__.py`, `app/modules/access_requests/api.py`, `app/modules/access_requests/approvals.py`, `app/modules/home/services.py`, `frontend/src/components/access/approvals-inbox.tsx`, `frontend/src/components/access/request-errors.ts`, `frontend/src/components/home/role-summary.tsx`, `frontend/tests/components/access/approvals-inbox.test.tsx` (+4) | app/modules, frontend/src, frontend/tests, tests/access_requests | ☐ |
| `confirmar` | función | `frontend/src/components/connectors/connector-delete-dialog.tsx`, `frontend/src/components/connectors/job-retry-dialog.tsx` | `app/modules/access/services.py`, `app/modules/users/directory_accounts.py`, `app/modules/users/roles.py`, `frontend/src/components/login-form.tsx`, `frontend/tests/components/users/admin-role-dialog.test.tsx`, `tests/test_login_local.py` | app/modules, frontend/src, frontend/tests, tests | ☐ |
| `guardar` | función | `frontend/src/components/users/admin-role-dialog.tsx` | `app/modules/api/admin.py`, `app/modules/audit/sanitizar.py`, `app/modules/connectors/provider.py`, `app/modules/provisioning/providers.py`, `frontend/src/components/access/request-errors.ts`, `frontend/src/components/areas/area-admins-panel.tsx`, `frontend/src/components/areas/area-form.tsx`, `frontend/src/components/connectors/connector-catalog.ts` (+13) | app/modules, frontend/src, frontend/tests | ☐ |
| `quitar` | función | `frontend/src/components/users/admin-role-dialog.tsx` | `app/modules/audit/events.py`, `app/modules/audit/parametros.py`, `app/modules/directory/api.py`, `app/modules/provisioning/saneo.py`, `app/modules/secretos/cifrado.py`, `frontend/src/components/access/approvals-inbox.tsx`, `frontend/src/components/access/request-catalog.tsx`, `frontend/src/components/users-list.tsx` (+2) | app/modules, frontend/src, frontend/tests | ☐ |
| `submit` | función | `frontend/src/components/access/reject-dialog.tsx`, `frontend/src/components/users/revoke-access-dialog.tsx` | `frontend/src/components/access/inventory-filters.tsx`, `frontend/src/components/access/request-form-modal.tsx`, `frontend/src/components/audit/audit-filters.tsx`, `frontend/src/components/connectors/connector-form.tsx`, `frontend/src/components/login-form.tsx`, `frontend/src/components/users/directory-account-form.tsx` | frontend/src | ☐ |

Falsos positivos: `abrir`, `aprobar`, `confirmar`, `guardar`, `quitar`, `submit` son funciones locales con el mismo nombre que otras del proyecto; `--color-panel-fill` y `TopeLiterales` no cambiaron (aparecen por líneas vecinas).

## Impacto en elementos compartidos
| Elemento | Usado en |
|---|---|
| `Modal`, `ConfirmDialog` | `areas-list`, `users-list`, `platform-admin`, `notifications-list`, `settings-panel`, `access/request-form-modal` |

## Impacto cruzado
- Origen ← DIS-013

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-20 | DIS-015 (auditor-accesibilidad): agregar `describedBy` a `Modal` |
| 2026-10-21 | DIS-019 (auditor-accesibilidad): `describedBy` para los diálogos de rol y foco inicial solo al montar |
| 2026-10-26 | Aprobada en modo autónomo y En curso, junto con DIS-038 y DIS-043 (rama `dis/DIS-031-038-modal`) |
| 2026-10-26 | `useFocusTrap` común (Modal y menú móvil), foco inicial, devolución, `describedBy` en 6 diálogos y `ConfirmDialog`, ✕ de 48 px; 23 pruebas nuevas; typecheck, lint, vitest y build en 0. En revisión |
