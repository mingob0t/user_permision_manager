# FNC-066 — Resumen del inicio por rol: pendientes, accesos y solicitudes

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | estadisticas |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-066-resumen-inicio-por-rol` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (exposición de datos por rol) |

## Contexto
- La tabla de pantallas pide un Inicio distinto por rol (usuario: mis accesos y solicitudes; admin: pendientes y resumen de sus áreas; superadmin: global)
- `GET /stats` (`routes.py`) solo da contadores y visitas
- Requerimientos: Pantalla "Inicio" de REQUERIMIENTOS §4

## Objetivo
- Exponer `GET /home/summary` con los contadores por rol, sin tocar `GET /stats`

## Alcance
- **Incluye:**
  - Usuario: accesos activos, solicitudes por estado
  - Admin: pendientes de sus áreas, accesos fallidos de sus áreas
  - Superadmin: pendientes, fallidos y totales globales
- **No incluye:**
  - Gráficas nuevas
  - Cambiar `GET /stats`
  - Pantalla (DIS-024)

## Archivos previstos
- `app/modules/home/api.py`
- `app/modules/home/services.py`
- `app/__init__.py` (registro)
- `tests/home/`

## Reutilización
- Consultas de FNC-054, FNC-056 y FNC-049

## Criterios de aceptación
- [ ] Cada rol recibe solo sus contadores (pruebas)
- [ ] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Genera → DIS-024
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-054, FNC-056, FNC-049, FNC-038
- Contrato → docs/contratos/inicio.md

## Riesgos y reversión
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
