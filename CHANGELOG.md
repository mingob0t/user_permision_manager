# Changelog

## [Sin publicar]

### Agregado
- Estructura inicial del proyecto (FNC-001, 2026-10-13).
- ESLint estándar de Next.js en el frontend y línea base de typecheck, lint y build (FNC-024, 2026-10-13).
- Suite base de pruebas del backend con pytest: fixtures, BD temporal y clientes por rol (FNC-019, 2026-10-13).
- Pruebas de protección por rol de los 46 endpoints /api/v1 y guardia de rutas sin clasificar (FNC-020, 2026-10-13).
- Pruebas de alcance por área (áreas A y B, 5 actores) y de escalada de privilegios con ids ajenos (FNC-021, 2026-10-13).
- Pruebas de autenticación: login local, por directorio (LDAP simulado), SSO, logout y sesión (FNC-022, 2026-10-13).
- Pruebas de notificaciones, auditoría del CRUD, respaldo, secretos en respuestas, rutas heredadas, CSRF y arranque (FNC-023, 2026-10-14).
- Contratos v1 backend↔web del gestor de accesos en `docs/contratos/` (FNC-038, 2026-10-14).
- Migraciones versionadas con Alembic: línea base `0001` del esquema actual y prueba de desfase modelos↔migraciones (FNC-039, 2026-10-14).
- Cliente OpenLDAP centralizado de solo lectura con TLS validado, CA y esquema configurables por `LDAP_*` (FNC-040, 2026-10-14).
- Servicio de escritura en OpenLDAP: alta y baja idempotentes de miembros de grupo y alta de cuentas sin contraseña, con resultado tipificado (FNC-041, 2026-10-15).
- Auditoría ampliada e inmutable: actor, usuario afectado, área, plataforma, antes/después, catálogo de eventos e IP real del cliente (corrige SEG-25); migración `0002` (FNC-047, 2026-10-14).
- Avisos por correo del gestor de accesos (solicitud nueva, aprobada, rechazada y fallo de aprovisionamiento) con plantillas en la migración `0003`; los correos HTML escapan los valores (corrige SEG-23) (FNC-048, 2026-10-15).
- El admin de área da de alta áreas (queda como su admin), edita y da de baja las suyas; `409` con plataformas o accesos; validación y auditoría del contrato (FNC-045, 2026-10-18).
- Cliente y tipos web de los contratos v1 del gestor de accesos (`lib/access/`), errores con `code`/`fields` y datos simulados tras `NEXT_PUBLIC_ACCESS_MOCKS`; el alta de usuarios ya no envía `auth_source` ni `managed_area_ids` (FNC-069, 2026-10-19).
- Hook web `usePolling`: refresco periódico con el intervalo del usuario, pausa con la pestaña oculta y *backoff* ante errores (ADR-006) (FNC-071, 2026-10-19).
- Pruebas del frontend con Vitest (`npm test`): cliente de la API, `AuditLog`, contraste WCAG de los tokens y tope de colores literales (FNC-025, 2026-10-13).

### Corregido
- Configuración del directorio solo desde `LDAP_*`: la contraseña de bind sale de la BD (migración `0004`), la prueba de conexión y la búsqueda usan el cliente con TLS validado y responden errores genéricos (corrige SEG-08 de LDAP, SEG-13, SEG-21 de LDAP y SEG-22) (FNC-043, 2026-10-18).
- Login por directorio sobre el cliente LDAP con TLS validado: sin purga de cuentas, filtro escapado, respuesta única y sin rol desde LDAP ni `Remote-Groups` (SEG-01, 10, 12; FNC-042, 2026-10-15).
- Solo el superadmin crea o eleva admins y asigna áreas administradas (`PUT /users/<id>/managed-areas`); un admin de área ya no gestiona otros admins ni contraseñas no locales (corrige SEG-05 y SEG-09) (FNC-044, 2026-10-15).
- El build web ya no falla por lint: enlace de error con `Link` y avisos resueltos (FNC-072, 2026-10-13).
