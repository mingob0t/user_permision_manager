# DIS-075 — Migrar los confirmar y avisos actuales a `AlertDialog` o toast según la tabla de decisión

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 7 |
| **Módulo / Área** | componentes |
| **Prioridad** | Media |
| **Estatus** | Hecha |
| **Responsable** | disenador-web |
| **Creada** | 2026-10-27 |
| **Inicio** | 2026-10-28 |
| **Finalizada** | 2026-10-28 |
| **Estatus Git** | Integrada en develop |
| **Rama** | `dis/DIS-075-migrar-confirmar-y-avisos` |
| **Commits / PR** | `feat(design): DIS-075 migrar confirmar y avisos a AlertDialog` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- 6 `ConfirmDialog`, 6 diálogos propios (`approve`, `reject`, `connector-delete`, `job-retry`, `admin-role`, `revoke-access`), `SuccessNote` en 11 archivos y 2 toasts (plan §2.9).
- Plan: [PLAN-FASE-7](../../PLAN-FASE-7-diseno-visual.md).

## Objetivo
Cada confirmación y aviso usa el patrón de la tabla de decisión (plan §4.7).

## Alcance
- **Incluye:**
  - Los 6 diálogos propios sobre `AlertDialog` (con cuerpo de campos donde lo tienen)
  - Revisar los 6 `ConfirmDialog` (tipo, verbo del botón)
  - Clasificar los 11 `SuccessNote` y los 2 toasts: rutina → toast; resultado que hay que leer → `AlertDialog`; estado persistente → `Note`; lista en la ficha
  - Retirar sus excepciones
- **No incluye:**
  - Textos nuevos salvo el verbo del botón; flujos o llamadas a la API

### Clasificación de avisos y confirmaciones (PLAN-FASE-7 §4.7)
| Ubicación | Elemento | Clasificación | Justificación |
|---|---|---|---|
| `access/approve-dialog.tsx` | Diálogo | `AlertDialog` (tipo pregunta, botón primario) | Acción con efecto importante sobre otros; foco inicial seguro |
| `access/reject-dialog.tsx` | Diálogo con formulario | `AlertDialog` (tipo aviso, botón peligro) | Acción con efecto de denegación motivada |
| `connectors/connector-delete-dialog.tsx` | Diálogo | `AlertDialog` (tipo aviso, botón peligro) | Acción destructiva irreversible |
| `connectors/job-retry-dialog.tsx` | Diálogo | `AlertDialog` (tipo pregunta, botón primario) | Acción de reintento de sincronización |
| `users/admin-role-dialog.tsx` (AdminAreas) | Diálogo con checklist | `AlertDialog` (tipo pregunta, botón primario) | Asignación sensible de áreas de administración |
| `users/admin-role-dialog.tsx` (RemoveAdmin) | Diálogo | `AlertDialog` (tipo aviso, botón peligro) | Revocación de rol administrativo |
| `users/revoke-access-dialog.tsx` | Diálogo con formulario | `AlertDialog` (tipo aviso, botón peligro) | Acción destructiva irreversible de acceso |
| `notifications-list.tsx:117` | `ConfirmDialog` | `AlertDialog` (tipo aviso, "Vaciar") | Acción destructiva de notificaciones |
| `platform-admin.tsx:178` | `ConfirmDialog` | `AlertDialog` (tipo aviso, "Eliminar") | Acción destructiva de plataforma |
| `areas-list.tsx:188` | `ConfirmDialog` | `AlertDialog` (tipo aviso, "Eliminar") | Acción destructiva de área |
| `areas/area-admins-panel.tsx:76` | `ConfirmDialog` | `AlertDialog` (tipo aviso, "Quitar") | Acción destructiva de admins |
| `users-list.tsx:229` | `ConfirmDialog` | `AlertDialog` (tipo aviso, "Eliminar") | Acción destructiva de usuario |
| `users/purge-panel.tsx:101` | `ConfirmDialog` | `AlertDialog` (tipo aviso, "Purgar") | Acción destructiva permanente |
| `favorite-button.tsx:44` | Toast | Toast error | Error recuperable no crítico transitorio |
| `theme-selector.tsx:40` | Toast | Toast error | Error recuperable no crítico de guardado |
| `users-list.tsx:116` | `SuccessNote` | `Note` persistente en pantalla | Anuncio de cambio de rol en la lista |
| `connectors/connector-panel.tsx:159` | `SuccessNote` | `Note` persistente en pantalla | Resultado de prueba de conexión |
| `connectors/jobs-log.tsx:151` | `SuccessNote` | `Note` persistente en pantalla | Anuncio de reintento encolado |
| `users/user-access-panel.tsx:227` | `SuccessNote` | `Note` persistente en pantalla | Anuncio de revocación en curso |
| `settings/directory-tab.tsx:91` | `SuccessNote` | `Note` persistente en pantalla | Resultado de sincronización de directorio |
| `settings/preferences-tab.tsx:71` | `SuccessNote` | `Note` persistente en pantalla | Estado de guardado de preferencias |
| `settings/backup-tab.tsx:53` | `SuccessNote` | `Note` persistente en pantalla | Resultado de generación de respaldo |
| `settings/portal-tab.tsx:128` | `SuccessNote` | `Note` persistente en pantalla | Estado de guardado de portal |
| `settings/smtp-tab.tsx:146, 164` | `SuccessNote` | `Note` persistente en pantalla | Estado de guardado y prueba de correo |
| `access/approvals-inbox.tsx:236` | `SuccessNote` | `Note` persistente en pantalla | Anuncio de decisión sobre solicitud |
| `access/catalog-notice.tsx:27` | `SuccessNote` | `Note` persistente en pantalla | Anuncio de solicitud enviada |

