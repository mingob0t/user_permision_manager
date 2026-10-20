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
- Ejecutor de aprovisionamiento con Redis + RQ: trabajos e intentos en la BD (migración `0006`), `flask provisioning worker`, reintentos con *backoff*, bitácora sin secretos, auditoría `sistema` y aviso de fallo (FNC-049, 2026-10-19).
- Alta de cuentas en OpenLDAP desde el portal (`POST /users/directory`): superadmin y admins para sus áreas, rol `usuario`, sin contraseña, 409 por uid o correo duplicados y auditoría (FNC-064, 2026-10-19).
- Hook web `usePolling`: refresco periódico con el intervalo del usuario, pausa con la pestaña oculta y *backoff* ante errores (ADR-006) (FNC-071, 2026-10-19).
- Menú por rol del gestor de accesos (Mis solicitudes, Aprobaciones, Inventario, Conectores; Plataformas pasa a Catálogo), guarda `RequireRole` y rutas reservadas (FNC-070, 2026-10-19).
- Pruebas del frontend con Vitest (`npm test`): cliente de la API, `AuditLog`, contraste WCAG de los tokens y tope de colores literales (FNC-025, 2026-10-13).
- Plataformas con tipo de integración (`ldap`/`conector`) y grupos del directorio por nivel validados bajo `LDAP_GROUPS_BASE_DN`; URLs solo `https://` (corrige SEG-24 en el backend); migración `0005` (FNC-046, 2026-10-19).
- Pantalla de áreas: el admin de área da de alta y gestiona las suyas; el superadmin asigna sus administradores; errores por campo y mensajes de los `409` (DIS-016, 2026-10-19).
- Formulario de plataformas con tipo de integración y grupos de acceso por nivel (solo superadmin), avisos tras guardar, errores por campo y de los `403`/`409`; la tarjeta y la tabla solo enlazan `https://` (corrige SEG-24 en el frontend) (DIS-017, 2026-10-19).

### Corregido
- Contraste AA del texto de estado (éxito, error, advertencia, estrella de favorito) con tokens `*-text` por tema, sin clases de paleta fija (DIS-002, 2026-10-19).
- Contraste AA de los tokens por tema: título de modales e insignias en oscuro, header y pestaña activa en emerald/rose/violet, y color de marca como texto con variantes `*-text` (DIS-001, 2026-10-19).
- Login local solo para la cuenta de emergencia (superadmin local) y con `auth_source=local`; el alta de usuarios ya no fija `nexus123` y el portal no fija contraseñas locales salvo la de emergencia; excepción de desarrollo `LOGIN_LOCAL_TODAS_LAS_CUENTAS` (corrige SEG-02) (FNC-077, 2026-10-19).
- Configuración del directorio solo desde `LDAP_*`: la contraseña de bind sale de la BD (migración `0004`), la prueba de conexión y la búsqueda usan el cliente con TLS validado y responden errores genéricos (corrige SEG-08 de LDAP, SEG-13, SEG-21 de LDAP y SEG-22) (FNC-043, 2026-10-18).
- Login por directorio sobre el cliente LDAP con TLS validado: sin purga de cuentas, filtro escapado, respuesta única y sin rol desde LDAP ni `Remote-Groups` (SEG-01, 10, 12; FNC-042, 2026-10-15).
- Solo el superadmin crea o eleva admins y asigna áreas administradas (`PUT /users/<id>/managed-areas`); un admin de área ya no gestiona otros admins ni contraseñas no locales (corrige SEG-05 y SEG-09) (FNC-044, 2026-10-15).
- El build web ya no falla por lint: enlace de error con `Link` y avisos resueltos (FNC-072, 2026-10-13).
