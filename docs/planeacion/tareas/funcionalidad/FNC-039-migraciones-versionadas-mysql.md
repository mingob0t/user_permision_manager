# FNC-039 — Migraciones versionadas de MySQL para la fase 3 (según ADR-002)

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | bd |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-039-migraciones-versionadas-mysql` |
| **Requiere migración BD** | Sí |
| **Requiere auditor-seguridad** | No |

## Contexto
- Los cambios de esquema se aplican a mano desde `utils/migrations/` sin registro de cuáles se aplicaron, y `db.create_all()` (`app/__init__.py`) no altera tablas existentes (`docs/backend/README.md` §7)
- La fase 3 agrega columnas a `platforms`, `audit_logs` y `auth_config`, y cinco tablas nuevas; sin control de versiones no es repetible en staging y producción
- Además, `004_drop_access_requests.sql` borra una tabla `access_requests`: las tablas nuevas **no** deben llamarse así
- Requerimientos: RNF-04

## Objetivo
- Dejar un mecanismo de migraciones versionado y repetible (el que decida ADR-002) con la línea base del esquema actual, para que cada tarea de la fase agregue su migración

## Alcance
- **Incluye:**
  - Mecanismo elegido en ADR-002 (recomendado: Alembic con Flask-Migrate) y su línea base del esquema actual de MySQL
  - Registro de las migraciones heredadas 001 a 004 como ya aplicadas o reproducidas
  - Comando documentado para aplicar y revertir en dev, staging y producción
  - Convención de nombres de tablas nuevas (prefijo `platform_access_*`, nunca `access_requests`)
- **No incluye:**
  - Retirar `db.create_all()` ni el admin semilla de `create_app()` (FNC-003, FNC-028, fase 4/5) salvo que ADR-002 lo exija
  - Limpiar `scratch/` y `utils/` (FNC-028)
  - Tablas de la fase 3 (cada tarea agrega la suya)

## Hallazgos de seguridad que absorbe
- Adelanta la parte "adoptar Alembic" de FNC-028 si ADR-002 lo aprueba; FNC-028 conserva la limpieza de `scratch/` y `utils/`.

## Archivos previstos
- `migrations/` (o la carpeta que fije ADR-002)
- `requirements.txt` (solo la dependencia de migraciones)
- `docs/backend/README.md` §7
- `docs/operacion/RELEASES.md` (paso de migración en el despliegue)

## Reutilización
- `db` de Flask-SQLAlchemy y los modelos existentes como fuente de la línea base

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `requirements.txt` | Dependencias | Backend completo, `deploy/install.sh` | Pendiente |
| Esquema de la BD | Datos | Todos los módulos | Pendiente |

## Variables y configuración
- Ninguna nueva prevista; si el mecanismo requiere una, se registra.

## Criterios de aceptación
- [ ] Migración de línea base aplicada en una BD MySQL de prueba vacía y en una copia con datos heredados, sin pérdida
- [ ] Bajada (downgrade) probada
- [ ] Prueba automatizada que verifica que el esquema de los modelos y el de las migraciones coinciden
- [ ] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Genera → Base de FNC-043, FNC-046, FNC-047, FNC-048, FNC-049, FNC-050, FNC-054, FNC-056, FNC-065
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, ADR-002 aceptado

## Riesgos y reversión
- Desfase entre `create_all()` y las migraciones: se documenta el orden (migrar primero) y se prueba en BD vacía.
- Reversión: bajar a la línea base; respaldo de la BD antes de aplicar (docs/operacion/RESPALDOS.md).

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
