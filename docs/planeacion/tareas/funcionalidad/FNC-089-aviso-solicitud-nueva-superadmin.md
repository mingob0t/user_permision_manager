# FNC-089 — Aviso `solicitud_nueva` también al superadmin (por confirmar)

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | notificaciones |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-20 |

## Contexto
- El encargo de FNC-056 mencionaba "admins del área y superadmin"; la decisión del dueño, el contrato `solicitudes.md` y FNC-048 dicen solo admins del área. FNC-056 reusa `notificar_solicitud_nueva` sin cambios (solo admins del área).
- Hueco: un área sin admins activos no avisa a nadie, aunque el superadmin puede aprobar.
- Pregunta al dueño: ¿superadmin siempre, solo como respaldo cuando el área no tiene admins, o nunca?
- Origen: FNC-056.

## Criterios de aceptación
- [ ] Destinatarios según la respuesta del dueño, con prueba de SMTP simulado
- [ ] Contrato y `docs/backend/README.md` actualizados

## Impacto cruzado
- Origen ← FNC-056; toca `app/modules/notifications/access_notifications.py` (compartido con FNC-057)
