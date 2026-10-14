# FNC-048 — Notificaciones del gestor de accesos: plantillas y envío por evento

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | notificaciones |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-048-notificaciones-gestor-accesos` |
| **Requiere migración BD** | Sí (datos: plantillas nuevas) |
| **Requiere auditor-seguridad** | Sí (contenido de usuario en correos) |

## Contexto
- El motor de correo existe (`send_notification_by_slug`, `app/modules/notifications/services.py:191`) pero solo se usa `usuario_creado`, y sustituye valores en HTML sin escapar (SEG-23): con F-NOT-01 la justificación del solicitante llegará a los admins y serviría para *phishing* desde el remitente corporativo
- Requerimientos: F-NOT-01, OB-02

## Objetivo
- Agregar las plantillas y un servicio de avisos del gestor de accesos con destinatarios resueltos por regla, para que los módulos de solicitudes, aprobaciones y aprovisionamiento solo llamen a una función por evento

## Alcance
- **Incluye:**
  - Plantillas `solicitud_nueva` (admins del área de la plataforma), `solicitud_aprobada` y `solicitud_rechazada` (solicitante, con motivo), `aprovisionamiento_fallido` (destinatarios según P10)
  - `access_notifications.py` con una función por evento; resuelve destinatarios con `area_admins` y respeta `pref_email_notifications` según P10
  - Escape HTML de todos los valores del contexto cuando la plantilla es HTML
  - Envío fuera de la transacción: un fallo de SMTP no revierte la operación y queda en el log y en auditoría
  - Si ADR-003 lo aprueba, el envío se encola en el ejecutor (FNC-049); si no, se hace después del commit
- **No incluye:**
  - Notificaciones in-app (sugerencia fuera de alcance)
  - Recordatorios y escalamiento (fuera de la v1)
  - Corregir notificaciones globales leídas (FNC-031)

## Hallazgos de seguridad que absorbe
- **FNC-017** parcial: SEG-23 (escape en correos).
- Duplicado D-04 no se absorbe (aviso de usuario creado, FNC-030).

## Archivos previstos
- `app/modules/notifications/access_notifications.py` (nuevo)
- `app/modules/notifications/services.py` (escape en `send_notification_by_slug`)
- Migración de datos con las plantillas (ADR-002)
- `tests/notifications/`

## Reutilización
- `send_notification_by_slug`, `resolve_smtp_settings`, modelo `NotificationTemplate` y la pestaña Plantillas existente para editarlas

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `send_notification_by_slug` | Servicio compartido | `api/auth.py` (alta por SSO), `auth/services.py` (alta por LDAP), `POST /smtp/test` | Pendiente |

## Variables y configuración
- `NOTIFY_ACCESS_EVENTS` (`true`/`false`, interruptor del módulo) si el dueño lo quiere aparte de `ENABLE_NOTIFICATIONS`; registrar.

## Criterios de aceptación
- [ ] Cada evento envía a los destinatarios correctos con SMTP simulado (pruebas)
- [ ] Un `<script>` en la justificación llega escapado (prueba de regresión)
- [ ] Con SMTP caído la operación de negocio termina bien y queda registro (prueba)
- [ ] Las plantillas se editan desde Ajustes → Plantillas sin cambios de interfaz
- [ ] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Genera → Llamadas desde FNC-049, FNC-056, FNC-057
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-039, ADR-003

## Riesgos y reversión
- Correos a muchos admins por área: se agrupan destinatarios en un envío.
- Reversión: bajar la migración de plantillas.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
