# FNC-035 — Depurar documentación obsoleta (business_rules, ARCHITECTURE, README raíz, deploy/README)

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | infra |
| **Agente** | devops |
| **Fase** | 6 |
| **Módulo / Área** | docs |
| **Prioridad** | Baja |
| **Estatus** | En revisión |
| **Responsable** | devops |
| **Creada** | 2026-10-13 |
| **Inicio** | 2026-10-27 |
| **Finalizada** | |
| **Estatus Git** | Commit local, sin push |
| **Rama** | `fnc/FNC-035-depurar-documentacion` |
| **Commits / PR** | |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
Documentos que contradicen el código; ya marcados como parcialmente obsoletos.

Origen (diagnóstico inicial, FNC-001):
- [`docs/estandarizacion/auditorias/2026-10-13-auditoria-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-auditoria-inicial.md): H-18
- [`docs/backend/README.md`](../../../backend/README.md): discrepancias

## Objetivo
Que ningún documento contradiga el sistema actual (p. ej. `business_rules.md` prohibía SSH y `/api/v1`, y hoy existen).

## Alcance
- **Incluye:** `docs/business_rules.md`, `docs/ARCHITECTURE.md`, `README.md` raíz, `deploy/README.md` y las referencias a ellos.
- **No incluye:** código; versión de Node en `deploy/` y Dockerfile (FNC-073); documentos-foto (diagnóstico y auditorías).

## Criterios de aceptación
- [x] Hallazgos de origen corregidos y verificados (H-18 y discrepancias de `deploy/README.md` en `ENTORNOS.md`)
- [x] Prueba de regresión que primero falla: no aplica (solo documentación)
- [x] Pruebas mínimas: búsqueda de enlaces rotos y `validar_proyecto.py` (ver Verificación)
- [x] Cumple `docs/estandarizacion/` y no duplica: las `SMTP_*` remiten a `VARIABLES.md`
- [x] Sin direcciones IP ni secretos en los documentos tocados

## Decisión por archivo
Todas: decisión del orquestador (pendiente de validar en la prueba de concepto).

| Archivo | Decisión | Motivo | Dónde vive lo vigente |
|---|---|---|---|
| `docs/business_rules.md` | Retirado (`git rm`) | Prohibía `/api/v1`, SSH y exigía Docker; contraseña obligatoria, paginación DataTables y mensaje de área ya no aplican | `docs/REQUERIMIENTOS.md`; baja de áreas (`409 area_con_plataformas`) y `PUT /areas/<id>/users` en `docs/backend/README.md` §4.3 y `docs/contratos/areas-y-roles.md`; conector SSH en `docs/backend/README.md` §5 |
| `docs/ARCHITECTURE.md` | Retirado (`git rm`) | Dos roles, `AccessRequests`, Jinja2 y slugs inexistentes; lo vigente duplicaba otros documentos | `docs/backend/README.md` §1–3, `docs/frontend/README.md` §1, ADR-001 |
| `README.md` (raíz) | Reescrito | Describía NEXUS, enlazaba los retirados, `assets/` y `templates/` que no existen y un roadmap ajeno | Qué es, estado de fases (fase 5 en pausa, no exponer), desarrollo, pruebas, índice de documentos |
| `deploy/README.md` | Actualizado | Instalación manual con `deploy/nexus-*.service` y `deploy/nginx-nexus.conf` inexistentes; IPs literales (loopback y un rango privado en `--no-proxy`); bloque `SMTP_*` duplicado de `VARIABLES.md` | Plantillas `*.tmpl` con destino; `loopback` y dominio; remisión a `VARIABLES.md`; aviso de no exponer antes de la fase 5 |
| `docs/decisiones/ADR-001-stack.md` | Referencia ajustada | Remitía a la nota de los retirados | Nota de retiro con los documentos vigentes |
| `docs/operacion/ENTORNOS.md` | Sección de discrepancias marcada como corregida | Las dos discrepancias se resolvieron aquí | — |
| `docs/README.md` | Tres filas al índice (backend, frontend, contratos) | No enlazaba esos documentos (auditoría inicial, H-18) | — |
| `docs/DIAGNOSTICO-INICIAL.md`, `docs/estandarizacion/auditorias/2026-10-13-auditoria-inicial.md` | Sin cambio | Documentos-foto; solo mencionan los nombres, no enlazan | — |

**Node (FNC-073):** se dejaron las cifras actuales: README raíz «Node 18.18 o superior (se recomienda 22 LTS)»; `deploy/README.md` «Node ≥ 18.18» y «Node 22».

## Verificación
| Comando | Resultado |
|---|---|
| `grep -rn "business_rules\|ARCHITECTURE\.md"` en `docs/`, `README.md`, `deploy/`, `frontend/` | Solo menciones en la ficha, el tablero, el ADR-001 (nota de retiro) y los dos documentos-foto; ningún enlace |
| Script de enlaces relativos `](…)` en los 5 Markdown tocados | 0 rotos |
| `grep` de IPv4 en `README.md` y `deploy/README.md` | 0 |
| `validar_proyecto.py` | 1 error y 3 avisos, todos previos (en `develop`: 1 error y 2 avisos; el aviso extra «no hay carpeta logs/» es del worktree): `.gitignore` sin `logs/`, `NODE_ENV`/`TZ` fuera de `.env.example`, IP en `deploy/install.sh` |
| Pre-commit del proyecto (al hacer commit) | Ver bitácora |

No verificado: los comandos del README no se ejecutaron de punta a punta (se tomaron de `docs/backend/README.md` §6, `docs/frontend/README.md` §7 y `package.json`).

## Impacto en elementos compartidos
`impacto.py` (contra `develop`): **ninguno detectado** (10 archivos cambiados, solo documentación).

## Hallazgos fuera de alcance (para registrar en la base)
- `.gitignore` no ignora `logs/` (error de `validar_proyecto.py`, previo).
- `NODE_ENV` y `TZ` usadas en el código y ausentes de `.env.example`.
- IP de loopback en `deploy/install.sh` (lista `no_proxy` por defecto).

## Impacto cruzado
- Depende de → —

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-27 | Aprobada en modo autónomo; En curso (devops) |
| 2026-10-27 | Retirados `business_rules.md` y `ARCHITECTURE.md`; README raíz reescrito; `deploy/README.md` actualizado. En revisión |
