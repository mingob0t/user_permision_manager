# DIS-024 — Inicio por rol

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | dashboard |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `dis/DIS-024-inicio-por-rol` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- El Panel (`dashboard.tsx`) muestra contadores y visitas iguales para todos; la tabla de pantallas pide un Inicio por rol
- Requerimientos: Pantalla "Inicio" de REQUERIMIENTOS §4

## Objetivo
- Agregar al inicio el resumen por rol de FNC-066 con accesos directos (Mis solicitudes, Aprobaciones, ejecuciones fallidas)

## Alcance
- **Incluye:**
  - Bloque de resumen en componente propio, encima de lo existente
  - Usa `usePolling` de FNC-071 (ADR-006): refresco con el intervalo de la preferencia del usuario, en pausa con la pestaña oculta.
- **No incluye:**
  - Corregir la gráfica (DIS-003)
  - Quitar contenido existente

## Archivos previstos
- `frontend/src/components/home/role-summary.tsx`
- `frontend/src/components/dashboard.tsx` (importación)

## Reutilización
- `StatTile`, `Card` de `ui.tsx`, `usePolling`

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `dashboard.tsx` | Pantalla | `/` | Pendiente |

## Criterios de aceptación
- [ ] Cada rol ve sus contadores y enlaces
- [ ] Criterios comunes de diseño (FNC-037)

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-024, FNC-025, FNC-069, FNC-071, FNC-066
- Contrato → docs/contratos/inicio.md

## Riesgos y reversión
- Puede avanzar con los datos simulados de FNC-069; se integra después del backend.
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
