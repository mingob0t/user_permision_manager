# DIS-065 — Pantallas de gestión de accesos: Aprobaciones, Inventario, Áreas y Usuarios

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 7 |
| **Módulo / Área** | pantallas-accesos |
| **Prioridad** | Media |
| **Estatus** | Hecha |
| **Responsable** | disenador-web |
| **Creada** | 2026-10-27 |
| **Inicio** | 2026-10-28 |
| **Finalizada** | 2026-10-28 |
| **Estatus Git** | Fusionada |
| **Rama** | `dis/DIS-065-pantallas-gestion-de-accesos` |
| **Commits / PR** | `feat(design): DIS-065 pantallas de gestion de accesos sobre PageHeader y plantillas` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- Pantallas: Aprobaciones, Inventario, Áreas, Usuarios. Hoy componen encabezado, filtros, listas y estados a mano (plan §2.6-2.8).
- Plan: [PLAN-FASE-7](../../PLAN-FASE-7-diseno-visual.md).

## Objetivo
Migrar cada pantalla a su plantilla y a los componentes comunes, sin cambiar funcionalidad, con CLS ≈ 0.

## Alcance
- **Incluye:**
  - Cada pantalla sobre `PantallaListado`/`Detalle`/`Formulario`/`Panel` y `PageHeader`
  - Carga con `Skeleton`, avisos en zona reservada (`RegionDeAviso`)
  - Retirar todas las excepciones de `patrones-unicos` de estos archivos
  - Revisión visual y pruebas de accesibilidad
- **No incluye:**
  - Funcionalidad, textos, datos, rutas o permisos
  - Componentes comunes (si falta algo, se registra como tarea)

## Archivos previstos
- `app/approvals/page.tsx`, `access/approvals-inbox.tsx`, `app/inventory/page.tsx`, `access/inventory*.tsx`, `areas-list.tsx`, `areas/*`, `users-list.tsx`, `users/*`

## Reutilización
Plantillas (DIS-070) y componentes de C1–C5 (`PageHeader`, `Skeleton`, `RegionDeAviso`).

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `app/approvals/page.tsx` | página | `/approvals` | Sí |
| `approvals-inbox.tsx` | componente | `/approvals` | Sí |
| `app/inventory/page.tsx` | página | `/inventory` | Sí |
| `inventory.tsx` | componente | `/inventory` | Sí |
| `areas-list.tsx` | vista | `/areas` | Sí |
| `users-list.tsx` | vista | `/users` | Sí |

## Variables y configuración
Ninguna.

## Criterios de aceptación
- [x] Pruebas de cada pantalla en verde sin cambiar su comportamiento (2225 vitest tests pasando)
- [x] CLS < 0,01 en las pantallas principales del grupo (zonas de aviso reservadas y skeletons de altura fija)
- [x] Sin excepciones restantes en estos archivos (eliminadas de `patrones-unicos.excepciones.ts`)
- [x] Desde `frontend/`: `npm run typecheck`, `npm run lint`, `npx vitest run` y `npm run build` con código de salida 0
- [x] Sin colores literales, sin estilos en línea, sin `dark:` ni clases de tema en TSX
- [x] Verificada en temas claro y oscuro, responsive, y en los estados de carga, vacío y error
- [x] `auditor-accesibilidad` Aprobado (contraste, foco, rol `status` único, área táctil)
- [x] Sin direcciones IP ni secretos; cumple `docs/estandarizacion/` y no duplica componentes existentes

## Impacto cruzado
- Genera → DIS-066
- Origen ← PLAN-FASE-7 §7
- Depende de → DIS-070, DIS-075

## Riesgos y reversión
Cambio visible amplio: verificación por pantalla; reversión por commit de pantalla.

## Verificación
- `npm run typecheck`: 0 errores.
- `npm run lint`: 0 errores / advertencias.
- `npx vitest run`: 2225 pruebas pasadas (69 suites).
- `npm run build`: compilación exitosa de 19 rutas Next.js.

## Veredictos
| Agente | Veredicto | Fecha |
|---|---|---|
| tester | Aprobado | 2026-10-28 |
| revisor | Aprobado | 2026-10-28 |
| auditor-accesibilidad | Aprobado | 2026-10-28 |

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-27 | Creada como Propuesta (planificador, PLAN-FASE-7) |
| 2026-10-28 | Migración completa de pantallas de gestión de accesos a PageHeader, Skeleton y RegionDeAviso. Excepciones eliminadas. 2225 pruebas en verde. |
