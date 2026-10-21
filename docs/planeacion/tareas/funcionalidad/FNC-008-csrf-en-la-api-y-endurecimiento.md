# FNC-008 — CSRF en la API y endurecimiento de la sesión (SameSite, Secure, remember, revocación al desactivar)

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 5 |
| **Módulo / Área** | auth |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Responsable** | |
| **Creada** | 2026-10-13 |
| **Inicio** | |
| **Finalizada** | |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-008-csrf-en-la-api-y-endurecimiento` |
| **Commits / PR** | |
| **Requiere migración BD** | Por definir |
| **Requiere auditor-seguridad** | Sí |

## Contexto
CSRF exento en todos los blueprints (`app/__init__.py:134-143`); `POST /backup` y `/users/purge` son explotables; sesión de 7 días y remember de 365 sin `Secure`.

Origen (diagnóstico inicial, FNC-001):
- [`docs/seguridad/auditorias/2026-10-13-auditoria-inicial.md`](../../../seguridad/auditorias/2026-10-13-auditoria-inicial.md): SEG-06, SEG-14

> **Regla de fases (2026-10-13):** esta corrección se hace en la fase 5 (seguridad final), **salvo** que una tarea anterior modifique este módulo: en ese caso la tarea debe dejarlo cumpliendo `docs/seguridad/LINEAMIENTOS.md` y corrige este hallazgo de paso.

## Objetivo
_Se completa al aprobar la tarea._

- Requisito antes de desplegar en staging o prod (auditorías de FNC-056 y FNC-058).
- Mientras tanto, `app/modules/api/csrf_provisional.py` (`escritura_del_portal`: JSON obligatorio y sin `Sec-Fetch-Site: cross-site`) protege `POST /access-requests` y `POST /access/<id>/revoke`; no reemplaza esta tarea.

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
| 2026-10-20 | Marcada como requisito antes de staging o prod (auditorías de FNC-056 y FNC-058) |

- 2026-10-21 (auditoría de seguridad DIS-019): `POST /users/directory`, `PUT /users/<id>` y `PUT /users/<id>/managed-areas` sin `escritura_del_portal`; cubrir con el CSRF definitivo.
