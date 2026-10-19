# FNC-046 — Plataformas: tipo de integración y grupos LDAP por nivel

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | plataformas |
| **Prioridad** | Alta |
| **Estatus** | Hecha |
| **Inicio** | 2026-10-19 |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Commit local, sin push (worktree `pokemon-wt-046`) |
| **Rama** | `fnc/FNC-046-plataformas-integracion` |
| **Commits / PR** | `81241d5` [FNC-046] (local, sin push ni PR) + commit de registro del hash |
| **Requiere migración BD** | Sí (columnas nuevas en `platforms`) |
| **Requiere auditor-seguridad** | Sí (validación de URL y DN) |

## Contexto
- `Platform` (`app/modules/core/models.py:37`) no tiene tipo de integración ni grupos (F-PLAT-01)
- `direct_link` y `logo_url` aceptan cualquier esquema (SEG-24)
- Requerimientos: F-PLAT-01, RF-01, RF-02

## Objetivo
- Agregar a la plataforma `integration_type` (`ldap` o `conector`) y los DN de sus grupos de nivel `usuario` y `admin`, validados contra la convención de ADR-004 y, si es posible, contra el directorio

## Alcance
- **Incluye:**
  - Columnas `integration_type`, `ldap_group_user_dn`, `ldap_group_admin_dn` (nulos solo si es `conector` y ADR-004 lo permite)
  - Validación en `POST/PUT /platforms`: DN dentro de `LDAP_GROUPS_BASE_DN`, grupos distintos por nivel, existencia comprobada con el cliente de FNC-040 (aviso si no existe)
  - Validación de `direct_link` y `logo_url`: solo `https://` (o `http://` si el dueño lo justifica)
  - Cambiar el tipo o los grupos con accesos activos responde 409 (no hay migración de miembros en v1)
  - `to_dict` incluye los campos nuevos; deja de exponer `user_ids` si FNC-065 se aprueba
- **No incluye:**
  - Configuración del conector (FNC-050, FNC-061)
  - Crear los grupos en el directorio (ADR-004)
  - Pantalla (DIS-017)

## Hallazgos de seguridad que absorbe
- **FNC-017** parcial: SEG-24 (validación de URL en `crud.py:139-142`, `:158-168`).

## Archivos previstos
- `app/modules/core/models.py` (`Platform`)
- `app/modules/core/validators.py` (nuevo) → se hizo en `app/modules/platforms/validacion.py` (módulo propio)
- `app/modules/api/crud.py` (`create_platform`, `update_platform`) → rutas movidas a `app/modules/platforms/api.py`
- Migración (ADR-002)
- `tests/platforms/`

## Archivos tocados
- Nuevos: `app/modules/platforms/{__init__,api,validacion,grupos,tipos,estado}.py`, `migrations/versions/0005_plataformas_integracion_grupos.py`, `tests/platforms/{__init__,test_integracion_y_grupos,test_regresion_seg24,test_migracion_0005,test_revision_seguridad}.py`
- Revisión: `app/modules/api/routes.py` (`url_segura` en `_platform_payload`), `docs/estandarizacion/03-reutilizacion.md`, `docs/contratos/plataformas-integracion.md`, FNC-015
- Modificados: `app/__init__.py` (registro del blueprint), `app/modules/api/crud.py` (rutas de plataformas retiradas), `app/modules/core/models.py` (`Platform`), `app/modules/directory/configuracion.py` (`LDAP_PLATFORM_GROUP_TEMPLATE`)
- Pruebas ajustadas: `tests/matriz_proteccion.py`, `tests/test_proteccion_por_rol.py`, `tests/test_auditoria_crud.py`, `tests/test_alcance_por_area.py`
- Docs: `.env.example`, `docs/configuracion/VARIABLES.md`, `HISTORIAL.md`, `docs/backend/README.md`, `docs/seguridad/LINEAMIENTOS.md` §11, `CHANGELOG.md`, tablero, FNC-017, `docs/logs/2026-10-19.md`

