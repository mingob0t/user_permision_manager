# FNC-003 — Eliminar credenciales por defecto y crear el primer superadmin con un comando explícito

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 5 |
| **Módulo / Área** | auth |
| **Prioridad** | Crítica |
| **Estatus** | Propuesta |
| **Responsable** | |
| **Creada** | 2026-10-13 |
| **Inicio** | |
| **Finalizada** | |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-003-eliminar-credenciales-por-defecto-y-crear` |
| **Commits / PR** | |
| **Requiere migración BD** | Por definir |
| **Requiere auditor-seguridad** | Sí |

## Contexto
`nexus123` para todo usuario sin contraseña (`app/modules/api/crud.py:283`), superadmin automático `admin/admin123` (`app/__init__.py:160-167`, `utils/nexus_structure.sql`, `utils/emergency_reset.py`); el login local no exige `auth_source=local`.

Origen (diagnóstico inicial, FNC-001):
- [`docs/seguridad/auditorias/2026-10-13-auditoria-inicial.md`](../../../seguridad/auditorias/2026-10-13-auditoria-inicial.md): SEG-02, SEG-03
- [`docs/estandarizacion/auditorias/2026-10-13-auditoria-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-auditoria-inicial.md): H-07

> **Regla de fases (2026-10-13):** esta corrección se hace en la fase 5 (seguridad final), **salvo** que una tarea anterior modifique este módulo: en ese caso la tarea debe dejarlo cumpliendo `docs/seguridad/LINEAMIENTOS.md` y corrige este hallazgo de paso.

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
| 2026-10-19 | SEG-02 cerrado por FNC-077 (En revisión): sin `nexus123` en `POST /users`, login local solo cuenta de emergencia y `auth_source=local`; xfail retirado. Queda SEG-03 (`admin/admin123` en `create_app`, SQL y `utils/`) |
