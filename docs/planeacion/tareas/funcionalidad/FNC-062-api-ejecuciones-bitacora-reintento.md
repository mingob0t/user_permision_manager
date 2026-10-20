# FNC-062 — API de ejecuciones: bitácora de aprovisionamiento y reintento manual

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | aprovisionamiento |
| **Prioridad** | Media |
| **Estatus** | En revisión |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Commit local en `fnc/FNC-062-api-ejecuciones`, sin push |
| **Rama** | `fnc/FNC-062-api-ejecuciones` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (acciones privilegiadas) |

## Contexto
- Las ejecuciones (FNC-049) tienen bitácora, pero nadie la ve; un acceso `fallido` tras agotar reintentos no tiene salida salvo revocar y volver a solicitar
- Requerimientos: F-CON-01

## Objetivo
- Exponer la bitácora de ejecuciones (por plataforma, usuario, estado) y el reintento manual según P10

## Alcance
- **Incluye:**
  - `GET /provisioning/jobs` con filtros y paginación; detalle con intentos
  - Alcance: superadmin todo; admin las de sus áreas (lectura)
  - `POST /provisioning/jobs/<id>/retry` para trabajos `fallido` (rol según P10)
- **No incluye:**
  - Cancelar trabajos (no pedido)
  - Pantalla (DIS-022, DIS-018)

## Archivos previstos
- `app/modules/provisioning/api.py`
- `app/__init__.py` (registro)
- `tests/provisioning/test_api.py`

## Reutilización
- Modelos y cola de FNC-049

## Nota de FNC-049 (2026-10-19)
- Reintento manual con `app.modules.provisioning.ejecucion.reabrir(trabajo, cfg)`: solo desde `fallido` (si no, `EstadoInvalido` → `409 estado_invalido`), conserva la bitácora y sube `max_attempts` en `PROVISIONING_MAX_ATTEMPTS`; no reinicia el contador. Un otorgar con una revocación posterior de su terna no se reabre (`EstadoInvalido` → 409; re-auditoría de FNC-049). Decisión del orquestador (pendiente de validar en la prueba de concepto). Commit y auditoría `ejecucion_reintentada` los hace FNC-062
- `status` incluye `cancelado` (otorgar dejado sin efecto por una revocación)

## Archivos tocados
- Nuevos: `app/modules/provisioning/api.py`, `consultas.py`, `serializacion.py`, `reintento.py`; `tests/provisioning/test_api.py`
- Modificados: `app/__init__.py` (registro), `provisioning/ejecucion.py` (`reabrir` condicional), `provisioning/queue.py` (`despertar_tras_commit`), `access/services.py` (`reabrir_acceso` condicional), `audit/parametros.py` (`leer_entero`), `tests/matriz_proteccion.py`
- Sin migración. Sin variables nuevas

## Decisiones
- P10 (dueño): reintento solo superadmin; el admin del área ve la bitácora de sus áreas
- Decisión del orquestador (pendiente de validar en la prueba de concepto): el área de un trabajo es su `area_id` (la de la plataforma al encolar); con el área borrada solo lo ve el superadmin
- Decisión del orquestador (pendiente de validar en la prueba de concepto): el reintento exige cuerpo JSON `{}` (`escritura_del_portal`, hasta FNC-008); cualquier campo → `400 campo_no_permitido`
- Decisión del orquestador (pendiente de validar en la prueba de concepto): `from`/`to` sin zona en hora local del proceso (como la auditoría), comparadas en UTC
- Decisión del orquestador (pendiente de validar en la prueba de concepto): `attempts[].error` se sanea otra vez al salir; no se envían `idempotency_key`, `locked_by` ni `locked_at`
- Concurrencia: `reabrir` y `reabrir_acceso` con `UPDATE … WHERE status = <fallido>`; el segundo reintento simultáneo → `409 estado_invalido`; una revocación confirmada a la vez no se pisa
- Otorgar con revocación posterior o acceso ya no fallido (p. ej. `revocado`) → 409, sin reabrir nada
- SEG-062-01/02 (auditor-seguridad): el reintento de un otorgar vuelve a pasar `access.rules.validar_otorgamiento` (actor de la sesión; sistema para `admin_de_area`): cuenta borrada, inactiva, ahora superadmin o fuera del área (P1) → 409. Trabajo sin `access_id` → 409
- SEG-062-03: `from`/`to` que desbordan al pasar a UTC (`0001-01-01`, `9999-12-31T23:59:59`) → `400 parametro_invalido`