## Reutilización
- Cliente de FNC-040 para comprobar grupos
- `platform_manage_required`

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `Platform.to_dict` | Serialización | Solo respuestas de `POST/PUT /platforms` (administración de plataformas, `platform-admin.tsx`); `GET /platforms`, `/favorites` y `/stats` usan `_platform_payload` y no cambian | Pendiente (DIS-017) |
| Modelo `Platform` | Modelo | 4 columnas nuevas con valor por defecto; lecturas existentes sin cambio | Sí (pytest completo) |
| `POST/PUT /platforms` | Endpoint | `frontend/src/lib/api.ts` (`createPlatform`, `updatePlatform`), `platform-admin.tsx` | Pendiente (DIS-017/FNC-069) |
| `ConfiguracionDirectorio` / `cargar_configuracion` | Configuración | `ldap_client.py`, `resumen.py`, pruebas del directorio: campo nuevo opcional `plantilla_grupo` (aditivo) | Sí (pytest completo) |

### Salida real de `impacto.py` (contra `develop`, tras la revisión; 19 elementos)
| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `/platforms` | endpoint | `app/modules/api/crud.py`, `app/modules/platforms/api.py` | `app/modules/core/routes.py`, `app/modules/users/routes.py`, `frontend/src/components/app-shell.tsx`, `frontend/src/lib/api.ts`, `tests/users/test_roles_y_areas_administradas.py` | app/modules, frontend/src, tests/users | ☐ |
| `Platform` | clase | `app/modules/core/models.py` | `app/authz.py`, `app/modules/audit/models.py`, `app/modules/auth/models.py`, `frontend/src/components/platform-admin.tsx`, `frontend/src/components/platform-card.tsx`, `frontend/src/components/users-list.tsx`, `frontend/src/lib/api.ts`, `frontend/src/lib/types.ts` (+2) | app, app/modules, frontend/src, scratch, tests | ☐ |
| `__init__` | función | `app/modules/platforms/api.py` | `app/modules/directory/ldap_client.py`, `app/modules/directory/writer.py`, `app/modules/notifications/services.py`, `app/utils/redis_client.py`, `tests/directorio_falso.py`, `tests/directory/conftest.py`, `tests/directory/test_tls.py`, `tests/smtp_falso.py` | app/modules, app/utils, tests, tests/directory | ☐ |
| `_actor` | función | `app/modules/platforms/api.py` | `app/modules/audit/services.py` | app/modules | ☐ |
| `_codigo` | función | `tests/platforms/test_integracion_y_grupos.py` | `tests/directory/test_api.py`, `tests/users/test_roles_y_areas_administradas.py` | tests/directory, tests/users | ☐ |
| `_texto` | función | `app/modules/platforms/validacion.py` | `app/modules/directory/ldap_client.py` | app/modules | ☐ |
| `_valores` | función | `app/modules/platforms/api.py` | `app/modules/directory/resumen.py` | app/modules | ☐ |
| `area` | función | `tests/platforms/test_integracion_y_grupos.py` | `app/modules/audit/models.py`, `app/modules/notifications/access_notifications.py`, `app/modules/users/areas_administradas.py`, `frontend/src/components/areas-list.tsx`, `frontend/src/components/dashboard.tsx`, `frontend/src/components/platform-admin.tsx`, `frontend/src/components/platform-catalog.tsx`, `frontend/src/components/users-list.tsx` (+8) | app/modules, frontend/src, migrations/versions, tests, tests/audit, tests/notifications | ☐ |
| `campos_no_permitidos` | función | `app/modules/platforms/validacion.py` | `app/modules/users/roles.py` | app/modules | ☐ |
| `cargar_configuracion` | función | `app/modules/directory/configuracion.py` | `app/modules/directory/ldap_client.py`, `app/modules/directory/resumen.py`, `tests/directorio_falso.py`, `tests/directory/conftest.py`, `tests/directory/test_config.py`, `tests/directory/test_tls.py` | app/modules, tests, tests/directory | ☐ |
| `datos` | función | `tests/test_auditoria_crud.py` | `app/authz.py`, `app/modules/api/admin.py`, `app/modules/api/helpers.py`, `app/modules/audit/services.py`, `app/modules/directory/api.py`, `app/modules/directory/errors.py`, `app/modules/directory/writer.py`, `app/modules/notifications/access_notifications.py` (+31) | app, app/modules, app/utils, frontend, frontend/src, frontend/tests, migrations/versions, scratch, scripts/lineamientos, tests, tests/audit, tests/directory, tests/notifications, tests/users, utils, utils/migrations | ☐ |
| `directorio` | función | `tests/platforms/test_integracion_y_grupos.py` | `app/modules/api/admin.py`, `app/modules/api/auth.py`, `app/modules/auth/models.py`, `app/modules/auth/routes.py`, `app/modules/auth/services.py`, `app/modules/directory/api.py`, `app/modules/directory/errors.py`, `app/modules/directory/ldap_client.py` (+20) | app/modules, frontend/src, scratch, tests, tests/directory | ☐ |
| `downgrade` | función | `migrations/versions/0005_plataformas_integracion_grupos.py` | `migrations/versions/0001_linea_base_esquema_actual.py`, `migrations/versions/0002_auditoria_ampliada.py`, `migrations/versions/0003_plantillas_gestor_accesos.py`, `migrations/versions/0004_vaciar_credencial_ldap.py`, `tests/notifications/test_migracion_plantillas.py`, `tests/test_migracion_0004.py`, `tests/test_migraciones.py` | migrations/versions, tests, tests/notifications | ☐ |
| `falla` | función | `tests/platforms/test_integracion_y_grupos.py` | `app/authz.py`, `app/modules/audit/services.py`, `frontend/src/components/platform-card.tsx`, `frontend/tests/accesibilidad/colores-literales.excepciones.ts`, `frontend/tests/accesibilidad/contraste.test.ts`, `migrations/versions/0002_auditoria_ampliada.py`, `tests/directory/test_ldap_client.py`, `tests/directory/test_tls.py` (+4) | app, app/modules, frontend/src, frontend/tests, migrations/versions, tests, tests/directory, tests/users | ☐ |
| `identificador` | función | `app/modules/platforms/grupos.py` | `app/modules/auth/services.py`, `app/modules/directory/api.py`, `app/modules/directory/ldap_client.py`, `app/modules/directory/writer.py`, `app/modules/users/areas_administradas.py`, `tests/directory/test_ldap_client.py`, `tests/directory/test_verificar_contrasena.py`, `tests/directory/test_writer.py` (+1) | app/modules, tests, tests/directory | ☐ |
| `superadmin` | función | `tests/platforms/test_integracion_y_grupos.py` | `app/authz.py`, `app/modules/api/admin.py`, `app/modules/api/auth.py`, `app/modules/auth/services.py`, `app/modules/directory/api.py`, `app/modules/users/api.py`, `app/modules/users/areas_administradas.py`, `app/modules/users/roles.py` (+8) | app, app/modules, frontend/src, migrations/versions, tests, tests/notifications, tests/users | ☐ |
| `to_dict` | función | `app/modules/core/models.py` | `app/modules/api/admin.py`, `app/modules/audit/models.py`, `app/modules/auth/models.py`, `app/modules/notifications/models.py`, `app/modules/settings/models.py`, `tests/audit/test_registro_ampliado.py`, `tests/users/test_roles_y_areas_administradas.py` | app/modules, tests/audit, tests/users | ☐ |
| `upgrade` | función | `migrations/versions/0005_plataformas_integracion_grupos.py` | `migrations/env.py`, `migrations/versions/0001_linea_base_esquema_actual.py`, `migrations/versions/0002_auditoria_ampliada.py`, `migrations/versions/0003_plantillas_gestor_accesos.py`, `migrations/versions/0004_vaciar_credencial_ldap.py`, `tests/notifications/test_migracion_plantillas.py`, `tests/test_migracion_0004.py`, `tests/test_migraciones.py` | migrations, migrations/versions, tests, tests/notifications | ☐ |
| `validar` | función | `app/modules/platforms/validacion.py` | `app/modules/api/admin.py`, `frontend/src/components/login-form.tsx`, `tests/directory/test_aislamiento.py`, `utils/db_migrate.py` | app/modules, frontend/src, tests/directory, utils | ☐ |

