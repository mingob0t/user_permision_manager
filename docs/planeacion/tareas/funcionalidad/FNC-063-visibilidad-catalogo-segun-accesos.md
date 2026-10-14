# FNC-063 — Visibilidad de plataformas y acceso a ellas según los accesos otorgados

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | authz |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-063-visibilidad-catalogo-segun-accesos` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (autorización compartida) |

## Contexto
- `scoped_platforms` (`app/authz.py:110`) filtra por las áreas del usuario (`user_areas`) e ignora los accesos; `user_platforms` se edita pero no limita (deuda 13, hallazgo 16 del diagnóstico: "se resuelve en el gestor de accesos")
- Requerimientos: F-SOL-01, F-ACC-01, pantallas "Inicio" y "Catálogo"

## Objetivo
- Que "mis plataformas" (catálogo para abrir, favoritos, visitas) se base en accesos `activo` según P4, separado del catálogo para solicitar (FNC-056)

## Alcance
- **Incluye:**
  - `scoped_platforms` y `can_access_platform` consideran accesos activos (y las plataformas de las áreas que administra un admin)
  - Comportamiento de `user_areas` según P4
- **No incluye:**
  - Catálogo para solicitar (FNC-056)
  - Retirar `user_platforms` (FNC-065)

## Archivos previstos
- `app/authz.py`
- `tests/authz/`

## Reutilización
- Modelo de FNC-054

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `scoped_platforms`, `can_access_platform` | Funciones de autorización | `GET /platforms`, `/favorites`, `POST /platforms/<id>/visit` y `/favorite`, `GET /stats` (`routes.py`, 6 usos), `crud.py` (2 usos); pantallas Panel, Plataformas, Favoritos | Pendiente |

## Criterios de aceptación
- [ ] Un usuario sin acceso activo no ve la plataforma en `GET /platforms` ni puede marcarla favorita (prueba)
- [ ] Un acceso `revocado` o `fallido` no da visibilidad (prueba)
- [ ] Las pruebas de alcance de FNC-021 siguen en verde o se actualizan con motivo
- [ ] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-054, Respuesta a P4

## Riesgos y reversión
- Usuarios que hoy ven plataformas por pertenecer al área dejan de verlas si no tienen acceso: plan de transición en P4/FNC-065.
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
