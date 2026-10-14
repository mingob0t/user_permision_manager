# DIS-016 — Áreas: alta por el admin y asignación de admins por el superadmin

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | areas |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `dis/DIS-016-areas-alta-admin-asignacion` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- En `/areas` (`areas-list.tsx`) solo el superadmin crea áreas; no hay forma explícita de asignar admins (F-AREA-01/02)
- Requerimientos: F-AREA-01, F-AREA-02, RF-04

## Objetivo
- Permitir al admin crear sus áreas y al superadmin asignar o quitar admins de un área

## Alcance
- **Incluye:**
  - Botón y formulario de alta visibles para `admin_area`
  - Panel "Administradores del área" solo para el superadmin, con búsqueda de usuarios
  - Lo nuevo en archivos propios; `areas-list.tsx` solo los importa
- **No incluye:**
  - Rediseño de la lista de áreas
  - Estilos inline existentes de `areas-list.tsx` (DIS-012)

## Archivos previstos
- `frontend/src/components/areas/area-admins-panel.tsx`
- `frontend/src/components/areas/area-form.tsx` (si se extrae el existente)
- `frontend/src/components/areas-list.tsx` (importaciones y permiso del botón)

## Reutilización
- `Modal`, `Field`, `Select`, `Button`, `ConfirmDialog`

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `areas-list.tsx` | Pantalla | `/areas` | Pendiente |

## Criterios de aceptación
- [ ] Un admin de área no ve el panel de asignación
- [ ] Criterios comunes de diseño (FNC-037)

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-024, FNC-025, FNC-069, FNC-044, FNC-045
- Contrato → docs/contratos/areas-y-roles.md

## Riesgos y reversión
- Puede avanzar con los datos simulados de FNC-069; se integra después del backend.
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