Lectura:
- **Reales:** `/platforms` (`POST`/`PUT` en `lib/api.ts` → DIS-017; el `GET` de `routes.py` solo filtra URL no https), `Platform` (columnas con valor por defecto), `cargar_configuracion` (campo opcional `plantilla_grupo`), `Platform.to_dict` (solo lo usa `platforms/api.py`).
- **Homónimos** (mismo nombre, otra cosa): `__init__` (clase `Rechazo`), `_actor`, `_texto`, `_valores`, `identificador`, `validar` (funciones privadas o locales de `platforms/`), `campos_no_permitidos` (nombre retirado de `platforms`; el de `users/roles.py` no cambia), `to_dict` de otros modelos, `upgrade`/`downgrade` (cada migración), y fixtures de prueba `_codigo`, `area`, `datos`, `directorio`, `falla`, `superadmin`.

## Criterios de aceptación
- [x] Alta de plataforma `ldap` sin grupos responde 4xx: `422 validacion` según el contrato (`test_ldap_sin_grupos_ni_convencion_responde_422`)
- [x] DN fuera de la base de grupos responde `422` (`test_dn_fuera_de_la_base_responde_422`, 5 variantes)
- [x] `javascript:` en `direct_link` responde `422` (`test_regresion_seg24.py`, falló antes del cambio)
- [x] Cambio de grupos, tipo o área con accesos activos responde `409` (`test_cambio_de_grupos_tipo_o_area_con_accesos_responde_409`, con el punto de extensión simulado)
- [x] Criterios comunes backend (FNC-037): protección, lista blanca, alcance 404, auditoría en la misma transacción, matriz

