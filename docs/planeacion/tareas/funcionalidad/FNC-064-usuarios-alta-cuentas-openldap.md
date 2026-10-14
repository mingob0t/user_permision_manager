# FNC-064 — Usuarios: crear cuentas en OpenLDAP desde el portal

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | usuarios |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-064-usuarios-alta-cuentas-openldap` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (creación de identidades) |

## Contexto
- `POST /users` (`crud.py:255`) crea la cuenta solo en la BD local y, si no llega contraseña, asigna una fija (SEG-02)
- F-USR-02 pide crearlas en OpenLDAP, fuente de verdad
- Requerimientos: F-USR-02, F-USR-01, RF-02

## Objetivo
- Que el superadmin (y el admin si P2 lo permite) cree la cuenta en OpenLDAP con los atributos de ADR-004 y el usuario local enlazado (`auth_source=ldap`), sin contraseña por defecto, con el flujo de contraseña inicial de P8

## Alcance
- **Incluye:**
  - `POST /users/directory` (o el cambio de `POST /users` que fije el contrato)
  - Validación de identificador único en el directorio y en la BD
  - Sin contraseña por defecto; contraseña inicial según P8
  - Auditoría del alta
- **No incluye:**
  - Borrar o desactivar cuentas en LDAP (fuera de la v1: baja masiva)
  - Elevar a admin (FNC-044)
  - Pantalla (DIS-019)

## Hallazgos de seguridad que absorbe
- **FNC-003** parcial: SEG-02 (contraseña fija en `create_user`). El admin semilla `admin/admin123` (SEG-03) queda en FNC-003.

## Archivos previstos
- `app/modules/users/directory_accounts.py`
- `app/modules/users/api.py`
- `app/modules/api/crud.py` (retiro de la contraseña por defecto)
- `tests/users/`

## Reutilización
- `create_user` de FNC-041
- `sanitize_display_name`

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `POST /api/v1/users` | Endpoint | Pantalla `/users` (`users-list.tsx`) | Pendiente |

## Criterios de aceptación
- [ ] Alta crea la entrada en el directorio (doble de LDAP) y el usuario local (prueba)
- [ ] Sin contraseña no se asigna ninguna por defecto (prueba de regresión SEG-02)
- [ ] Identificador duplicado responde 409 (prueba)
- [ ] Admin de área según P2 (prueba)
- [ ] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Genera → DIS-019
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-041, FNC-044, FNC-038, Respuestas a P2 y P8
- Contrato → docs/contratos/usuarios-directorio.md

## Riesgos y reversión
- Fallo a mitad (LDAP creado, BD no): se crea primero en LDAP y se enlaza de forma idempotente al reintentar.
- Reversión: revertir la rama; las cuentas creadas quedan en el directorio.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
