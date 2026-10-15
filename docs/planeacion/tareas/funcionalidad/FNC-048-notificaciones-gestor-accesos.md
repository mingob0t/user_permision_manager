# FNC-048 — Notificaciones del gestor de accesos: plantillas y envío por evento

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | notificaciones |
| **Prioridad** | Alta |
| **Estatus** | Hecha |
| **Creada** | 2026-10-13 |
| **Inicio** | 2026-10-15 |
| **Finalizada** | 2026-10-15 |
| **Estatus Git** | Commit local, sin push |
| **Rama** | `fnc/FNC-048-notificaciones-gestor` (worktree `pokemon-wt-048`) |
| **Commits / PR** | `8d8a908`, `ecaf71e`, `8f4acba` y el de hashes en ficha y tablero (locales, sin push ni PR) |
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
| `send_notification_by_slug` (escape HTML, asunto sin CR/LF, sustitución de una pasada) | Servicio compartido | `api/auth.py` (alta por SSO), `auth/services.py` (alta por LDAP) con `usuario_creado`; `POST /smtp/test` **no** lo usa (usa `send_test_email`) | Pruebas: `test_notificaciones.py` y `test_sso.py`/`test_login_directorio.py` en verde; validar el correo `usuario_creado` real si su plantilla es HTML con `&` en la URL (ahora `&amp;`, correcto en HTML) |
| `Evento` (+`NOTIFICACION_FALLIDA`) | Enum compartido | `audit/models.py`, `audit/services.py`, filtro `action` de `GET /audit`; contrato `auditoria.md` (aditivo) | `test_el_catalogo_coincide_con_el_contrato` en verde |

Salida real de `impacto.py` (contra `develop`, con los archivos nuevos en `git add -N`):

| Elemento | Usado en (según la herramienta) | Lectura |
|---|---|---|
| `BASE_URL` | `api/auth.py`, `auth/services.py`, `tests/conftest.py`, `test_sesion_y_logout.py` | Solo se lee; sin cambio de valor ni significado |
| `ENABLE_NOTIFICATIONS` | `tests/conftest.py` | No cambió: aparece en el contexto del diff de `services.py` |
| `Evento` | `audit/models.py`, `audit/services.py`, `test_registro_ampliado.py` | Real (valor nuevo, aditivo) |
| `correo` | `api/admin.py`, `api/crud.py`, `frontend/…` (+12) | Homónimo: *fixture* local de la prueba |
| `correos` | `api/auth.py`, `test_alcance_por_area.py`, `test_respaldo.py` | Homónimo: función nueva del módulo; esos archivos usan variables con el mismo nombre |
| `escenario`, `motor` | `tests/…`, `migrations/env.py` | Homónimos: *fixtures* locales |
| `upgrade`, `downgrade` | `0001`, `0002`, `env.py`, `test_migraciones.py` | Convención de Alembic (cada migración define las suyas) |

- La herramienta no detecta `send_notification_by_slug` (cambió el cuerpo, no el nombre); se agrega a mano arriba.

## Variables y configuración
- `NOTIFY_ACCESS_EVENTS` (`true` por defecto): interruptor de estos avisos; `ENABLE_NOTIFICATIONS` sigue mandando. Registrada en `VARIABLES.md`, `HISTORIAL.md` y `.env.example`.
- Constantes con nombre: `CLAVES_POR_PLANTILLA`, `OPERACIONES`, `SEPARADOR_DESTINATARIOS`, `PATRON_CORREO`, `PATRON_VARIABLE`, `PATRON_SALTO_DE_LINEA`.

## Decisiones
- Envío síncrono después del commit: ADR-003 aprobó Redis + RQ, pero la cola (FNC-049) aún no existe; FNC-049 puede encolar llamando a estas mismas funciones.
- Con `ENABLE_NOTIFICATIONS` apagado los avisos devuelven `skipped` sin conectar (`notifications_enabled()` compartido con `send_notification_by_slug`).
- Los cuatro avisos respetan `pref_email_notifications`, incluido `aprovisionamiento_fallido` (respuesta del dueño a P10, 2026-10-15; antes se ignoraba como valor más seguro del contrato).
- Ninguna función pública lanza: plataforma sin área, usuario faltante u operación desconocida → log y `{'status': 'error', 'recipients': 0}` (endurecimiento de seguridad, Baja).

