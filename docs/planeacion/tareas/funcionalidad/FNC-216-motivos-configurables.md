# FNC-216 — Motivo de solicitud y de rechazo configurables desde `.env`

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Fase** | 8 |
| **Estatus** | Hecha |
| **Creada / Finalizada** | 2026-11-27 |
| **Aprobación** | Pedido directo del dueño (2026-11-27), modo autónomo |
| **Genera →** | FNC-217 (web, otro agente) |

## Contexto
- Decisión del dueño (2026-11-27): se controla por variables de entorno, no por pantalla de Configuración.
- **Modifica RF-06** (el rechazo exigía motivo): rechazar sin motivo lo pidió explícitamente el dueño. Nota en `docs/REQUERIMIENTOS.md` y `docs/seguridad/LINEAMIENTOS.md`.

## Cambios
- `access_requests/motivos.py` (nuevo): modos, lectura, `como_dict()` y `validar_al_arrancar()` (llamado desde `create_app`; valor inválido → no arranca, sin repetir el valor).
- `services.limpiar_justificacion`: `oculto` descarta (null, sin validar lo que llegue), `opcional` como antes, `obligatorio` exige no vacía ≤ 500 (`422 validacion` `fields.justification`).
- `approvals.limpiar_motivo_rechazo`: `obligatorio` 10–500; `opcional` vacío → null y si viene 10–500; `oculto` descarta. El rechazo sigue auditado (`solicitud_rechazada`).
- `GET /auth/context` agrega `motivos` (lugar de configuración pública que la web ya consulta antes de pintar).
- `notifications/services.py`: tras renderizar una plantilla HTML se quita el encabezado + `<blockquote>` vacío (la plantilla `solicitud_rechazada` vive en la BD y no se toca).
- Contratos `solicitudes` 1.5 (reglas, campo expuesto, errores, qué debe hacer la web) y `autenticacion` 1.1. Variables, historial, `.env.example`, CHANGELOG.

## Decisiones
- Por omisión `SOLICITUD_MOTIVO=oculto`: la API **descarta** `justification` (antes la guardaba si llegaba). Las pruebas heredadas de `access_requests` fijan `opcional`.
- Modos en minúsculas sin importar mayúsculas; vacío = valor por omisión.
- Cambiar el valor exige reiniciar el backend (se lee del entorno al validar; se relee por petición, pero `.env` solo se carga al arrancar).

## Verificación
- `tests/access_requests/test_motivos.py` (18), caso nuevo en `tests/notifications/test_access_notifications.py`; `tests/test_oidc.py` ajustado (clave `motivos` del contexto). Suite completa de backend: `3736 passed`, salida 0.
- No verificado: render del correo en un cliente real; revisor/auditor-seguridad no se ejecutaron (cambio acotado; `motivos` en `/auth/context` es público y no sensible).

## Impacto en elementos compartidos
- `GET /auth/context` (campo nuevo, aditivo), `render` de plantillas HTML (`send_notification_by_slug`, afecta todo correo HTML con `<p>…:</p><blockquote></blockquote>` vacío), `limpiar_justificacion` y `limpiar_motivo_rechazo`.

## Bitácora
- 2026-11-27: implementada y cerrada.
