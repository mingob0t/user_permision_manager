# DIS-019 — Usuarios: alta en el directorio y elevación a admin

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | usuarios |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `dis/DIS-019-usuarios-alta-directorio-elevacion` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- El alta actual crea cuentas locales con rol libre; RF-04 y F-USR-02 piden alta en OpenLDAP y que solo el superadmin eleve y asigne áreas administradas
- Requerimientos: F-USR-02, F-USR-03, F-AREA-02, RF-04

## Objetivo
- Formulario de alta en el directorio (campos de ADR-004) y, solo para el superadmin, acciones "Hacer admin" con selección de áreas administradas y "Quitar admin"

## Alcance
- **Incluye:**
  - Formulario en componente propio
  - Acciones de rol solo visibles al superadmin
  - Mensajes de 409 (identificador existente)
- **No incluye:**
  - Revocación (DIS-018)
  - Purga de inactivos (sin cambios)

## Archivos previstos
- `frontend/src/components/users/directory-account-form.tsx`
- `frontend/src/components/users/admin-role-dialog.tsx`
- `frontend/src/components/users-list.tsx` (importaciones y permisos de botones)

## Reutilización
- `Modal`, `Field`, `Select`, `Checkbox`, `ConfirmDialog`

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `users-list.tsx` | Pantalla | `/users` | Pendiente |

## Criterios de aceptación
- [ ] Un admin de área no ve opciones de rol
- [ ] Criterios comunes de diseño (FNC-037)

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-024, FNC-025, FNC-069, FNC-064, FNC-044, DIS-018 (mismo archivo, en secuencia)
- Contrato → docs/contratos/usuarios-directorio.md y areas-y-roles.md

## Riesgos y reversión
- Puede avanzar con los datos simulados de FNC-069; se integra después del backend.
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
