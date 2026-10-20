# FNC-055 — Acceso automático de los admins a las plataformas de sus áreas

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | accesos |
| **Prioridad** | Alta |
| **Estatus** | Hecha |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Rama local, sin push |
| **Rama** | `fnc/FNC-055-acceso-automatico-admins` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (otorgamiento sin solicitud) |

## Contexto
- El admin "da de alta sus áreas y plataformas y tiene acceso automático a ellas" (REQUERIMIENTOS §2)
- Hoy no existe ningún otorgamiento automático
- Requerimientos: F-AREA-01, RF-03

## Objetivo
- Otorgar con origen `admin_de_area` el nivel que defina P6 (dueño: `usuario`) a cada admin de un área sobre cada plataforma `ldap` o `conector` de esa área: al crear la plataforma, al asignar el admin al área, y revocarlo según P6 al quitarlo

## Alcance
- **Incluye:**
  - Servicio `sync_area_admin_grants(area)` en el módulo de accesos, idempotente
  - Llamado desde el alta de plataforma (FNC-046), la asignación de admins (FNC-044) y el alta de área (FNC-045) mediante una función pública, sin lógica en esos módulos
  - Comportamiento al quitar un admin o mover una plataforma según P6
- **No incluye:**
  - Accesos de áreas ajenas (se solicitan, RF-03)
  - Endpoints o pantallas

## Archivos previstos
- `app/modules/access/area_admin_sync.py`
- Una llamada en los servicios de FNC-044, FNC-045 y FNC-046
- `tests/access/test_area_admin_sync.py`

## Reutilización
- `grant()`/`revoke()` de FNC-054

## Implementación
| Archivo | Cambio |
|---|---|
| `app/modules/access/area_admin_sync.py` (nuevo) | `sincronizar_plataforma`, `sincronizar_cuenta`, `otorgar_si_falta`, `revocar_si_ya_no_administra`, `administra`, `aprovisionable`; reutiliza `services.otorgar`/`revocar` |
| `app/modules/access/manejadores.py` | `al_exito`: otorgar confirmado de quien ya no administra el área → revocar |
| `app/modules/access/consultas.py` | `contar_vigentes_no_automaticos` |
| `app/modules/access/tipos.py` | `MOTIVO_RETIRO_ADMIN = 'ya_no_administra_el_area'` |
| `app/modules/platforms/estado.py` | Punto de extensión `accesos_que_impiden_mover` |
| `app/modules/platforms/api.py` | `create_platform` y `update_platform` (área, tipo o grupos) llaman a `sincronizar_plataforma`; el 409 por área ya no cuenta los automáticos |
| `app/modules/users/areas_administradas.py` | `asignar_areas_administradas` llama a `sincronizar_cuenta(cuenta, áreas agregadas)` |
| `app/modules/users/roles.py` | `cambiar_rol` llama a `sincronizar_cuenta` al dejar `admin_area`, tras `rol_cambiado` |
| `tests/access/test_area_admin_sync.py` (nuevo) | 18 pruebas |
| `tests/platforms/test_integracion_y_grupos.py` | Fixture `con_accesos` simula también `accesos_que_impiden_mover` |

- `create_area` (FNC-045) no llama: un área recién creada no tiene plataformas.
- Nombres: el contrato decía `sync_area_admin_grants(area)`; se implementó por plataforma y por cuenta (más acotado); contratos actualizados.
- Sin migración.

## Decisiones
- Dueño (2026-10-14, P6): nivel `usuario`; todos los admins del área, también en plataformas nuevas; al quitarle el área se revocan sus `admin_de_area` de esa área; el superadmin tiene acceso por defecto, no recibe automáticos ni entra a grupos LDAP. Auditoría: "admin X dio de alta la plataforma Y" y "sistema dio permisos de acceso a admin X". Respuesta registrada en `docs/contratos/README.md`.
- Decisiones del orquestador (pendientes de validar en la prueba de concepto):
  - Solo se otorga ante un evento (alta, área agregada, cambio de área, tipo o grupos): una revocación manual del superadmin no se deshace sola.
  - Solo se revoca un acceso `activo`; uno `en_proceso` se revoca al confirmarse (manejador). Uno `fallido` no da acceso; si se reintenta (FNC-062) se revoca al confirmarse.
  - Con un vigente en la plataforma (cualquier nivel u origen, o revocación en curso de nivel `usuario`) no se otorga otro.
  - Admin inactivo: no recibe. Plataforma `ldap` sin grupo de nivel `usuario` (heredada): no recibe; al completar grupos o cambiar tipo se sincroniza.
  - Cambiar el área con solo accesos automáticos ya no da 409: se resincronizan (anteriores → `revocando`, nuevos → `en_proceso`). Con accesos por solicitud, sigue 409. Tipo y grupos siguen dando 409 con cualquier vigente (FNC-085).
  - Degradar `admin_area` → `usuario` revoca como quitar todas las áreas.
  - Revocación con motivo `ya_no_administra_el_area` y actor `sistema`.

