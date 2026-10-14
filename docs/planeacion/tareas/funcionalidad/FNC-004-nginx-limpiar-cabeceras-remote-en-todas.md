# FNC-004 — nginx: limpiar cabeceras Remote-* en todas las location, bloquear /api y /auth sin distinguir mayúsculas, TLS y cabeceras de seguridad

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | infra |
| **Agente** | devops |
| **Fase** | 5 |
| **Módulo / Área** | deploy |
| **Prioridad** | Crítica |
| **Estatus** | Propuesta |
| **Responsable** | |
| **Creada** | 2026-10-13 |
| **Inicio** | |
| **Finalizada** | |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-004-nginx-limpiar-cabeceras-remote-en-todas` |
| **Commits / PR** | |
| **Requiere migración BD** | Por definir |
| **Requiere auditor-seguridad** | Sí |

## Contexto
Suplantación por SSO: `location /` no hereda la limpieza de `Remote-*` (`deploy/nginx.conf.tmpl:70-72,115-120`); sin CSP, HSTS, X-Frame-Options ni TLS.

Origen (diagnóstico inicial, FNC-001):
- [`docs/seguridad/auditorias/2026-10-13-auditoria-inicial.md`](../../../seguridad/auditorias/2026-10-13-auditoria-inicial.md): SEG-04, SEG-15

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
- Depende de → Junto con FNC-005 y FNC-006 cierra SEG-04

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