## Verificación
| Comando | Resultado real |
|---|---|
| `venv/bin/python -m pytest -q` (antes, `develop` 3f7e625) | 805 passed, 17 xfailed, código 0 |
| `pytest tests/platforms/test_regresion_seg24.py` contra el código anterior | 14 failed (aceptaba `javascript:`, `data:`, `http:`, sin host, con espacio) |
| `venv/bin/python -m pytest -q -p no:cacheprovider -W ignore` (después) | 877 passed, 17 xfailed, código 0 (+72 pruebas) |
| `pytest tests/platforms/test_revision_seguridad.py` antes de corregir la revisión | 15 failed, 3 passed (los 3 son de no regresión: propia plataforma, ida y vuelta del superadmin, URL válida) |
| `venv/bin/python -m pytest -q -p no:cacheprovider -W ignore` (tras la revisión) | 896 passed, 17 xfailed, código 0 (+19 pruebas); luego se quitó el caso de IPv4 completa en notación decimal con puntos (el control de IP del commit lo bloquea; la IPv4 completa la cubre `ipaddress` y quedan IPv6 y abreviadas): pytest completo de nuevo: ver fila siguiente |
| `venv/bin/python -m pytest -q -p no:cacheprovider -W ignore` (final) | 895 passed, 17 xfailed, código 0 |
- Sin `xfail` que quitar: ninguno cubría SEG-24 ni las reglas nuevas
- No verificado: OpenLDAP real (sin servidor ni valores, ADR-004); existencia de grupos solo con `ldap3` `MOCK_SYNC`; MySQL real para la migración 0005 (solo SQLite)

## Decisiones y observaciones
- Decisión del orquestador (pendiente de validar en la prueba de concepto): errores de formato `422 validacion` (contrato), no `400` como decía la ficha; `400` queda para cuerpo inválido y campos fuera de la lista blanca
- Decisión del orquestador (pendiente de validar en la prueba de concepto): URL solo `https://` (contrato y SEC-SES-10); `http://` no se justificó. `''` o `null` = sin enlace
- Decisión del orquestador (pendiente de validar en la prueba de concepto): convención en `LDAP_PLATFORM_GROUP_TEMPLATE` (relativa a `LDAP_GROUPS_BASE_DN`, `{plataforma}` y `{nivel}` obligatorios, `{area}` opcional), vacía por defecto: sin ella el admin no crea plataformas `ldap` (422) y el superadmin indica los DN
- Decisión del orquestador (pendiente de validar en la prueba de concepto): los valores derivados se pasan a identificador ASCII (`Contabilidad General` → `contabilidad-general`) y se escapan; no pueden agregar RDN
- Decisión del orquestador (pendiente de validar en la prueba de concepto): la base de validación es `LDAP_GROUPS_BASE_DN` (no la base misma); DN mal formado = fuera de la base
- Decisión del orquestador (pendiente de validar en la prueba de concepto): `ldap` con el directorio inactivo → `422` en `integration_type` (no se guardan grupos sin poder validarlos)
- Decisión del orquestador (pendiente de validar en la prueba de concepto): `conector` no acepta DN (`422`); pasar a `conector` borra los DN y deja `sin_verificar`
- Decisión del orquestador (pendiente de validar en la prueba de concepto): un admin que envía cualquier campo DN (aunque sea `null`) recibe `403 dn_solo_superadmin`
- Decisión del orquestador (pendiente de validar en la prueba de concepto): en `PUT` los grupos solo se validan si cambian el tipo o un DN; las plataformas heredadas (`ldap` sin grupos) se editan sin completarlos. Cambiar de área no rederiva los DN
- Decisión del orquestador (pendiente de validar en la prueba de concepto): `user_ids` deja de exponerse en `to_dict` (contrato v1; ningún consumidor lo lee; menos exposición) aunque FNC-065 siga en Propuesta
- Decisión del orquestador (pendiente de validar en la prueba de concepto): área inexistente o ajena → `404` en `POST` y `PUT` (contrato), antes `403`; `DELETE` y `PUT .../users` siguen igual (`403`)
- Rutas `POST/PUT/DELETE /platforms` y `PUT /platforms/<id>/users` movidas a `app/modules/platforms/api.py`; `DELETE` y `/users` sin cambios
- Puntos de extensión: `platforms/estado.py` `accesos_vigentes` (FNC-054) y `tiene_conector` (FNC-050); hoy `0`/`False`
- Acceso automático de los admins del área al dar de alta (P6) no se hace aquí: FNC-055
- `GET /platforms` (`routes.py`) no expone los campos nuevos: visibilidad en FNC-063
- `GET /auth-config` no muestra `LDAP_PLATFORM_GROUP_TEMPLATE` (sería aditivo en `usuarios-directorio.md`); queda como observación para DIS-017/DIS-023
- SEG-24 en el frontend (`platform-card.tsx`, `href`) sigue abierto en FNC-017 (web)

