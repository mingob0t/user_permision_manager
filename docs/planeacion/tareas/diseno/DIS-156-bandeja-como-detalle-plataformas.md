# DIS-156 — Historial de solicitudes con filtros, como el detalle Plataformas > área

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Fase** | 8 |
| **Estatus** | Hecha |
| **Creada / Aprobada / Finalizada** | 2026-11-27 (pedido directo del dueño; ampliada el mismo día a historial con filtros) |
| **Depende de** | FNC-218 (backend: `status=todas` y `q` en `GET /access-requests/inbox`, contrato `solicitudes.md` 1.5) |

## Cambios
- `access/approvals-inbox.tsx`: «Ver todo» pasa a ser el historial: `DataTable` de Plataformas (cabecera con degradado, zebra, filas fantasma a 8, pie «N de N registros», `CapsulePager`), 8 por página, esqueleto con forma de tabla, vacío con «Limpiar búsqueda», error con Reintentar. Filtros Estado (Todas, Pendientes, Aprobadas, Rechazadas; `pendiente` por defecto), Área > Plataforma en cascada (`api.platforms({areaId})`; cambiar el área limpia la plataforma) y búsqueda `q` recortada y con retraso de 300 ms. Los filtros se reflejan en la URL (`status`, `area_id`, `platform_id`, `q`) con `history.replaceState`.
- `access/approvals-inbox-toolbar.tsx` (nuevo): tarjeta de herramientas con Volver («Resumen», `nx-btn-toolbar`), buscador `nx-buscador-toolbar` y selectores.
- `access/approvals-inbox-columns.tsx` (nuevo): columnas Solicitante, Plataforma, Nivel, Estado (insignias + fecha corta o «Decidida … por …»), Justificación (truncada con `title`), Motivo del rechazo (solo si hay rechazadas) y Acciones (iconos aprobar/rechazar con `aria-label`; solo en pendientes ajenas). `mostrarJustificacion` y `mostrarMotivo` son opciones de `columnasBandeja` y constantes `MOSTRAR_*` en la bandeja: punto de enganche para FNC-217.
- `access/approvals-view.tsx`: título «Historial de solicitudes»; ya no usa `backHref` (Volver está en la barra) ni `key` por estado; admite `status=todas`.
- `lib/access/types.ts` (`InboxStatus`, `InboxListParams` con `q`), `lib/access/requests.ts` (`inbox` los usa), `lib/use-debounced-value.ts` (nuevo).
- Se elimina la prop `estadoFijo` (único uso: `approvals-view.tsx`).

## Impacto en elementos compartidos
- `ApprovalsInbox`: usado por `approvals-view.tsx` (`/approvals?status=…`); `solicitudes-panel.tsx` importa `MENSAJE_PROPIA` y `avisoDecision` (se conservan); `approvals-resumen.tsx` y `home/solicitudes-pendientes.tsx` solo enlazan o citan. Vistas a validar: `/approvals?status=pendiente|aprobada|rechazada|todas` y «Ver todo» del Resumen.
- `requestsApi.inbox`: ahora acepta `status: 'todas'` y `q`; `solicitudes-panel.tsx` lo sigue llamando igual.
- `DataTable`, `nx-btn-toolbar`, `nx-buscador-toolbar`: solo se reutilizan, sin cambios.

## Propuestas
- Extraer la barra de herramientas (Volver + buscador) de `platform-admin.tsx` a un componente compartido; hoy está inline y `approvals-inbox-toolbar.tsx` la replica con las mismas clases.
- `DataTable` no tiene esqueleto con forma de tabla sin `encabezado`; la bandeja arma el suyo (tarjeta + cabecera + filas).

## Verificación
- tsc 0, eslint 0; vitest 3703/3703 (ver bitácora). Tema claro/oscuro y móvil: no verificados visualmente (sin captura); solo tokens y clases existentes, sin estilos inline ni colores literales (grep limpio).

## Bitácora
- Revisión (`revisor`) y accesibilidad (`auditor-accesibilidad`): corregido `min-w-[64rem]` (DIS-072), mock y pruebas de `approvals-resumen.test.tsx` (usa `ApprovalsView`), foco al buscador tras limpiar, motivo vacío con texto `sr-only`, «Limpiar búsqueda» del vacío vuelve a la página 1.
- FNC-217 pidió columnas condicionables: constantes `MOSTRAR_*` y opciones de `columnasBandeja`, sin implementar la configuración.
- `frontend/node_modules` del worktree es un symlink local: no se agrega a git.
- Pendiente de integración: FNC-218 (backend) define `status=todas`/`q`; versión de contrato por acordar (FNC-216 reclama la 1.5).
- Riesgo conocido: la bandeja lee la URL solo al montar; navegar a otro `/approvals?status=…` sin desmontarla conservaría el estado anterior (hoy ningún enlace lo hace).
- Verificación final: tsc 0, eslint 0, vitest completo 121 archivos / 3703 pruebas, salida 0.
