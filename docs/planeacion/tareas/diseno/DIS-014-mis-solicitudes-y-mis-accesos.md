# DIS-014 — Mis solicitudes y mis accesos

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | solicitudes |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Commit local, sin push |
| **Rama** | `dis/DIS-014-mis-solicitudes-accesos` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- No hay pantalla para que el usuario vea sus solicitudes ni sus accesos (F-SOL-02, pantallas "Mis solicitudes" e "Inicio")
- Requerimientos: F-SOL-02, F-ACC-02 (vista del usuario)

## Objetivo
- Pantalla `/requests` con dos pestañas: solicitudes (estado, nivel, fecha, motivo de rechazo) y accesos (plataforma, nivel, desde, estado del aprovisionamiento)

## Alcance
- **Incluye:**
  - Lista paginada de solicitudes con estado y motivo de rechazo visible
  - Lista de accesos con estado `en_proceso`/`activo`/`fallido` explicado en lenguaje claro
  - Usa `usePolling` de FNC-071 (ADR-006): refresco con el intervalo de la preferencia del usuario, en pausa con la pestaña oculta.
- **No incluye:**
  - Cancelar solicitudes (no pedido)
  - Revocar desde el usuario (no pedido)

## Archivos previstos
- `frontend/src/components/access/my-requests.tsx`
- `frontend/src/components/access/my-access.tsx`
- `frontend/src/app/requests/page.tsx`

## Archivos tocados
| Archivo | Cambio |
|---|---|
| `frontend/src/app/requests/page.tsx` | Monta `MyRequestsView`; sin `RequireRole` (ver decisión 1) |
| `frontend/src/components/access/my-requests-view.tsx` | Nuevo: pestañas "Mis solicitudes" / "Mis accesos" (`tablist`, `aria-controls`, `tabpanel`); superadmin con estado vacío explicado |
| `frontend/src/components/access/my-requests.tsx` | Nuevo: `GET /access-requests/mine` con `usePolling`, filtro por estado, paginación, motivo de rechazo, justificación, decisión y estado del acceso |
| `frontend/src/components/access/my-access.tsx` | Nuevo: `GET /me/access` (`vigente` por defecto) con `usePolling`, filtro, paginación, origen y estado explicado (`EXPLICACION_ESTADO`) |
| `frontend/src/components/access/responsive-list.tsx` | Nuevo, reutilizable: `ResponsiveList`, `ResponsiveRow`, `ETIQUETA_CELDA` (tabla en `md`, lista en móvil) |
| `frontend/src/components/access/list-pager.tsx` | Nuevo, reutilizable: `ListPager`, `totalPaginas` para `Paginated` |
| `frontend/src/components/access/request-status-badge.tsx` | Nuevo, reutilizable: `RequestStatusBadge`, `ESTADOS_SOLICITUD` |
| `frontend/src/components/access/fecha.ts` | Nuevo: `formatearFecha`, `LOCALE_FECHAS` (`es-MX`) |
| `frontend/src/components/access/request-errors.ts` | Agrega `describeListError` y `listLoadError` (conserva el estado HTTP para que `usePolling` se detenga con 401); lo existente sin cambios |
| `frontend/src/components/ui.tsx` | `EmptyNote`: `text-label/60` → `/85` (AA; ver decisión 5) |
| `frontend/tests/components/access/my-requests-view.test.tsx` | Nuevo: 16 pruebas |
| `frontend/tests/accesibilidad/pares-contraste.ts` | Par `empty-note/panel` (`alfaTexto` 0,85) |

## Decisiones del orquestador (pendientes de validar en la prueba de concepto)
| # | Decisión | Motivo |
|---|---|---|
| 1 | `/requests` ya no usa `RequireRole requester`: el superadmin que entra por URL ve "Como superadmin tienes acceso a todas las plataformas…" en vez de "sin permiso"; sin llamadas a la API | Pedido del orquestador; los contratos responden 200 vacío al superadmin, así que no se expone nada |
| 2 | Una sola entrada de menú ("Mis solicitudes", sin cambio en `app-shell.tsx`) con dos pestañas; el superadmin sigue sin verla | REQUERIMIENTOS (Pantallas por rol): Mis solicitudes para usuario y admin; "Mis accesos" no es pantalla propia (va en Inicio) |
| 3 | El refresco con `usePolling` corre siempre al intervalo del usuario, no solo "mientras haya `pendiente`/`en_proceso`" como dice la tabla Refresco de los contratos | `usePolling` no tiene opción para pausarse por datos; cambiarlo es otro elemento compartido. Propuesta DIS-033 |
| 4 | Mis accesos abre en `vigente` (por defecto del contrato) con filtro por cada estado; Mis solicitudes abre en "Todas" | Contratos |
| 5 | `EmptyNote` (compartido, 17 archivos) sube el texto de `/60` (2,88–3,35:1) a `/85` (5,16–6,63:1 en los 7 temas) | AA exigido; mismo criterio que el placeholder de DIS-013 |
| 6 | Fechas con `Intl` `es-MX`, estilo medio, zona del navegador | No había formateador de fechas en el frontend |
| 7 | Sin "cancelar solicitud" ni "revocar" | Fuera de alcance de la ficha |

