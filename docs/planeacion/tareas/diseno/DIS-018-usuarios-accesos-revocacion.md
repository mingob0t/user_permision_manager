# DIS-018 — Usuarios y accesos: accesos de un usuario y revocación

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
| **Estatus Git** | Rama local |
| **Rama** | `dis/DIS-018-accesos-usuario-revocacion` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- En `/users` (`users-list.tsx`, 581 líneas) se asignan plataformas a mano; no se ven accesos con nivel ni se puede revocar (F-ACC-02)
- Requerimientos: F-ACC-02, RF-03

## Objetivo
- Panel de accesos de un usuario (plataforma, nivel, origen, desde, quién aprobó, estado, última ejecución) con revocación confirmada (motivo según P7), dentro del alcance del admin

## Alcance
- **Incluye:**
  - Componente `user-access-panel.tsx` abierto desde la fila del usuario
  - Revocar con diálogo de confirmación
  - Estado del aprovisionamiento y error saneado
  - Usa `usePolling` de FNC-071 (ADR-006): refresco con el intervalo de la preferencia del usuario, en pausa con la pestaña oculta.
- **No incluye:**
  - Alta en directorio y elevación (DIS-019)
  - Dividir `users-list.tsx` (DIS-011)

## Archivos previstos
- `frontend/src/components/users/user-access-panel.tsx` (+ `revoke-access-dialog.tsx`, `revoke-errors.ts`)
- `frontend/src/components/users-list.tsx` (acción que abre el panel; retiro de la asignación directa si FNC-065 se aprueba)

## Reutilización
- `Modal`, `ConfirmDialog`, `access-status-badge.tsx`, `usePolling`

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `users-list.tsx` (`UsersList`): botón "Accesos" en cada tarjeta, estado `accessOf` y el panel encima de la lista | Pantalla | `/users` | Pendiente (dueño) |
| `access/my-access.tsx`: `FILTROS` pasa a `export` (sin cambio de valor) | Constante | `/requests` (Mis accesos) y el panel de DIS-018 | Pendiente (sin cambio visible) |
| `access/access-status-badge.tsx`: `ESTADOS` pasa a `export` (sin cambio de valor) | Constante | `/platforms` (catálogo), `/requests`, `/approvals`, panel de DIS-018 y `pares-contraste.ts` | Pendiente (sin cambio visible) |
| `tests/accesibilidad/pares-contraste.ts`: pares `badge-acceso-*` (6 × 7 temas) | Prueba | `contraste.test.ts` | Pasan (Vitest) |

Salida de `impacto.py` (2026-10-20). Salvo las cuatro filas de arriba, son coincidencias de nombre de funciones locales nuevas (`Fila`, `abrir`, `revocado`, `submit`, `message`, `pagina`…), no elementos compartidos:

**⚠ Impacto en elementos compartidos** (comparado contra `develop`): este cambio toca 12 elemento(s) usados en otras secciones: app, app/modules, frontend/src, frontend/tests, migrations/versions, scratch, tests, tests/access, tests/areas, tests/audit, tests/directory, tests/home, tests/platforms, tests/provisioning, tests/users. Valida cada una antes de integrar.

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `Fila` | función | `frontend/src/components/users/user-access-panel.tsx` | `frontend/src/components/access/approvals-inbox.tsx`, `frontend/src/components/access/my-requests.tsx`, `frontend/src/components/access/responsive-list.tsx`, `tests/directory/test_api.py` | frontend/src, tests/directory | ☐ |
| `Filtro` | tipo | `frontend/src/components/access/my-access.tsx`, `frontend/src/components/users/user-access-panel.tsx` | `app/modules/directory/ldap_client.py` | app/modules | ☐ |
| `Tono` | tipo | `frontend/src/components/access/access-status-badge.tsx` | `frontend/src/components/access/request-status-badge.tsx` | frontend/src | ☐ |
| `UsersList` | función | `frontend/src/components/users-list.tsx` | `frontend/src/app/users/page.tsx`, `frontend/tests/components/users-list.test.tsx` | frontend/src, frontend/tests | ☐ |
| `abrir` | función | `frontend/src/components/users/user-access-panel.tsx` | `app/modules/api/routes.py`, `app/modules/directory/errors.py`, `app/modules/notifications/services.py`, `frontend/src/app/platforms/page.tsx`, `frontend/src/components/access/approvals-inbox.tsx`, `frontend/src/components/access/request-catalog.tsx`, `frontend/src/components/platform-admin.tsx`, `frontend/src/components/platforms/platform-form.tsx` (+1) | app/modules, frontend/src, tests | ☐ |
| `cerrarAviso` | función | `frontend/src/components/users/user-access-panel.tsx` | `frontend/src/components/access/approvals-inbox.tsx`, `frontend/src/components/access/request-catalog.tsx` | frontend/src | ☐ |
| `message` | función/componente | `frontend/src/components/users/revoke-errors.ts` | `app/__init__.py`, `app/authz.py`, `app/modules/api/admin.py`, `app/modules/api/auth.py`, `app/modules/api/crud.py`, `app/modules/api/helpers.py`, `app/modules/api/routes.py`, `app/modules/areas/routes.py` (+73) | app, app/modules, frontend/src, frontend/tests, migrations/versions, scratch, tests, tests/areas, tests/directory, tests/platforms, tests/users | ☐ |
| `pagina` | función | `frontend/tests/components/users/user-access-panel.test.tsx` | `frontend/src/components/access/request-catalog.tsx`, `frontend/tests/components/access/approvals-inbox.test.tsx`, `frontend/tests/components/access/my-requests-view.test.tsx`, `tests/provisioning/test_api.py` | frontend/src, frontend/tests, tests/provisioning | ☐ |
| `remove` | función | `frontend/src/components/users-list.tsx` | `app/modules/api/routes.py`, `frontend/src/components/areas-list.tsx`, `frontend/src/components/platform-admin.tsx`, `frontend/src/lib/access/connectors.ts`, `frontend/tests/components/access/approvals-inbox.test.tsx`, `frontend/tests/lib/access/peticiones.test.ts`, `tests/audit/test_inmutabilidad.py`, `tests/conftest.py` (+1) | app/modules, frontend/src, frontend/tests, tests, tests/audit | ☐ |
| `revocado` | función | `frontend/src/components/users/user-access-panel.tsx` | `app/modules/access/services.py`, `app/modules/access/tipos.py`, `app/modules/provisioning/reintento.py`, `frontend/src/lib/access/types.ts`, `frontend/tests/components/access/my-requests-view.test.tsx`, `tests/access/test_api.py`, `tests/access/test_area_admin_sync.py`, `tests/access/test_inventario.py` (+2) | app/modules, frontend/src, frontend/tests, tests/access, tests/home | ☐ |
| `submit` | función | `frontend/src/components/users/revoke-access-dialog.tsx` | `frontend/src/components/access/reject-dialog.tsx`, `frontend/src/components/access/request-form-modal.tsx`, `frontend/src/components/login-form.tsx` | frontend/src | ☐ |
| `tinte` | función/componente | `frontend/tests/accesibilidad/pares-contraste.ts` | `frontend/src/styles/tokens.css` | frontend/src | ☐ |