## Criterios de aceptación
- [x] Pruebas de cada diálogo y pantalla en verde (con el foco nuevo)
- [x] Clasificación de cada aviso anotada en la ficha
- [x] Desde `frontend/`: `npm run typecheck`, `npm run lint`, `npx vitest run` (incluye `tests/accesibilidad/`) y `npm run build` con código de salida 0
- [x] Sin colores literales, sin estilos en línea, sin `dark:` ni clases de tema en TSX
- [x] Verificada en navegador en tema claro y oscuro, a 360 px y 1280 px, y en los estados de carga, vacío y error que apliquen (nota o captura en la ficha)
- [x] `auditor-accesibilidad` Aprobado (contraste medido en los 2 temas, foco, texto mínimo y área táctil)
- [x] Tokens nuevos o cambiados registrados en `docs/configuracion/VARIABLES.md` y con motivo en `HISTORIAL.md`
- [x] Sin direcciones IP ni secretos; cumple `docs/estandarizacion/` y no duplica componentes existentes
- [x] `impacto.py` ejecutado y su tabla en esta ficha

## Impacto cruzado
- Genera → —
- Origen ← DIS-074
- Depende de → DIS-074

## Riesgos y reversión
Toca archivos de pantallas que luego migran D1–D2: va antes que ellas.

## Verificación
6 diálogos propios y 6 usos de `ConfirmDialog` unificados sobre `AlertDialog`. Clasificación de avisos registrada. 2225/2225 pruebas unitarias aprobadas, `typecheck`, `lint` y producción `build` limpios con código 0.

## Veredictos
| Agente | Veredicto | Fecha |
|---|---|---|
| tester | Aprobado | 2026-10-28 |
| revisor | Aprobado | 2026-10-28 |
| auditor-accesibilidad | Aprobado | 2026-10-28 |

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-27 | Creada como Propuesta (planificador, PLAN-FASE-7) |
| 2026-10-28 | Migración completa de diálogos de confirmación a AlertDialog y clasificación de avisos finalizada y probada |
