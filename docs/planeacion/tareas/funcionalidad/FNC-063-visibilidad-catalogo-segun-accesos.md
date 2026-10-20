# FNC-063 — Visibilidad de plataformas y acceso a ellas según los accesos otorgados

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | authz |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-063-visibilidad-plataformas` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (autorización compartida) |
| **Inicio** | 2026-10-20 |

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

## Archivos tocados
| Archivo | Cambio |
|---|---|
| `app/authz.py` | `scoped_platforms` por accesos `activo` (+ áreas administradas del admin); `can_access_platform` usa la misma query; docstring del módulo |
| `app/modules/access/consultas.py` | `plataformas_con_acceso_activo(usuario_id)` (subconsulta) |
| `app/modules/api/crud.py` | `PUT /users/<id>/platforms`: lo permitido se limita a `can_manage_platform` (un acceso propio del admin no da alcance) |
| `tests/authz/test_visibilidad_por_accesos.py` | 17 pruebas nuevas (12 funciones) |
| `tests/fabricas.py` | `crear_acceso` |
| `tests/test_alcance_por_area.py` | Fixture `alcance`: un acceso `activo` por usuario (motivo abajo) |
| `tests/matriz_proteccion.py` | `visit` y `favorite`: el `usuario` de la matriz (sin acceso) espera `404` |
| `tests/platforms/test_revision_seguridad.py` | El usuario del listado recibe un acceso `activo` |

## Respuesta a P4 y decisiones
| Tema | Valor aplicado | Fuente |
|---|---|---|
| Base de "mis plataformas" | Accesos `activo` (`platform_access_grants`); `en_proceso`, `fallido`, `revocando`, `revocado`, `fallo_revocacion` no dan visibilidad | P4 (contratos/README), criterios |
| `user_platforms` | No interviene en la visibilidad (ya no lo hacía); se sigue editando sin efecto hasta FNC-065 | P4 |
| `user_areas` sola | Ya no da visibilidad a un usuario | P4 |
| Superadmin | Todas las plataformas | Dueño (P6) |
| Admin de área | Plataformas de las áreas que administra, sin mirar el estado del acceso automático, más las de sus accesos `activo` | Dueño (FNC-055) |
| Acceso `activo` en un área a la que la cuenta ya no pertenece | No da visibilidad (P1; quitar un área no revoca el acceso) | Decisión del orquestador (pendiente de validar en la prueba de concepto) |
| Acceso automático del admin en `en_proceso`/`fallido` | El admin ve igual sus áreas (administra la plataforma) | Decisión del orquestador (pendiente de validar en la prueba de concepto) |
| `PUT /users/<id>/platforms` | Solo plataformas que el admin administra; ver una por acceso propio no basta (mínimo privilegio, SEC-AUTHZ-03) | Decisión del orquestador (pendiente de validar en la prueba de concepto) |
| Estado `Inactivo` de área o plataforma | Sin cambio (antes tampoco filtraba) | Fuera de alcance |

### Plan de transición (`user_platforms` → accesos)
1. FNC-063 (esta): la visibilidad sale solo de accesos `activo`. Los usuarios que veían plataformas por su área dejan de verlas hasta tener acceso.
2. Antes de desplegar en un entorno con usuarios: otorgar accesos por solicitud o masivamente (FNC-065, P4 dice que los de NEXUS se descartan; confirmar con el dueño si hace falta una carga inicial).
3. FNC-065: retirar `user_platforms`, `PUT /platforms/<id>/users` y `PUT /users/<id>/platforms`.

### Motivo del cambio en las pruebas de FNC-021
- 8 pruebas fallaron con la regla nueva: el usuario veía la plataforma de su área sin acceso. El fixture `alcance` ahora da a cada usuario un acceso `activo` a la plataforma de su área; las aserciones no cambian. Los casos sin acceso quedan en `tests/authz/`.
- Mismo motivo en otras 3: `test_url_heredada_no_https_sale_null_en_el_listado` (se le da acceso; la aserción no cambia) y la matriz de protección de `visit`/`favorite` para `usuario` (200 → 404: el actor de la matriz no tiene acceso; se le dejó así porque darle acceso rompería `POST /access-requests` → `409 nivel_vigente`).

## Reutilización
- Modelo de FNC-054

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `scoped_platforms`, `can_access_platform` | Funciones de autorización | `GET /platforms`, `/favorites`, `POST /platforms/<id>/visit` y `/favorite`, `GET /stats` (`routes.py`, 5 usos), `crud.py` `PUT /users/<id>/platforms`, `platform_access_required` (sin uso en rutas); pantallas Panel, Plataformas, Favoritos | Pruebas en verde; validar pantallas |
| `consultas.plataformas_con_acceso_activo` | Consulta (nueva) | `authz.scoped_platforms` | Sí |
| `tests/fabricas.crear_acceso` | Fábrica (nueva) | `tests/authz/`, `tests/test_alcance_por_area.py` | Sí |

Salida de `impacto.py` (contra `develop`):

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `alcance` | función | `tests/test_alcance_por_area.py` | `app/modules/access/api.py`, `app/modules/access/inventario.py`, `app/modules/access/rules.py`, `app/modules/api/auth.py`, `app/modules/api/routes.py`, `app/modules/audit/api.py`, `app/modules/audit/queries.py`, `app/modules/platforms/api.py` (+17) | app/modules, frontend/src, frontend/tests, tests, tests/access, tests/audit, tests/users | ☐ |
| `crear_usuario_de_rol` | función | `tests/fabricas.py` | `tests/conftest.py` | tests | ☐ |
| `scoped_platforms` | función | `app/authz.py` | `app/modules/api/routes.py` | app/modules | ☐ |

- `alcance`: falso positivo (coincide con la palabra "alcance"); el fixture solo lo usa su archivo.
- `crear_usuario_de_rol`: sin cambio; se agregó `crear_acceso` después en el mismo archivo.
- `scoped_platforms`: cambio real; afecta Panel, Plataformas y Favoritos de la web para el rol `usuario`.
- No los detecta la herramienta: `can_access_platform` (decorador `platform_access_required`, sin uso en rutas) y `PUT /users/<id>/platforms` (`crud.py`).

## Criterios de aceptación
- [x] Un usuario sin acceso activo no ve la plataforma en `GET /platforms` ni puede marcarla favorita (prueba)
- [x] Un acceso `revocado` o `fallido` no da visibilidad (prueba; también `en_proceso`, `revocando`, `fallo_revocacion`)
- [x] Las pruebas de alcance de FNC-021 siguen en verde o se actualizan con motivo (fixture actualizado, motivo arriba)
- [ ] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Origen ← FNC-037
- Genera → FNC-096 (exponer integración y `active_grants` en `GET /platforms` a quien administra, pedido por DIS-017)
- Depende de → FNC-036, FNC-019, FNC-054, Respuesta a P4

## Verificación
| Comando | Resultado real |
|---|---|
| `venv/bin/python -m pytest tests/authz -q` sin la implementación | 13 failed, 3 passed (regresiones fallan primero; `superadmin`, admin de sus áreas y cuenta inactiva ya pasaban) |
| Ídem tras implementar | 16 passed (17 con la prueba de `crud.py`) |
| `test_acceso_activo_del_admin_no_le_da_alcance_para_asignar` sin el cambio de `crud.py` | 1 failed; con el cambio, passed |
| `pytest tests/test_alcance_por_area.py` con la regla nueva y el fixture viejo | 8 failed (motivo arriba); con el fixture actualizado, 89 passed |
| Primer pytest completo | 3 failed, 1475 passed, 15 xfailed (código 1): matriz `visit`/`favorite` y listado de URL heredada; corregidas (motivo arriba) |
| `venv/bin/python -m pytest -q` (completo, final) | 1478 passed, 15 xfailed; código de salida 0 |

No verificado:
- Pantallas web (Panel, Plataformas, Favoritos) con un usuario real: sin navegador en esta tarea.
- MySQL: las pruebas usan SQLite; la consulta es `IN (subconsulta)` estándar.
- Sin migración.
- `revisor` y `auditor-seguridad` no se lanzaron (indicación del orquestador); quedan pendientes.

## Riesgos y reversión
- Usuarios que hoy ven plataformas por pertenecer al área dejan de verlas si no tienen acceso: plan de transición en P4/FNC-065.
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-20 | Aprobada por el orquestador (modo autónomo); En curso |
| 2026-10-20 | Implementada: visibilidad por accesos `activo`; FNC-021 actualizada con motivo; propuesta FNC-096. pytest completo en verde (salida 0). En revisión; pendientes revisor y auditor-seguridad |