## Revisiones
- auditor-seguridad: **Aprobado** con 1 Media y 2 Baja, corregidas:
  - Media: `409 grupo_en_uso` si un DN (enviado o derivado, comparado con `mismo_dn`) es de otra plataforma, en alta y edición
  - Baja: URL guardadas que no cumplen `validar_url` salen `null` en `to_dict` y `GET /platforms` (`url_segura`); el frontend queda para DIS-017
  - Baja: `validar_url` rechaza credenciales, IP literal (`es_ip_literal`, también abreviadas) y DEL
- revisor: **Requiere cambios**, corregidos: catálogo `03-reutilizacion.md`, impacto completo, nota de heredadas en el contrato (aditivo), `PUT` sin cambios no audita, `campos_no_permitidos` → `campos_fuera_de_lista`; `DELETE` y `PUT .../users` fuera de la transacción quedan en la bitácora de FNC-015
- Decisión del orquestador (pendiente de validar en la prueba de concepto): cambiar `integration_type` en `PUT` es solo del superadmin (`403 dn_solo_superadmin`), porque borra o re-deriva grupos; el admin de área elige el tipo solo en el alta
- Decisión del orquestador (pendiente de validar en la prueba de concepto): la comprobación de grupo en uso compara contra todas las demás plataformas con DN (en Python, por normalización); suficiente para el volumen esperado

## Impacto para DIS-017 (frontend sin tocar)
- `POST /platforms` exige `integration_type` y `description`: el formulario actual no envía `integration_type` → `422` hasta DIS-017/FNC-069
- Errores `422` con `fields`, `403 dn_solo_superadmin` (DN o cambio de tipo), `404`, `409 grupos_iguales`, `409 grupo_en_uso` y `409 plataforma_con_accesos`
- URL guardadas no https llegan `null`
- Respuesta con `warnings` (`grupo_no_existe`, `directorio_no_disponible`) y campos nuevos de `Platform`
- `direct_link`/`logo_url` solo `https://`
- Campos DN solo para el superadmin; el admin no debe enviarlos

## Riesgos y reversión (implementación)
- **No promover a staging sin DIS-017/FNC-069**: el alta desde la pantalla actual responde `422`.

## Impacto cruzado
- Genera → DIS-017
- Genera → FNC-050
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-039, FNC-040, FNC-038, FNC-047
- Contrato → docs/contratos/plataformas-integracion.md

## Riesgos y reversión
- Plataformas existentes quedan sin grupos: la migración las marca `ldap` sin grupos y no se pueden solicitar hasta completarlas.
- Reversión: bajar la migración.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-19 | Aprobada (modo autónomo, vía orquestador); implementada en `fnc/FNC-046-plataformas-integracion`; absorbe SEG-24 (backend) de FNC-017. En revisión |
| 2026-10-19 | auditor-seguridad Aprobado (1 Media, 2 Baja) y revisor Requiere cambios: todo corregido con regresiones; sigue En revisión |
- Re-auditoría de seguridad (2026-10-19): Aprobado; la carrera de altas concurrentes queda en FNC-080 (Propuesta, Baja).
- Cierre (2026-10-19): merge local a `develop` (modo autónomo).
