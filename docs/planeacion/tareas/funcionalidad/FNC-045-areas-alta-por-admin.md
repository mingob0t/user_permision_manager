# FNC-045 — Áreas: el admin da de alta sus áreas y queda como su administrador

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | areas |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-045-areas-alta-por-admin` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (autorización) |

## Contexto
- Hoy solo el superadmin crea áreas (`POST /areas` con `admin_required`, `crud.py:35`)
- F-AREA-01 pide que el admin dé de alta las suyas y quede asignado automáticamente
- Requerimientos: F-AREA-01, RF-01

## Objetivo
- Permitir a un `admin_area` crear un área, que queda en sus `area_admins`; edición en su alcance; baja según la decisión del dueño (pregunta P11)

## Alcance
- **Incluye:**
  - `POST /areas` con `any_admin_required`; si lo crea un admin de área, se agrega a `area_admins` en la misma transacción
  - `PUT /areas/<id>` sigue con `area_admin_required`
  - `DELETE /areas/<id>`: según P11 (dueño, 2026-10-14): el admin de esas áreas y el superadmin; 409 si tiene plataformas o accesos activos. Agregar el caso a `tests/matriz_proteccion.py`
  - Auditoría del alta con actor y área
- **No incluye:**
  - Asignar admins a un área (FNC-044, superadmin)
  - Acceso automático a plataformas (FNC-055)
  - Pantalla (DIS-016)

## Archivos previstos
- `app/modules/api/crud.py` (solo `create_area` y `delete_area`)
- `tests/areas/`

## Reutilización
- `any_admin_required`, `area_admin_required`, `can_manage_area` de `app/authz.py`
- `sanitize_display_name`

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `POST/DELETE /api/v1/areas` | Endpoint | Pantalla `/areas` (`areas-list.tsx`) | Pendiente |

## Criterios de aceptación
- [ ] Un `admin_area` crea un área y aparece en sus áreas administradas (prueba)
- [ ] Un `usuario` recibe 403 (prueba)
- [ ] Nombre duplicado responde 409 (prueba)
- [ ] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Genera → DIS-016
- Genera → FNC-055
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-044, FNC-038, FNC-047
- Contrato → docs/contratos/areas-y-roles.md

## Riesgos y reversión
- Proliferación de áreas: queda auditada. Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
