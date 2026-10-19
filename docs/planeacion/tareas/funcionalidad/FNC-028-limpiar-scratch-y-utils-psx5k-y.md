# FNC-028 — Limpiar scratch/ y utils/ (PSX5K) y adoptar Alembic con las migraciones 001-004

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 4 |
| **Módulo / Área** | bd |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Responsable** | |
| **Creada** | 2026-10-13 |
| **Inicio** | |
| **Finalizada** | |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-028-limpiar-scratch-y-utils-psx5k-y` |
| **Commits / PR** | |
| **Requiere migración BD** | Por definir |
| **Requiere auditor-seguridad** | No |

## Contexto
15 scripts en `scratch/` y 16 en `utils/`, restos de PSX5K; migraciones SQL sueltas sin control; `nexus_structure.sql` y `seed_users.py` obsoletos.

Origen (diagnóstico inicial, FNC-001):
- [`docs/estandarizacion/auditorias/2026-10-13-auditoria-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-auditoria-inicial.md): H-07, H-08
- [`docs/backend/README.md`](../../../backend/README.md): migraciones

## Objetivo
_Se completa al aprobar la tarea._

## Alcance
- **Incluye:** lo descrito en el contexto.
- **No incluye:** _se precisa al aprobar._

## Criterios de aceptación
- [ ] Hallazgos de origen corregidos y verificados
- [ ] Prueba de regresión que primero falla (si corrige un defecto)
- [ ] Pruebas mínimas del lineamiento de pruebas, ejecutadas
- [ ] Cumple `docs/estandarizacion/` y no duplica código existente
- [ ] Sin direcciones IP ni secretos

## Impacto cruzado
- Depende de → —

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-18 | FNC-043 retiró `validate_ldap_connection`: `utils/test_ldap.py` y `utils/nexus_health.py` la importan (ya fallaban: la llamaban sin argumentos); limpiar o pasar a `ClienteDirectorio` aquí |
