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
- Pruebas del frontend con Vitest (`npm test`): cliente de la API, `AuditLog`, contraste WCAG de los tokens y tope de colores literales (FNC-025, 2026-10-13).

### Corregido
- Login por directorio sobre el cliente LDAP con TLS validado: sin purga de cuentas, filtro escapado, respuesta única y sin rol desde LDAP ni `Remote-Groups` (SEG-01, 10, 12; FNC-042, 2026-10-15).
- El build web ya no falla por lint: enlace de error con `Link` y avisos resueltos (FNC-072, 2026-10-13).
