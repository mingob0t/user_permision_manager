# FNC-027 — Retirar los blueprints heredados (44 rutas) y app/decorators.py

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 4 |
| **Módulo / Área** | global |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Responsable** | desarrollador |
| **Creada** | 2026-10-13 |
| **Inicio** | 2026-10-26 |
| **Finalizada** | |
| **Estatus Git** | Commit local en la rama de la tarea (sin push) |
| **Rama** | `fnc/FNC-027-retirar-blueprints-heredados` |
| **Commits / PR** | |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
7 blueprints solo redirigen o devuelven 410 (`app/modules/*/routes.py`, `app/__init__.py:127-143`).

Origen (diagnóstico inicial, FNC-001):
- [`docs/estandarizacion/auditorias/2026-10-13-auditoria-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-auditoria-inicial.md): H-01

## Objetivo
Retirar los siete blueprints heredados de NEXUS (44 rutas), sus registros y exenciones de CSRF, y `app/decorators.py`. Lo retirado responde `404`.

## Alcance
- **Incluye:** los siete `routes.py` heredados, su registro y exención de CSRF en `create_app`, `login_view`, `app/decorators.py`, el bloque `/auth/` de Nginx, pruebas, matriz y guardia, documentación.
- **No incluye:** `frontend/src` y `frontend/next.config.ts` (carril web; ver propuesta FNC-118).

## Criterios de aceptación
- [x] Hallazgo H-01 corregido y verificado
- [x] Prueba de regresión que primero falla (`tests/test_rutas_retiradas.py`: 92 fallaban antes de retirar)
- [x] Pruebas mínimas ejecutadas (ver Verificación)
- [x] Cumple `docs/estandarizacion/`; elimina D-01 y D-02 del catálogo
- [x] Sin direcciones IP ni secretos

## Impacto cruzado
- Depende de → Antes de FNC-020

## Decisiones
- **404, sin 410 para clientes viejos** (decisión del orquestador, pendiente de validar en la prueba de concepto). Motivo: el frontend solo llama a `/api/v1` (verificado con búsqueda en `frontend/src`) y Nginx es el único otro cliente; no hay integraciones externas conocidas. Un 410 obligaría a conservar el blueprint. El 410 `endpoint_retirado` de `/api/v1` (FNC-065) no se toca.
- **`platform_access_required` se conserva** en `app/authz.py`: solo `app/decorators.py` lo reexportaba, pero `authz` lo define, está documentado y probado en su módulo; borrarlo es otra decisión (sin uso en rutas desde FNC-063). Decisión del orquestador (pendiente de validar en la prueba de concepto).
- **`_deny` (authz) siempre devuelve 403 JSON**: su rama HTML hacía `url_for('core.index')`, que dejaría de existir y habría lanzado `BuildError`. Toda ruta protegida es de `/api/v1`, así que el comportamiento observable no cambia. Se quitó `_wants_json` (sin otro uso).
- **Nginx:** se retiró `location /auth/` (solo servía rutas heredadas); `/auth/*` pasa al frontend.
- **`login_manager.login_view`** se quitó: el `unauthorized_handler` propio nunca la usaba.
- `FRONTEND_URL` se conserva (la usa el `unauthorized_handler`); solo cambió su descripción (HISTORIAL.md).
- Sin plantillas ni estáticos que retirar (`template_folder=None`, `static_folder=None`).

## Usos revisados antes de borrar
- Rutas/código: solo `app/__init__.py` importaba los siete blueprints; `app/authz.py` usaba `url_for('core.index')`.
- Frontend: `frontend/src` solo llama a `/api/v1/...` (`lib/api.ts`); ninguna llamada real a las rutas retiradas. `frontend/next.config.ts` tiene un `rewrite` de `/auth/:path*` al backend: queda inerte (pasaría a 404); no se toca (propuesta FNC-118).
- Nginx (`deploy/`): `location /auth/`, retirado. Scripts de `deploy/` y README usan `/api/v1/auth/context`.
- Pruebas: `test_rutas_heredadas.py` (eliminada, sustituida), `test_csrf.py` (prueba heredada eliminada), `matriz_proteccion.py` (`BLUEPRINTS_HEREDADOS` eliminada), `test_guardia_rutas.py` (ahora exige cero rutas fuera de `/api/v1`).

## Verificación
- Regresión primero en rojo: `venv/bin/python -m pytest tests/test_rutas_retiradas.py` con los blueprints aún presentes: 92 failed, 2 passed (fallaban las 90 de rutas con y sin sesión, las rutas fuera de `/api/v1` y `app.decorators` importable; pasaban solo los dos conteos). La prueba del 403 JSON de `_deny` (petición con `Accept: text/html`) no se vio fallar de forma aislada: tras quitar los blueprints sin tocar `authz`, la app ni siquiera arrancaba; pasa con el cambio.
- `venv/bin/python -m pytest -q -p no:cacheprovider` (suite completa tras el cambio): **2335 passed, 15 xfailed** en 18 min 9 s, código de salida 0. Los 15 xfail son los previos (SEG-xx con su tarea).
- No verificado: el despliegue real con Nginx (la plantilla se edita sin ejecutar `install.sh`); el frontend (typecheck, lint, vitest) no se ejecutó porque no se tocó; revisor y auditorías no lanzados por indicación.

## Impacto en elementos compartidos
Salida de `impacto.py`:

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `can_manage_user` | función | `app/authz.py` | `access/api.py`, `access/rules.py`, `access_requests/approvals.py`, `api/crud.py`, `api/routes.py`, `audit/api.py`, `tests/test_alcance_por_area.py` | app/modules, tests | ☐ |

Lectura: la herramienta marca `can_manage_user` por estar en `app/authz.py`, pero su código no cambió. Lo realmente modificado en `authz.py` es `_deny` (privada, la usan `admin_required`, `any_admin_required`, `area_admin_required`, `platform_access_required` y `platform_manage_required`, es decir, todos los endpoints protegidos de `/api/v1`): ahora siempre 403 JSON; ya lo era para toda ruta de API. Validar: un 403 de cualquier pantalla del frontend.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-26 | Aprobada en modo autónomo; implementada y en revisión (rama `fnc/FNC-027-retirar-blueprints-heredados`) |
