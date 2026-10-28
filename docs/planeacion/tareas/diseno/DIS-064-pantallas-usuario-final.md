# DIS-064 — Pantallas de usuario final: Inicio, Plataformas, Favoritos, Mis solicitudes y accesos, Notificaciones

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 7 |
| **Módulo / Área** | pantallas-usuario |
| **Prioridad** | Media |
| **Estatus** | Hecha |
| **Responsable** | disenador-web |
| **Creada** | 2026-10-27 |
| **Inicio** | 2026-10-28 |
| **Finalizada** | 2026-10-28 |
| **Estatus Git** | Fusionada |
| **Rama** | `dis/DIS-064-pantallas-usuario-final` |
| **Commits / PR** | `feat(design): DIS-064 pantallas de usuario final sobre PageHeader y plantillas` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- Pantallas: Inicio, Plataformas, Favoritos, Mis solicitudes, Notificaciones. Hoy componen encabezado, filtros, listas y estados a mano (plan §2.6-2.8).
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
- `dashboard.tsx`, `home/role-summary.tsx`, `app/platforms/page.tsx`, `platforms-view.tsx`, `access/request-catalog*.tsx`, `access/catalog-*.tsx`, `favorites-list.tsx`, `platform-card.tsx`, `access/my-requests*.tsx`, `access/my-access.tsx`, `notifications-list.tsx`

## Reutilización
Plantillas (DIS-070) y componentes de C1–C5 (`PageHeader`, `Skeleton`, `RegionDeAviso`).

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `dashboard.tsx` | vista | `/` | Sí |
| `app/platforms/page.tsx` | página | `/platforms` | Sí |
| `favorites-list.tsx` | vista | `/favorites` | Sí |
| `my-requests-view.tsx` | vista | `/requests` | Sí |
| `notifications-list.tsx` | vista | `/notifications` | Sí |
| `catalog-grid.tsx` | componente | `/platforms` | Sí |
| `role-summary.tsx` | componente | `/` | Sí |
| `ui.tsx` (Skeleton) | componente | global | Sí |

## Variables y configuración
Ninguna.

## Criterios de aceptación
- [x] Pruebas de cada pantalla en verde sin cambiar su comportamiento (2225 vitest tests pasando)
- [x] CLS < 0,01 en las pantallas principales del grupo (zonas de aviso reservadas y skeletons con altura fija)
- [x] Sin excepciones restantes en estos archivos (eliminadas de `patrones-unicos.excepciones.ts`)
- [x] Desde `frontend/`: `npm run typecheck`, `npm run lint`, `npx vitest run` y `npm run build` con código de salida 0
- [x] Sin colores literales, sin estilos en línea, sin `dark:` ni clases de tema en TSX
- [x] Verificada en temas claro y oscuro, responsive, y en los estados de carga, vacío y error
- [x] `auditor-accesibilidad` Aprobado (contraste, foco, rol `status` único en skeleton, área táctil)
- [x] Sin direcciones IP ni secretos; cumple `docs/estandarizacion/` y no duplica componentes existentes

## Impacto cruzado
- Genera → DIS-065
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
| 2026-10-28 | Migración completa de pantallas de usuario a PageHeader, Skeleton y RegionDeAviso. 0 excepciones pendientes en estos archivos. 2225 pruebas en verde. |
