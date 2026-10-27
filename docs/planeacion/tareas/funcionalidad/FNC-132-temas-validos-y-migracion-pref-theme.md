# FNC-132 — Preferencias: `TEMAS_VALIDOS` a sistema, claro y oscuro, y migración 0012 de `pref_theme`

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 7 |
| **Módulo / Área** | preferencias |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Responsable** | |
| **Creada** | 2026-10-27 |
| **Inicio** | |
| **Finalizada** | |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-132-temas-validos-y-migracion-pref-theme` |
| **Commits / PR** | |
| **Requiere migración BD** | Sí (Alembic 0012, solo datos) |
| **Requiere auditor-seguridad** | Sí (migración de datos de usuario) |

## Contexto
- `app/modules/users/temas.py`: `TEMAS_VALIDOS` = sistema, claro, oscuro, esmeralda, obsidiana, rosa, violeta (FNC-122).
- `users.pref_theme` (migración 0011, `String(20)`, por defecto `sistema`) puede guardar los 4 temas que se retiran.
- El dueño pide solo claro y oscuro (plan §5).
- Plan: [PLAN-FASE-7](../../PLAN-FASE-7-diseno-visual.md).

## Objetivo
Aceptar solo `sistema`, `claro` y `oscuro`, y convertir los valores guardados sin perder la intención del usuario.

## Alcance
- **Incluye:**
  - `TEMAS_VALIDOS` = {`sistema`, `claro`, `oscuro`}
  - Migración `0012_temas_retirados.py`: `esmeralda`/`rosa` → `claro`; `obsidiana`/`violeta` → `oscuro`; otro valor fuera de la lista → `sistema`; idempotente; `downgrade` sin cambio de datos, documentado
  - Pruebas: `tests/test_migracion_0012.py` (cada valor, idempotencia, ninguno fuera de la lista tras `upgrade`) y `tests/users/test_tema_en_la_cuenta.py` (retirado → `422`)
  - `docs/backend/README.md` (tabla de endpoints y modelo)
- **No incluye:**
  - Cambios de columna o tipo
  - Frontend (DIS-054)
  - Otras preferencias
  - Lista blanca general (FNC-120)

## Archivos previstos
- `app/modules/users/temas.py`
- `migrations/versions/0012_temas_retirados.py` (nuevo)
- `tests/test_migracion_0012.py` (nuevo)
- `tests/users/test_tema_en_la_cuenta.py`
- `docs/backend/README.md`

## Reutilización
Patrón de `0011_tema_en_la_cuenta.py` (constantes fijas de la revisión, sin importar código de la app) y `tests/test_migracion_0011.py`.

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `TEMAS_VALIDOS` | constante | `users/preferencias_api.py` (`PUT /me/preferences`) | No |
| `users.pref_theme` (datos) | columna | `GET /me` (`api/routes.py`), selector de tema web (FNC-123) | No |

## Variables y configuración
Ninguna (lista de código, no configurable).

## Criterios de aceptación
- [ ] `PUT /me/preferences` con `esmeralda`, `obsidiana`, `rosa` o `violeta` → `422 validacion` con `fields.theme`; con `sistema`/`claro`/`oscuro` → 200
- [ ] Tras `alembic upgrade head`, ningún `pref_theme` fuera de la lista; la conversión es la del contrato
- [ ] `test_migraciones.py` (modelo = migraciones) en verde
- [ ] Pytest completo con código de salida 0 (salida a archivo y `echo $?`)
- [ ] `auditor-seguridad` Aprobado
- [ ] Prueba en MySQL/MariaDB real anotada o declarada pendiente con motivo
- [ ] Sin direcciones IP ni secretos
- [ ] `impacto.py` ejecutado y su tabla en esta ficha

## Impacto cruzado
- Genera → —
- Origen ← FNC-122, PLAN-FASE-7 §5
- Depende de → Contrato `docs/contratos/preferencias.md` aprobado; vinculada a DIS-054 (integrar juntas; desplegar web antes o junto)

## Riesgos y reversión
Un cliente web viejo que envíe un tema retirado recibe `422` (aviso de FNC-123). Reversión: `downgrade` no restaura los valores; respaldo previo de `users.pref_theme` si se quiere volver.

## Verificación
Pendiente (tarea en Propuesta).

## Veredictos
| Agente | Veredicto | Fecha |
|---|---|---|
| tester | | |
| revisor | | |
| auditor-seguridad | | |

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-27 | Creada como Propuesta (planificador, PLAN-FASE-7) |