## Reutilización
- `access-status-badge.tsx` (DIS-013)
- `Card`, `Badge`, estados de `ui.tsx`
- `usePolling`
- Reutilizados: `AccessStatusBadge` y `NIVELES` (DIS-013), `ApiError`, `Select`, `Button`, `Spinner`, `ErrorNote`, `EmptyNote`, `Card`, clases de las pestañas de `settings-panel.tsx`
- No existía componente de tabla ni de paginación (D-10 del catálogo): se crean `ResponsiveList` y `ListPager` en `components/access/` y se agregan al catálogo

## Impacto en elementos compartidos
Salida de `python3 ~/.claude/agentes/herramientas/impacto.py`:

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `EmptyNote` | función | `frontend/src/components/ui.tsx` | `app/admin/connectors/page.tsx`, `app/approvals/page.tsx`, `app/inventory/page.tsx`, `components/access/request-catalog.tsx`, `areas-list.tsx`, `areas/area-admins-panel.tsx`, `audit-log.tsx`, `favorites-list.tsx` (+5) | frontend/src | ☐ |
| `Page` | función | `frontend/src/app/requests/page.tsx` | las demás `page.tsx` | frontend/src | ☐ (falso positivo: mismo nombre por convención de Next.js) |
| `describeCatalogError` | función | `frontend/src/components/access/request-errors.ts` | `request-catalog.tsx` | frontend/src | ☐ (sin cambio: solo se agregaron funciones después) |
| `tinte` | función | `frontend/tests/accesibilidad/pares-contraste.ts` | `styles/tokens.css` | frontend/src | ☐ (sin cambio: se agregó un par) |

- Validar: el texto de todos los estados vacíos (`EmptyNote`) se ve más oscuro, en Catálogo, Favoritos, Notificaciones, Auditoría, Áreas, Usuarios, Plataformas y rutas reservadas

## Criterios de aceptación
- [x] Tabla responsive (en móvil se presenta como lista): mismo marcado, `dl` por fila; cabecera de columnas solo en `md`
- [x] Criterios comunes de diseño (FNC-037): tokens y clases existentes, sin estilos inline; estados de carga, vacío, error y sin permiso; textos en español. Temas y móvil **no verificados en navegador**

## Verificación
| Comando (en `frontend/`) | Resultado |
|---|---|
| `npm run typecheck` | salida 0 |
| `npm run lint` | salida 0, sin avisos |
| `npx eslint tests/components/access/my-requests-view.test.tsx` | salida 0 |
| `npx vitest run` | salida 0: 16 archivos, 530 passed + 25 expected fail (antes 507 + 25; las 25 conocidas sin cambio) |
| `npx vitest run tests/accesibilidad` con `alfaTexto` 0,6 | `empty-note/panel` falla en los temas (regresión comprobada); con 0,85 pasa |
| `grep` de `style=`, `<style`, `.style.`, `#hex`, `rgb(`, IPs en los archivos nuevos | sin coincidencias |

- **No verificado en navegador:** temas claro y oscuro, móvil y escritorio. Sin backend ni sesión en el worktree; contraste medido con la fórmula en los tokens, no en pantalla
- Sin revisor, tester ni auditores (por instrucción del orquestador)

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-024, FNC-025, FNC-069, FNC-070, FNC-071, FNC-056, FNC-058, DIS-013
- Contrato → docs/contratos/solicitudes.md 1.1 y accesos.md 1.1
- Genera → DIS-033 (Propuesta)

## Riesgos y reversión
- Puede avanzar con los datos simulados de FNC-069; se integra después del backend.
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-20 | Aprobada en modo autónomo por el orquestador; En curso en el worktree `pokemon-wt-d023` |
| 2026-10-20 | Implementada; En revisión. Propuesta DIS-033 |
