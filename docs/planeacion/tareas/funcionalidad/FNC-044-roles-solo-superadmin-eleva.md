# FNC-044 — Roles: solo el superadmin crea o eleva admins y asigna las áreas administradas

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | usuarios-roles |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-044-roles-solo-superadmin-eleva` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (autorización) |

## Contexto
- Un `admin_area` puede crear o elevar a otro `admin_area` (`crud.py:236-252`, SEG-09) y tomar la cuenta de otro admin (`authz.py:180-200`, SEG-05)
- Un admin nuevo administra "las mismas áreas a las que pertenece", sin decisión explícita
- RF-04 exige que solo el superadmin cree o eleve admins, y F-AREA-02 que solo él asigne admins a un área
- Requerimientos: F-AREA-02, F-USR-03, RF-04

## Objetivo
- Que solo el superadmin asigne los roles `admin_area` y `administrador` y las filas de `area_admins`; que un admin de área no gestione cuentas de otros admins; y exponer un endpoint explícito para asignar las áreas que administra un admin

## Alcance
- **Incluye:**
  - `can_manage_user`: un admin de área solo gestiona cuentas con rol `usuario` de sus áreas
  - `POST/PUT /users`: el rol solo lo cambia el superadmin; un admin de área no puede crear ni editar admins
  - Nuevo `PUT /users/<id>/managed-areas` (superadmin) para `area_admins`; quitar el rol borra sus áreas administradas
  - Un solo `administrador`: no se puede crear un segundo (coherente con FNC-042)
  - Pruebas de escalada (la base viene de FNC-021)
- **No incluye:**
  - Acceso automático a las plataformas de un área al asignarla (FNC-055)
  - Alta de cuentas en LDAP (FNC-064)
  - Alta de áreas por el admin (FNC-045)
  - Pantallas (DIS-016, DIS-019)

## Hallazgos de seguridad que absorbe
- **FNC-007** completo (SEG-05, SEG-09).

## Archivos previstos
- `app/authz.py` (`can_manage_user`, `scoped_users`)
- `app/modules/api/crud.py` (`create_user`, `update_user`, validación de rol)
- `app/modules/users/` nuevo `api.py` para `managed-areas` (no crece `crud.py`)
- `tests/users/`

## Reutilización
- `is_admin`, `managed_area_ids`, `scoped_users` de `app/authz.py`
- `add_audit_log` ampliado (FNC-047)

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `can_manage_user`, `scoped_users` | Funciones de autorización | `PUT/DELETE /users/<id>`, `PUT /users/<id>/areas`, `PUT /users/<id>/platforms`, `GET /users` (`crud.py`, `routes.py`); pantalla `/users` | Pendiente |
| Reglas de `POST/PUT /users` | Endpoint | Pantalla `/users` (`users-list.tsx`) | Pendiente |

## Criterios de aceptación
- [ ] Un `admin_area` que intenta crear o elevar un admin recibe 403 (prueba de regresión que primero falla)
- [ ] Un `admin_area` no puede editar ni borrar a otro admin (prueba de regresión)
- [ ] Solo el superadmin cambia `area_admins` (prueba)
- [ ] No puede existir un segundo `administrador` (prueba)
- [ ] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Genera → DIS-016, DIS-019
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-038, FNC-047
- Contrato → docs/contratos/areas-y-roles.md

## Riesgos y reversión
- Admins de área existentes con áreas implícitas: la tarea documenta cómo quedan y el superadmin las revisa.
- Reversión: revertir la rama; no hay migración.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