## Impacto en elementos compartidos
Salida de `python3 ~/.claude/agentes/herramientas/impacto.py`:

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `al_exito` | función | `app/modules/access/manejadores.py` | `tests/access/test_servicio.py` | tests/access | ☐ |
| `asignar_areas_administradas` | función | `app/modules/users/areas_administradas.py` | `app/modules/users/api.py` | app/modules | ☐ |
| `cambiar_rol` | función | `app/modules/users/roles.py` | `app/modules/api/crud.py` | app/modules | ☐ |

Agregado a mano (la herramienta no detecta rutas):

| Elemento modificado | Tipo | Usado en | ¿Validado? |
|---|---|---|---|
| `POST /platforms`, `PUT /platforms/<id>` | Endpoints | Pantalla de plataformas (DIS-017) | ☐ (respuesta sin cambios de forma; ahora el cambio de área con solo automáticos responde 200) |
| `PUT /users/<id>/managed-areas` | Endpoint | Pantalla de áreas (DIS-016) | ☐ (sin cambios de forma) |
| `PUT /users/<id>` (rol) | Endpoint | Pantalla de usuarios | ☐ (sin cambios de forma) |
| `platforms/estado.py` | Punto de extensión | `platforms/api.py`, `core/models.py` | ☐ |
| Contratos `plataformas-integracion` 1.1 y `areas-y-roles` 2.1 | Contrato | web (FNC-069) | ☐ |

## Criterios de aceptación
- [x] Crear una plataforma en un área con dos admins genera dos accesos `admin_de_area` (prueba)
- [x] Asignar un admin a un área con tres plataformas genera tres accesos (prueba)
- [x] Repetir la sincronización no duplica (prueba)
- [x] El superadmin no recibe accesos automáticos (P6) (prueba)
- [x] Quitar el área o degradar al admin revoca sus automáticos; mover la plataforma de área los resincroniza (pruebas)
- [ ] Criterios comunes backend (FNC-037): falta revisor y auditor-seguridad

## Verificación
| Comando | Resultado |
|---|---|
| `venv/bin/python -m pytest -q tests/access/test_area_admin_sync.py` sin la implementación (código de `app/` apartado con `git stash`) | 15 failed, 2 passed, exit 1 (las 2 que pasan son guardas: solicitud no se toca y 409 con solicitud) |
| Igual, con la implementación | 18 passed |
| `venv/bin/python -m pytest -q` (completo, antes de ajustar 2 pruebas) | 2 failed, 1229 passed, 15 xfailed, exit 1: fixture `con_accesos` (área) y `test_si_falla_la_auditoria_no_se_cambia_el_rol` (el `flush` de la sincronización antes de la auditoría); corregidos (fixture y orden: sincronizar tras auditar) |
| `venv/bin/python -m pytest -q` (completo, final) | 1231 passed, 15 xfailed, exit 0 (antes de la tarea: 1213 passed, 15 xfailed) |

- No verificado: con MySQL real ni con Redis/worker reales (cola falsa y proveedor simulado); concurrencia de dos sincronizaciones simultáneas (la BD lo impide con `uq_platform_access_grants_*` y el llamador revierte con 500).
- No se lanzaron revisor ni auditor-seguridad (indicación del orquestador): pendientes.

## Riesgos conocidos
- `DELETE /platforms/<id>` con accesos falla por FK (500): ahora casi toda plataforma de un área con admins tiene accesos → FNC-083.
- Cambiar grupos o tipo de una plataforma con admins responde siempre 409 → FNC-085.
- Desactivar una cuenta no revoca sus accesos → FNC-084.
- Plataformas y admins existentes al desplegar no reciben accesos hasta un evento → FNC-086.

## Impacto cruzado
- Origen ← FNC-037
- Genera → FNC-084, FNC-085, FNC-086
- Depende de → FNC-036, FNC-019, FNC-054, FNC-044, FNC-045, FNC-046, Respuesta a P6

## Riesgos y reversión
- Muchos trabajos al asignar un admin a un área grande: se encolan por lotes.
- Reversión: revertir la rama; los accesos creados quedan auditados.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-20 | Aprobada (modo autónomo) y En curso |
| 2026-10-20 | Implementada; contratos `plataformas-integracion` 1.1 y `areas-y-roles` 2.1; genera FNC-084, FNC-085, FNC-086. En revisión (pendientes revisor y auditor-seguridad) |

## Decisiones del dueño (2026-10-14)
- Nivel del acceso automático: `usuario`.
- Lo reciben todos los admins del área, también en plataformas nuevas.
- Al quitarle el área a un admin se revocan sus accesos `admin_de_area` de esa área.
- El superadmin no entra a los grupos LDAP.
