# FNC-043 — Configuración del directorio: esquema de OpenLDAP en la API y credencial de bind fuera de la BD

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | configuracion-directorio |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-043-configuracion-directorio-openldap` |
| **Requiere migración BD** | Sí (vaciar y marcar obsoleta `auth_config.ldap_pass`) |
| **Requiere auditor-seguridad** | Sí (secretos) |

## Contexto
- La configuración LDAP vive en `auth_config` con la contraseña de bind en claro (SEG-08) y se edita en `GET/PUT/POST /auth-config` (`app/modules/api/admin.py`), cuyo "probar" combina el host del payload con la contraseña guardada (SEG-22) y devuelve `str(exc)` (SEG-21)
- La cuenta de bind pasa a tener permisos de escritura, por lo que su credencial debe ir a `.env`/Vaultwarden (ADR-004, ADR-005)
- Requerimientos: F-ACC-01, RNF-03

## Objetivo
- Que la API de configuración del directorio muestre la configuración efectiva (sin secretos) y permita al superadmin ajustar solo lo no sensible que ADR-004 deje en BD, con la credencial de bind leída solo del entorno

## Alcance
- **Incluye:**
  - `GET /auth-config`: configuración efectiva del cliente de FNC-040, origen de cada valor y estado de conexión, sin contraseña
  - `PUT /auth-config`: solo campos no sensibles permitidos por ADR-004; rechaza credenciales
  - `POST /auth-config/test`: usa la configuración efectiva, sin aceptar host nuevo con contraseña guardada; mensaje genérico
  - `GET /directory/search` migrado al cliente de FNC-040
  - Migración que vacía `auth_config.ldap_pass` y la marca obsoleta; los campos de mapeo de roles quedan obsoletos (FNC-042)
  - Lo nuevo vive en `app/modules/directory/api.py`; en `admin.py` solo se retiran las rutas movidas (sin refactor del resto)
- **No incluye:**
  - Secretos de SMTP (parte SMTP de FNC-010)
  - Respaldo con hashes (SEG-17, FNC-010)
  - Pantalla (DIS-023)
  - Dividir `admin.py` (FNC-029)

## Hallazgos de seguridad que absorbe
- **FNC-010** parcial: SEG-08 (contraseña de bind) y SEG-22 (prueba LDAP). La parte SMTP y SEG-17 quedan en FNC-010.
- **FNC-017** parcial: SEG-21 en `admin.py:404` y `:637` (prueba LDAP y búsqueda).
- Cierra **FNC-012** junto con FNC-042.

## Archivos previstos
- `app/modules/directory/api.py`
- `app/modules/api/admin.py` (retiro de las rutas movidas)
- `app/modules/auth/models.py` (`AuthConfig`, columnas obsoletas)
- Migración en la carpeta de ADR-002
- `app/__init__.py` (registro del blueprint)
- `tests/directory/test_api.py`

## Reutilización
- Cliente de FNC-040
- `admin_required` de `app/authz.py`

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `/api/v1/auth-config` y `/directory/search` | Endpoints | Pestaña Directorio (`settings-panel.tsx`), alta de usuarios desde el directorio (`users-list.tsx`) | Pendiente |
| `AuthConfig` | Modelo | `app/__init__.py`, `auth/services.py`, `api/admin.py`, respaldo `GET/POST /backup` | Pendiente |
| `app/__init__.py` | Arranque | Toda la app | Pendiente |

## Variables y configuración
- Las de FNC-040 pasan a ser la fuente; `auth_config.ldap_pass` marcada obsoleta en `VARIABLES.md` (configuración en BD) con motivo.

## Criterios de aceptación
- [ ] Ninguna respuesta incluye la credencial (prueba)
- [ ] Un `PUT` con contraseña o host nuevo para probar con la guardada se rechaza (prueba)
- [ ] El respaldo `GET /backup` deja de exportar `ldap_pass` (prueba)
- [ ] La búsqueda en el directorio funciona con `uid` y escapa la entrada
- [ ] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Genera → DIS-023
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-040, FNC-039, FNC-038
- Contrato → docs/contratos/usuarios-directorio.md (sección configuración)

## Riesgos y reversión
- Entornos que dependían de la configuración por interfaz deben cargar las variables antes de desplegar (RELEASES).
- Reversión: la migración conserva la columna (solo la vacía); bajar restaura la lectura previa sin el valor.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