## Criterios de aceptación
- [x] Un admin no ve botones de revocar en accesos de áreas ajenas (el backend no los lista; además no ve botón en automáticos ni en los de otro admin del área)
- [~] Criterios comunes de diseño (FNC-037): tokens y clases existentes, sin estilos inline; carga, vacío, error y sin permiso; teclado y foco probados en Vitest. Temas y responsive no verificados en navegador

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-024, FNC-025, FNC-069, FNC-071, FNC-058, DIS-013
- Contrato → docs/contratos/accesos.md

## Riesgos y reversión
- Puede avanzar con los datos simulados de FNC-069; se integra después del backend.
- Reversión: revertir la rama.

## Decisiones del orquestador (pendientes de validar en la prueba de concepto)
| # | Decisión | Motivo |
|---|---|---|
| 1 | El panel es una sección encima de la lista (como la purga), no un `Modal` | Revocar abre un diálogo: así no se anidan dos `Modal` (Escape cerraría ambos) |
| 2 | Botón "Revocar" de la fila secundario; en el diálogo, confirmar primario y "Cancelar" secundario | Mismo patrón que "Rechazar" (DIS-015); `danger` falla AA (DIS-004) |
| 3 | Solo se ofrece revocar en `activo`, no propio y, para el admin de área, ni `admin_de_area` ni de un admin del área (`managed_areas` del usuario incluye el área); en su lugar, texto con el motivo | Valor más seguro: evita 403/404/409 del contrato; el servidor sigue siendo la autoridad |
| 4 | Motivo opcional ≤ 500 con contador; se envía recortado y `null` si queda vacío | P7 y `limpiar_motivo` del backend |
| 5 | Refresco con `usePolling` siempre (no solo con estados transitorios) | Igual que Mis accesos; la pausa la agrega DIS-033 |
| 6 | Superadmin como usuario consultado: estado vacío explicado, sin llamada | No tiene registros (contrato) |
| 7 | "Estado del aprovisionamiento y error saneado": estado explicado y "Última ejecución: n.º N"; el detalle del error queda en la pantalla de ejecuciones | Ver el error exige `GET /provisioning/jobs/<id>` por fila; se evita N llamadas |
| 8 | Filtros de estado reutilizados de Mis accesos (`FILTROS` exportado) | No duplicar |
| 9 | Error 404/409 al revocar recarga la lista y lo dice | Mismo criterio que `describeDecisionError` |
| 10 | No se retira la asignación directa de plataformas de `UserForm` | Depende de FNC-065 y de DIS-011 (monolito) |

## Verificación
| Comando (en `frontend/`) | Resultado |
|---|---|
| `npm run typecheck` | salida 0 |
| `npm run lint` | salida 0, sin avisos |
| `npx vitest run` | salida 0: 18 archivos, 691 passed + 25 expected fail (las 25 fallas conocidas no aumentan) |
| `npx vitest run tests/components/users` | 31 passed (28 nuevas + 3 de `users-list.test.tsx`) |
| `grep` de `style=`, `<style`, `.style.`, `style={{`, `#hex`, `rgb(`, IPs en `components/users/` y el diff de `users-list.tsx` | sin coincidencias |

- No verificado en navegador (tema claro/oscuro, móvil/escritorio): la pantalla `/users` necesita el backend en marcha; solo se usan clases y tokens ya medidos (pares en `pares-contraste.ts`).
- Sin `tester`, `revisor` ni auditores (por instrucción del orquestador).

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-20 | Aprobada por el orquestador (modo autónomo) y En curso en el worktree `pokemon-wt-d023` |
| 2026-10-20 | Implementada: `users/user-access-panel.tsx`, `revoke-access-dialog.tsx`, `revoke-errors.ts`; botón "Accesos" en `users-list.tsx`; 28 pruebas y 42 pruebas de contraste (6 pares × 7 temas). En revisión |
