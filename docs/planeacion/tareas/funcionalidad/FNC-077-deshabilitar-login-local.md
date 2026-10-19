# FNC-077 — Deshabilitar el login local (solo Authelia/directorio), salvo acceso de emergencia del superadmin

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | auth |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-15 |

## Contexto
- Decisión del dueño (2026-10-15, revisión de FNC-044): la autenticación local se deshabilita; todo va por Authelia.
- Hoy `POST /api/v1/auth/login` acepta `method: local` y `POST/PUT /users` manejan contraseñas locales.
- Se conserva solo el acceso de emergencia del superadmin (ver SEC-AUTH y pregunta 5 de `docs/seguridad/LINEAMIENTOS.md` §12).

## Criterios de aceptación
- [ ] `method: local` rechazado para toda cuenta salvo la de emergencia del superadmin
- [ ] Alta y edición de cuentas sin contraseña local (revisar `POST/PUT /users`, FNC-044)
- [ ] Contrato y pantalla de login actualizados por tarea vinculada
- [ ] Prueba de regresión que primero falla

## Impacto cruzado
- Origen ← FNC-044 (decisión del dueño)
- Relacionadas → FNC-003, FNC-042, FNC-078, FNC-079

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-15 | Creada como Propuesta (decisión del dueño en la revisión de FNC-044) |