## Criterios de aceptación
- [x] Matriz de permisos por rol (pruebas): 3 casos y 2 entradas 400 en `tests/matriz_proteccion.py`
- [x] Reintentar un trabajo no fallido responde 409 (prueba)
- [x] Los errores mostrados están saneados (prueba)
- [x] Criterios comunes backend (FNC-037): 401/403/404, formato de error, paginación, auditoría en la transacción

## Impacto cruzado
- Genera → DIS-022
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-049, FNC-038, Respuesta a P10
- Contrato → docs/contratos/conectores-y-ejecuciones.md

## Impacto en elementos compartidos
**⚠ Impacto en elementos compartidos** (comparado contra `develop`): este cambio toca 3 elemento(s) usados en otras secciones: app/modules, tests/access, tests/provisioning. Valida cada una antes de integrar.

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `encolar` | función | `app/modules/provisioning/queue.py` | `app/modules/provisioning/__init__.py`, `app/modules/provisioning/tipos.py`, `tests/access/test_area_admin_sync.py`, `tests/provisioning/conftest.py`, `tests/provisioning/test_encolado.py`, `tests/provisioning/test_ldap_provider.py` | app/modules, tests/access, tests/provisioning | ☐ |
| `reabrir` | función | `app/modules/provisioning/ejecucion.py` | `tests/access/test_servicio.py`, `tests/provisioning/test_orden_y_reserva.py`, `tests/provisioning/test_reauditoria.py` | tests/access, tests/provisioning | ☐ |
| `reabrir_acceso` | función | `app/modules/access/services.py` | `tests/access/test_servicio.py` | tests/access | ☐ |

- `encolar`: solo cambia la línea del aviso al worker por `despertar_tras_commit` (mismo efecto)
- `reabrir` / `reabrir_acceso`: misma firma y errores; ahora con `UPDATE` condicional. Sus pruebas existentes pasan
- `leer_entero` (nuevo, `audit/parametros.py`): aditivo, sin usos previos

## Seguridad
- auditor-seguridad: Aprobado con 3 hallazgos (SEG-062-01 Media, SEG-062-02 Baja, SEG-062-03 Baja), corregidos con regresión

## Verificación
| Comando | Resultado |
|---|---|
| `venv/bin/python -m pytest tests/provisioning/test_api.py` (antes de implementar) | 28 failed, 1 passed (404 sin rutas; `DID NOT RAISE` en los dos de concurrencia) |
| `venv/bin/python -m pytest tests/provisioning tests/access` | salida 0 |
| `venv/bin/python -m pytest -q` (completa) | 1565 passed, 15 xfailed, salida 0 |
| Regresiones SEG-062-01/02/03 antes de corregir | 9 failed (5 retry `200 == 409`; 4 fechas `ValueError: year … is out of range`) |
| `venv/bin/python -m pytest -q` (completa, tras corregir) | 1574 passed, 15 xfailed, salida 0 |
| `venv/bin/python -m pytest -q` (completa, tras el merge de develop) | 1605 passed, 15 xfailed, salida 0 |

- No verificado: concurrencia real en MySQL (se simula con otra conexión en SQLite); aviso al worker con Redis real (cola falsa)

## Riesgos y reversión
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-20 | Aprobada en modo autónomo y En curso (orquestador) |
| 2026-10-20 | Implementada; En revisión. Pendientes revisor y auditor-seguridad |
| 2026-10-20 | auditor-seguridad Aprobado; corregidos SEG-062-01/02/03 con regresiones; `git merge --no-ff develop` (FNC-063, FNC-066; develop en 5968254): conflictos en `app/__init__.py` y docs resueltos uniendo ambas versiones; `matriz_proteccion.py` y TABLERO sin conflicto |
