# FNC-061 — API de configuración de conectores (superadmin)

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | conectores |
| **Prioridad** | Media |
| **Estatus** | En revisión |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Commit local en `fnc/FNC-061-api-conectores`, sin push |
| **Rama** | `fnc/FNC-061-api-conectores` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (configuración de credenciales) |

## Contexto
- La configuración de conectores la hace solo el superadmin (REQUERIMIENTOS §2 y tabla de pantallas)
- Sin API no se puede dar de alta un conector
- Requerimientos: F-CON-01

## Objetivo
- Exponer el CRUD de `platform_connectors` y una prueba de conexión (`check`) que no otorga ni revoca

## Alcance
- **Incluye:**
  - `GET/PUT /platforms/<id>/connector`, `DELETE` si no hay accesos activos
  - `POST /platforms/<id>/connector/test` con mensaje genérico
  - Validación de parámetros por tipo y de la referencia de credencial (existe, sin leer el valor en la respuesta)
  - Solo `admin_required`
- **No incluye:**
  - Pantalla (DIS-022)
  - Alta de ítems en Vaultwarden (lo hace el superadmin en Vaultwarden)

## Archivos previstos
- `app/modules/connectors/api.py`
- `app/__init__.py` (registro)
- `tests/connectors/test_api.py`

## Archivos tocados
| Archivo | Cambio |
|---|---|
| `app/modules/connectors/api.py` | Nuevo: 4 endpoints (blueprint `api_connectors`) |
| `app/modules/connectors/prueba.py` | Nuevo: `probar_conexion` (reutiliza `ProveedorConector.consultar`) |
| `app/__init__.py` | Registro del blueprint (2 líneas) |
| `tests/connectors/test_api.py` | Nuevo: 41 pruebas |
| `tests/matriz_proteccion.py` | 4 casos `solo_superadmin`, preparación `_con_conector_noop` y 1 caso de 400 |
| `docs/contratos/conectores-y-ejecuciones.md` | Fila de historial: aclaraciones (sin cambio de forma) |
| `docs/backend/README.md`, `docs/estandarizacion/03-reutilizacion.md`, `CHANGELOG.md` | Documentación |

## Decisiones del orquestador (pendientes de validar en la prueba de concepto)
| Tema | Decisión | Motivo |
|---|---|---|
| Aprobación | La tarea estaba en `Propuesta`; se aprobó en modo autónomo | Instrucción del dueño (2026-10-18) |
| `GET` sin configuración | `404 no_encontrado` | "Un recurso inexistente da 404"; el contrato no define otra forma |
| Existencia de la credencial | El `PUT` no consulta el gestor: valida formato y conflictos; la existencia la comprueba `test` y queda en `credential_status` (`ok`/`no_encontrada`) | Vaultwarden es *stub* hasta FNC-068; guardar no depende del gestor y nunca se lee el valor en la petición |
| `409` por accesos en `PUT` | Solo al cambiar el `type` del conector con `accesos_vigentes > 0`; host, puerto, `params`, referencia y `active` se pueden corregir | Cambiar el tipo deja accesos otorgados por otro mecanismo; corregir un dato no |
| Cuerpo de `DELETE` y `test` | JSON `{}` obligatorio; otro campo → `400 campo_no_permitido` | `escritura_del_portal` (P13), igual que el reintento de FNC-062 |
| Cuenta de la prueba | `consultar` con la cuenta del superadmin que prueba, nivel `usuario`, operación `otorgar` (enumerada); no otorga ni revoca | SEC-CON-03: solo datos del servidor |
| Caché | `limpiar_cache()` tras el commit de `PUT`/`DELETE` y antes de `test` | B4; la prueba debe reflejar el gestor actual |
| Auditoría | Antes y después solo de lo que cambió; `credential_ref` queda `[omitido]` por el saneo (`credential` es fragmento sensible) | No se evade el saneo; el valor nunca se guarda |
| Respuesta del `PUT` | `200` al crear y al reemplazar | Contrato |

## Reutilización
- Modelo, registro y resolvedor de FNC-050
- `admin_required`

## Criterios de aceptación
- [x] Admin de área y usuario reciben 403 (prueba; también si el admin administra el área)
- [x] Ninguna respuesta incluye secretos (prueba)
- [x] Parámetros inválidos para el tipo responden 422 `validacion` por campo, como dice el contrato; un campo fuera de la lista blanca responde 400 (pruebas)
- [x] Criterios comunes backend (FNC-037): matriz, formato de error, auditoría, sin IP ni secretos

## Impacto cruzado
- Genera → DIS-022
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-050, FNC-038
- Contrato → docs/contratos/conectores-y-ejecuciones.md

## Riesgos y reversión
- Reversión: revertir la rama.

## Requisitos de seguridad heredados de FNC-050 (auditor-seguridad)
- Solo el superadmin crea, modifica, borra o prueba conectores (SEC-CON-11); matriz con 403 para usuario y admin de área.
- Validar el cuerpo con `connectors.validacion.validar_configuracion(datos, referencias_en_uso=…)`, pasando las `credential_ref` de las demás plataformas (`consultas.referencias_de_otras`); sin reglas propias.
- Al guardar o borrar la configuración, llamar a `connectors.credenciales.limpiar_cache()` para no seguir usando la credencial anterior (B4).

## Impacto en elementos compartidos
Salida de `impacto.py` (2026-10-21): **ninguno detectado** (comparado contra `develop`; 11 archivos cambiados). Solo se agregó un blueprint (2 líneas en `app/__init__.py`) y casos en `tests/matriz_proteccion.py`; `escritura_del_portal`, `admin_required`, `validar_configuracion` y `limpiar_cache` se reutilizan sin cambios.

## Verificación
| Comando | Resultado |
|---|---|
| `venv/bin/python -m pytest tests/connectors tests/test_proteccion_por_rol.py tests/test_guardia_rutas.py` | 446 passed, salida 0 |
| Las mismas pruebas sin el registro del blueprint | 58 failed (fallan primero), salida 1 |
| `venv/bin/python -m pytest` (suite completa) | 1756 passed, 15 xfailed, salida 0 (16 min) |
No verificado: Vaultwarden real (stub hasta FNC-068); tipos `api`, `ssh`, `bd` (FNC-051 a 053). Pendientes: revisor y auditor-seguridad (no lanzados por instrucción).

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-20 | Recomendaciones de auditor-seguridad sobre FNC-050 agregadas (sección «Requisitos de seguridad heredados de FNC-050») |
| 2026-10-20 | En curso: API, prueba de conexión, pruebas y matriz |
| 2026-10-21 | En revisión: suite completa 1756 passed, 15 xfailed, salida 0; pendientes revisor y auditor-seguridad |
