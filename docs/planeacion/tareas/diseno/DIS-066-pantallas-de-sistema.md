# DIS-066 — Pantallas de sistema: Administrar plataformas, Conectores, Ejecuciones, Auditoría e historiales, Ajustes

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 7 |
| **Módulo / Área** | pantallas-sistema |
| **Prioridad** | Media |
| **Estatus** | Hecha |
| **Responsable** | disenador-web |
| **Creada** | 2026-10-27 |
| **Inicio** | 2026-10-28 |
| **Finalizada** | 2026-10-28 |
| **Estatus Git** | Fusionada |
| **Rama** | `dis/DIS-066-pantallas-de-sistema` |
| **Commits / PR** | `feat(design): DIS-066 pantallas de sistema sobre PageHeader y plantillas` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- Pantallas: Administrar plataformas, Conectores, Ejecuciones, Auditoría, Historiales, Ajustes. Hoy componen encabezado, filtros, listas y estados a mano (plan §2.6-2.8).
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
- `platform-admin.tsx`, `platforms/*`, `app/admin/connectors/page.tsx`, `connectors/*`, `app/admin/jobs/page.tsx`, `audit-log.tsx`, `audit/*`, `settings-panel.tsx`, `settings/*`

## Reutilización
Plantillas (DIS-070) y componentes de C1–C5 (`PageHeader`, `Skeleton`, `RegionDeAviso`).

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `platform-admin.tsx` | vista | `/admin/platforms` | Sí |
| `app/admin/connectors/page.tsx` | página | `/admin/connectors` | Sí |
| `app/admin/jobs/page.tsx` | página | `/admin/jobs` | Sí |
| `audit-log.tsx` | vista | `/audit` | Sí |
| `platform-audit-history.tsx` | vista | `/audit/platforms/[id]` | Sí |
| `user-audit-history.tsx` | vista | `/audit/users/[id]` | Sí |
| `settings-panel.tsx` | vista | `/settings` | Sí |

## Variables y configuración
Ninguna.

## Criterios de aceptación
- [x] Pruebas de cada pantalla en verde sin cambiar su comportamiento (2225 vitest tests pasando)
- [x] CLS < 0,01 en las pantallas principales del grupo (zonas reservadas y skeletons con altura fija)
- [x] Sin excepciones restantes en estos archivos (eliminadas de `patrones-unicos.excepciones.ts`)
- [x] Desde `frontend/`: `npm run typecheck`, `npm run lint`, `npx vitest run` y `npm run build` con código de salida 0
- [x] Sin colores literales, sin estilos en línea, sin `dark:` ni clases de tema en TSX
- [x] Verificada en temas claro y oscuro, responsive, y en los estados de carga, vacío y error
- [x] `auditor-accesibilidad` Aprobado (contraste, foco, rol `status` único, área táctil)
- [x] Sin direcciones IP ni secretos; cumple `docs/estandarizacion/` y no duplica componentes existentes

## Impacto cruzado
- Genera → DIS-067
- Origen ← PLAN-FASE-7 §7
- Depende de → DIS-070, DIS-075, DIS-053

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
| 2026-10-28 | Migración completa de pantallas de sistema a PageHeader, Skeleton y RegionDeAviso. Excepciones eliminadas. 2225 pruebas en verde. |
