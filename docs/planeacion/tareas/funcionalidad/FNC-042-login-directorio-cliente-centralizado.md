# FNC-042 — Login por directorio sobre el cliente centralizado, sin purga de cuentas y sin elevar rol desde LDAP

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | auth |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-042-login-directorio-cliente-centralizado` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (autenticación y rol) |

## Contexto
- `authenticate_user_ldap` (`app/modules/auth/services.py`) abre su propia conexión sin validar TLS, usa `sAMAccountName`, construye el filtro sin escapar (SEG-12), borra la cuenta local si no aparece en el directorio (SEG-01) y deriva `administrador` por subcadena del DN de grupo (SEG-10)
- Con OpenLDAP como fuente de verdad y "solo el superadmin eleva" (RF-04), el login tiene que pasar al cliente nuevo y dejar de elevar roles
- Requerimientos: F-USR-01, RF-04, OB-01

## Objetivo
- Migrar el login de directorio y la derivación de rol de LDAP y SSO al cliente de FNC-040: el directorio autentica, pero el rol lo asigna solo el superadmin en el portal; ninguna cuenta se borra por no aparecer

## Alcance
- **Incluye:**
  - `authenticate_user_ldap` usa `app/modules/directory`; filtro escapado y mensaje único para usuario inexistente o contraseña incorrecta
  - Se elimina el "protocolo de purga" del login
  - Rol: una cuenta nueva por LDAP o SSO entra como `usuario`; el directorio y `AUTHELIA_GROUP_ADMIN` ya no asignan `administrador` ni `admin_area`; se conserva el rol asignado en el portal
  - Un solo superadmin (comprobación al asignar, coordinada con FNC-044)
  - Pruebas de regresión que primero fallan para SEG-01, SEG-10 y SEG-12
- **No incluye:**
  - Secreto compartido con el proxy (FNC-006)
  - Límite de intentos (FNC-014)
  - CSRF y sesión (FNC-008)
  - Credenciales por defecto `admin/admin123` (FNC-003)

## Hallazgos de seguridad que absorbe
- **FNC-002** completo (SEG-01, SEG-12).
- **FNC-012** (resto: login migrado al cliente con TLS validado).
- **FNC-013** completo (SEG-10).
- No absorbe FNC-006, FNC-008 ni FNC-014 aunque estén en el mismo módulo `auth`: tocan otras funciones. Si el dueño interpreta la regla por módulo completo (pregunta P13), se agregan aquí.

## Archivos previstos
- `app/modules/auth/services.py`
- `app/modules/api/auth.py` (solo la derivación de rol en `/sso`)
- `tests/auth/`

## Reutilización
- `app/modules/directory/ldap_client.py` (FNC-040)
- `add_audit_log` ampliado (FNC-047)

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `authenticate_user_ldap` | Servicio | `POST /api/v1/auth/login`, `utils/test_ldap.py` | Pendiente |
| Derivación de rol SSO | Regla de autorización | `POST /api/v1/auth/sso`; todas las pantallas que dependen de `/me.permissions` | Pendiente |
| `AuthConfig.ldap_group_admin`, `ldap_role_mappings` | Configuración en BD | Pestaña Directorio de Ajustes (`settings-panel.tsx`) | Pendiente |

## Variables y configuración
- `AUTHELIA_GROUP_ADMIN` deja de asignar rol: marcar como *obsoleta* en `VARIABLES.md` con fecha y motivo (RF-04).

## Criterios de aceptación
- [ ] Login con un usuario de OpenLDAP real del entorno de pruebas o con doble: entra con atributo `uid`
- [ ] Una cuenta local cuyo correo no está en el directorio sigue existiendo tras un login de directorio fallido (prueba de regresión)
- [ ] Un miembro de un grupo "admin" del directorio entra como `usuario` si el portal no lo elevó (prueba)
- [ ] Respuesta idéntica para usuario inexistente y contraseña incorrecta (prueba)
- [ ] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-040, FNC-047

## Riesgos y reversión
- Usuarios que hoy son administradores por grupo LDAP pierden el rol: antes de desplegar, el superadmin los registra en el portal (nota en RELEASES).
- Reversión: revertir la rama; no hay migración.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
