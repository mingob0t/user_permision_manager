> **OBSOLETO PARCIALMENTE (FNC-001, 2026-10-13).** Se conserva como referencia histórica; la fuente vigente es `docs/backend/README.md`, `docs/frontend/README.md` y `docs/decisiones/ADR-001-stack.md`. Ya no aplica:
> - **AccessRequests**: la tabla `access_requests` se eliminó (migración `004_drop_access_requests.sql`); no hay flujo de solicitudes de acceso.
> - **RBAC con dos roles** (`administrador` y `usuario`): el código tiene tres (`administrador`, `admin_area`, `usuario`) con alcance por área en `app/authz.py`.
> - **"Variables Jinja2 en los correos"** y slugs `inicio`/`terminado`/`error`: las plantillas sustituyen `{clave}` por texto plano y el único slug usado por el código es `usuario_creado`.
> - **"Notificaciones in-app en tiempo real"**: son una lista consultada por petición (`GET /api/v1/notifications`), sin push.
> - El modelo de datos omite `users`, `user_areas`, `area_admins`, `user_platforms`, `user_favorites`, `auth_config`, `smtp_config`, `notification_templates`, `in_app_notifications` y `system_config`.
> Siguen vigentes: separación Flask API / Next.js, mismo dominio tras nginx y la tabla de alcance multitenant.

# 🏗️ ARQUITECTURA TÉCNICA - NEXUS

## 🧩 Patrón de Diseño
NEXUS separa frontend y backend en dos servicios:

*   **Backend Flask** — solo API JSON bajo `/api/v1`. Modular por Blueprints;
    cada módulo maneja su lógica, modelos y rutas. No sirve interfaz.
*   **Frontend Next.js** — toda la interfaz. Consume la API con la cookie de
    sesión que emite Flask, sin acceso directo a la base de datos.

Ambos se sirven bajo el mismo dominio tras Nginx, de modo que la cookie viaja
sin CORS y Authelia sigue siendo la autoridad de autenticación.

## 🏢 Multitenant
El **Área** es la unidad de aislamiento. Tres niveles, resueltos en
`app/authz.py`:

| Rol | Alcance |
|---|---|
| `administrador` | Todo el sistema y su configuración |
| `admin_area` | Solo las áreas que administra (`area_admins`) |
| `usuario` | Solo consulta las plataformas de sus áreas |

El aislamiento se aplica por fila: las funciones `scoped_*` filtran cada
consulta según el alcance de quien la hace. La interfaz oculta lo que el rol no
permite, pero el backend vuelve a comprobarlo en cada endpoint.

## 💾 Modelado de Datos
El sistema utiliza SQLAlchemy para la persistencia de datos con un enfoque en la gestión de accesos:

1.  **Areas**: Define los departamentos u organizaciones lógicas.
2.  **Platforms**: Representa los sistemas o servicios finales a los que los usuarios acceden.
3.  **AccessRequests**: Gestiona el flujo de solicitudes de acceso entre usuarios y plataformas.
4.  **AuditLogs**: Registro histórico de acciones administrativas y de usuario.

## 🔐 Seguridad y Auditoría
*   **RBAC (Role Based Access Control)**: Control de acceso basado en roles (`administrador` y `usuario`).
*   **LDAP Integration**: Permite la sincronización de usuarios corporativos mapeando atributos CN y Mail.
*   **AuditLog**: Cada interacción de escritura o cambio de configuración se registra en la tabla `audit_logs`, capturando Usuario, IP, Acción y Timestamp.

## 📧 Motor de Notificaciones
Centralizado en el módulo `notifications`, permite:
*   Configuración dinámica de SMTP.
*   Uso de **Slugs** (ej: `inicio`, `terminado`, `error`) para llamar a plantillas preconfiguradas.
*   Inyección de contexto dinámico (Variables Jinja2 en los correos).
*   Notificaciones In-App para avisos en tiempo real dentro del portal.
