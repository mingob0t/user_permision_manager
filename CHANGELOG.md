# Changelog

## [Sin publicar]

### Agregado
- Estructura inicial del proyecto (FNC-001, 2026-10-13).
- ESLint estándar de Next.js en el frontend y línea base de typecheck, lint y build (FNC-024, 2026-10-13).
- Suite base de pruebas del backend con pytest: fixtures, BD temporal y clientes por rol (FNC-019, 2026-10-13).
- Pruebas de protección por rol de los 46 endpoints /api/v1 y guardia de rutas sin clasificar (FNC-020, 2026-10-13).
- Pruebas de autenticación: login local, por directorio (LDAP simulado), SSO, logout y sesión (FNC-022, 2026-10-13).
- Pruebas del frontend con Vitest (`npm test`): cliente de la API, `AuditLog`, contraste WCAG de los tokens y tope de colores literales (FNC-025, 2026-10-13).

### Corregido
- El build web ya no falla por lint: enlace de error con `Link` y avisos resueltos (FNC-072, 2026-10-13).

## FNC-022 — Pruebas de autenticación
- Aprobada por el dueño; implementada en `fnc/FNC-022-pruebas-autenticacion`.
- 48 pruebas: login local, directorio con `ldap3` simulado, SSO por `Remote-*`, `/context`, logout y sesión.
- 13 `xfail` con su tarea: SEG-01, 02, 04, 10, 11 y 12 (FNC-002, 003, 006, 013 y 014).
- SEG-14 "desactivar no saca al usuario" no se reproduce: Flask-Login ya da 401.
- Solo pruebas; la app no cambia. `venv/bin/pytest`: 253 passed, 15 xfailed, código 0.