## Para quien llame (FNC-049, FNC-056, FNC-057)
- Llamar **después del commit** de la operación de negocio y **dentro de `try`**: el aviso nunca debe revertirla ni romper la respuesta.
- Pasar objetos de la BD (`User`, `Platform` con su `area`), nunca datos de la petición (SEC-MAIL-03).
- Destinatarios: solo usuarios activos; admins con rol `admin_area` (un degradado que siga en `area_admins` no recibe); un solo envío con todos en `To`.
- Fallo de correo: log + auditoría `notificacion_fallida` (actor `sistema`, `target` = plantilla, sin el detalle del servidor). Valor nuevo del catálogo, aditivo en `auditoria.md`.
- "Acceso revocado": no hay plantilla; ni la ficha ni los contratos piden correo al revocar (P7).
- FNC-031 no se absorbe (excluida en el alcance): su `xfail` sigue.

## Verificación
- Regresiones que primero fallan (con `services.py` de `develop`): `test_plantilla_html_escapa_los_valores_del_contexto`, `test_asunto_sin_saltos_de_linea_de_los_valores`, `test_un_valor_no_inyecta_otra_variable` → 3 failed.
- `xfail` de SEG-23 quitado de `test_plantilla_html_escapa_los_valores_del_contexto`; pasa como prueba normal.
- Nuevas: `tests/notifications/test_access_notifications.py` (destinatarios por evento, preferencia, inactivos, degradado, `<script>` escapado, CR/LF, `BASE_URL`, interruptor, SMTP caído con auditoría, excepción, commit conservado, sin destinatarios) y `test_migracion_plantillas.py` (upgrade, no pisa ediciones, downgrade).
- `venv/bin/python -m pytest -q` → `552 passed, 34 xfailed in 335.78s`, código 0.
- Ajuste 2026-10-15 (P10 y endurecimiento): 8 pruebas nuevas o cambiadas primero fallan (`8 failed, 20 passed`); con el cambio `tests/notifications` → 28 passed; suite completa → `558 passed, 34 xfailed in 333.68s`, código 0.
- Correcciones del revisor: 4 pruebas nuevas primero fallan (`4 failed, 28 passed`); con el cambio `tests/notifications` + `test_notificaciones.py` → 68 passed, 1 xfailed; suite completa en la bitácora.
- No verificado: envío real por SMTP; migración `0003` en MySQL (solo SQLite); edición en Ajustes → Plantillas en el navegador (la pestaña lista por `slug` sin cambios de interfaz). `auditor-seguridad`: Aprobado (2026-10-15). Falta `revisor`.

## Criterios de aceptación
- [x] Cada evento envía a los destinatarios correctos con SMTP simulado (pruebas)
- [x] Un `<script>` en la justificación llega escapado (prueba de regresión)
- [x] Con SMTP caído la operación de negocio termina bien y queda registro (prueba)
- [ ] Las plantillas se editan desde Ajustes → Plantillas sin cambios de interfaz
- [ ] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Genera → Llamadas desde FNC-049, FNC-056, FNC-057
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-039, ADR-003

## Riesgos y reversión
- Correos a muchos admins por área: se agrupan destinatarios en un envío.
- Reversión: bajar la migración `0003`; borra solo las plantillas que siguen idénticas a las insertadas (una preexistente o editada desde la interfaz se conserva; prueba en `test_migracion_plantillas.py`).

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-15 | Aprobada por el dueño (comunicado por el orquestador); implementada por desarrollador en `pokemon-wt-048`; migración `0003`; cierra SEG-23 (FNC-017 parcial); queda En revisión (falta revisor y auditor-seguridad) |
| 2026-10-15 | `auditor-seguridad`: Aprobado. Ajustes: P10 (el aviso de fallo respeta `pref_email_notifications`, decisión del dueño), funciones que nunca lanzan (endurecimiento Baja), nota para llamadores. Sigue En revisión (falta revisor) |
| 2026-10-15 | `revisor`: Requiere cambios: interruptor global → `skipped`, downgrade de `0003` solo borra lo insertado sin cambios, `REQUERIMIENTOS.md` (OB-02, F-NOT-01), hashes en ficha y tablero. Corregidos; la IP literal de `auth/services.py` queda para FNC-042. Pytest completo: 562 passed, 34 xfailed, código 0. Sigue En revisión |
| 2026-10-15 | Hecha: revisor y auditor-seguridad atendidos; merge local a `develop` aprobado por el dueño |
