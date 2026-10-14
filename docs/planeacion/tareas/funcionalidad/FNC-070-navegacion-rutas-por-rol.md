# FNC-070 — Navegación y rutas por rol del gestor de accesos

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | web |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | navegacion |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-070-navegacion-rutas-por-rol` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- El menú (`NAV` en `frontend/src/components/app-shell.tsx`) solo distingue `any_admin`; la fase agrega Mis solicitudes, Aprobaciones, Inventario y Conectores con visibilidad por rol (tabla de pantallas)
- La barra lateral se oculta en móvil sin alternativa (deuda 8 del frontend)
- Requerimientos: Tabla de pantallas por rol (REQUERIMIENTOS §4)

## Objetivo
- Agregar las entradas nuevas con su permiso, una guarda de ruta reutilizable que muestra el estado "sin permiso" y las rutas de página vacías que llenarán las tareas DIS

## Alcance
- **Incluye:**
  - Entradas: Mis solicitudes (todos), Aprobaciones (`any_admin`), Inventario (todos, alcance por rol), Conectores (`admin`); "Plataformas" pasa a mostrarse como Catálogo según DIS-013
  - Componente `RequireRole` en `components/require-role.tsx`
  - Rutas `/requests`, `/approvals`, `/inventory`, `/admin/connectors`
- **No incluye:**
  - Menú móvil (deuda 8: se registra como sugerencia o la toma DIS-011/fase 4)
  - Contenido de las pantallas

## Archivos previstos
- `frontend/src/components/app-shell.tsx` (solo `NAV`)
- `frontend/src/components/require-role.tsx`
- `frontend/src/app/{requests,approvals,inventory,admin/connectors}/page.tsx`

## Reutilización
- `useSession`, `ErrorNote`/`EmptyNote` de `ui.tsx`

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `NAV` de `app-shell.tsx` | Navegación compartida | Todas las pantallas autenticadas | Pendiente |

## Criterios de aceptación
- [ ] Cada rol ve exactamente las entradas de la tabla de pantallas (prueba de componente)
- [ ] Una ruta sin permiso muestra el estado "sin permiso" y no llama a la API
- [ ] Criterios comunes web (FNC-037)

## Impacto cruzado
- Genera → DIS-013 a DIS-024
- Origen ← FNC-037
- Depende de → FNC-036, FNC-024, FNC-025, FNC-069

## Riesgos y reversión
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
