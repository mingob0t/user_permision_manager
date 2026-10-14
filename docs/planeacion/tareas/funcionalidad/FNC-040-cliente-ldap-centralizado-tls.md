# FNC-040 — Cliente LDAP centralizado con TLS validado y esquema de OpenLDAP configurable

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | directorio |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Commit local en la rama, sin push |
| **Rama** | `fnc/FNC-040-cliente-ldap` (worktree `pokemon-wt-040`) |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (TLS, credencial de bind, inyección LDAP) |

## Contexto
- Hay tres conexiones LDAP duplicadas (`app/modules/auth/services.py:42,213`, `app/modules/api/admin.py:607-614`, duplicado D-06), todas con `Tls(validate=CERT_NONE)` (SEG-13) y con atributos de Active Directory (`sAMAccountName`, `memberOf`) cuando el directorio es OpenLDAP
- La escritura de grupos (F-ACC-01) necesita una sola conexión segura con una cuenta de servicio de escritura
- Requerimientos: RF-02, F-ACC-01, F-USR-01, F-USR-02

## Objetivo
- Crear el módulo `app/modules/directory/` con un cliente único: conexión LDAPS o StartTLS obligatoria con `CERT_REQUIRED` y CA configurable, tiempos de espera, filtros escapados y el esquema de OpenLDAP (atributo de usuario, clase y atributo de miembro de grupo, OUs) leído de configuración según ADR-004

## Alcance
- **Incluye:**
  - `ldap_client.py`: abrir conexión de servicio, búsqueda de usuario por atributo, lectura de grupos de un usuario, comprobación de existencia de un DN
  - `configuracion.py`: lectura y validación al arrancar de la configuración del directorio (ADR-004)
  - Escape de filtros con `ldap3.utils.conv.escape_filter_chars` y de DN
  - Pruebas con un doble de `ldap3` (`MOCK_SYNC`) sin directorio real
- **No incluye:**
  - Escritura en el directorio (FNC-041)
  - Migrar el login y el rol al cliente nuevo (FNC-042)
  - Cambiar los endpoints de configuración (FNC-043)

## Hallazgos de seguridad que absorbe
- FNC-012 (SEG-13) para todo código que use el cliente nuevo; FNC-042 y FNC-043 terminan de migrar los llamadores y cierran FNC-012.
- Duplicado D-06 (catálogo de reutilización), al completarse con FNC-042 y FNC-043.

## Archivos previstos
- `app/modules/directory/__init__.py`
- `app/modules/directory/ldap_client.py`
- `app/modules/directory/configuracion.py`
- `tests/directory/`

## Reutilización
- `_escape_ldap_filter` de `app/modules/api/admin.py:579` se reemplaza por la función del cliente (la migración del llamador es de FNC-043)
- `ldap3` ya está en dependencias

## Variables y configuración
- Propuestas según ADR-004: `LDAP_URL` (nombre de host, esquema `ldaps://` o `ldap://` + StartTLS), `LDAP_CA_CERT_FILE`, `LDAP_BIND_DN`, `LDAP_BIND_PASSWORD` (sensible, Vaultwarden en staging/prod), `LDAP_USERS_BASE_DN`, `LDAP_GROUPS_BASE_DN`, `LDAP_USER_ATTR` (p. ej. `uid`), `LDAP_GROUP_OBJECT_CLASS`, `LDAP_GROUP_MEMBER_ATTR`, `LDAP_TIMEOUT_SECONDS`.
- Registrar en `VARIABLES.md` y `HISTORIAL.md`; actualizar `.env.example` con marcadores.

## Implementación
- `app/modules/directory/configuracion.py` (la ficha decía `config.py`, pero `.gitignore` ignora todo `config.py`): variables `LDAP_*` → `ConfiguracionDirectorio` validada; `validar_al_arrancar()` (activo solo con `LDAP_URL`)
- `app/modules/directory/ldap_client.py`: `ClienteDirectorio` (`conexion_servicio`, `buscar_usuario`, `grupos_de_usuario`, `existe_dn`), `escapar_filtro`, `escapar_valor_dn`, `ErrorDirectorio`
- `app/__init__.py`: `create_app()` llama a `validar_al_arrancar()` tras `config_overrides`
- TLS: `CERT_REQUIRED`, SNI y nombre del host verificados, CA de `LDAP_CA_CERT_FILE` o del sistema, contexto por defecto de Python (TLS ≥ 1.2); `ldap://` hace StartTLS antes del bind
- Solo lectura (`read_only=True`); espera de conexión y de respuesta = `LDAP_TIMEOUT_SECONDS`
- Grupos por búsqueda bajo `LDAP_GROUPS_BASE_DN` (clase + atributo de miembro); `memberUid` usa el identificador, el resto el DN; sin overlay `memberOf`
- `LDAP_URL` con IP, sin esquema TLS o con ruta: no arranca; nombres de atributo/clase validados (entran en filtros)
- `tests/conftest.py`: el cliente nuevo también queda bloqueado por defecto en pruebas
- Llamadores heredados sin cambios (login, búsqueda en el directorio, prueba de conexión): su migración es de FNC-042 y FNC-043 según "No incluye"; ningún `xfail` cambia

## Verificación
| Comando | Resultado real |
|---|---|
| `venv/bin/pytest tests/directory -q` | 64 passed |
| Mismo, con `validate=ssl.CERT_NONE` en el cliente (mutación, revertida) | 3 failed (`test_certificado_no_confiable…`, `test_nombre_del_certificado_distinto…`, `test_servidor_exige_certificado…`) |
| `venv/bin/pytest -q` | 495 passed, 35 xfailed, código 0 (antes 431 + 64 nuevas) |
| Regresiones de auditor-seguridad antes de corregir (`pytest tests/directory`) | 5 failed (StartTLS sin efecto, log de búsqueda ambigua, 3 formas de IPv4 abreviada) |
| `venv/bin/pytest -q -p no:warnings` tras corregir | 500 passed, 35 xfailed, código 0 |
| `python3 ~/.claude/agentes/herramientas/impacto.py` | 9 nombres: `__init__`, `_cliente`, `_crear`, `_error`, `agregar`, `bind`, `cerrar`, `directorio`, `grupo` (ver abajo) |
- TLS probado con un servidor TLS real en `localhost` y certificado autofirmado generado en la prueba (no confiable → falla; nombre distinto → falla; CA y nombre correctos → saludo completo)
- No verificado: OpenLDAP real (no hay servidor ni valores; el dueño los define, ADR-004); StartTLS real (el doble `MOCK_SYNC` no lo implementa: se prueba el orden StartTLS → bind con un espía)
- `revisor` y `auditor-seguridad` ejecutados por el orquestador (ver bitácora)

## Impacto en elementos compartidos
- `impacto.py` (2026-10-14): 9 nombres. Son funciones y métodos nuevos de `app/modules/directory/` y `tests/directory/` que se llaman igual que código existente (p. ej. `_error` de `ldap_client.py` frente a `_error` de `api/admin.py` y `api/crud.py`; `directorio`/`agregar` frente a `tests/directorio_falso.py`): homónimos, sin impacto real.
- Revisión manual: `create_app()` (`app/__init__.py`) ahora valida `LDAP_*`; sin `LDAP_URL` no cambia nada. La usan `run.py`, utilidades de `utils/` y todas las pruebas (`migrations/env.py` no la llama)
- Revisión manual: fixture autouse `sin_servicios_externos` (`tests/conftest.py`) bloquea también `ldap_client.Connection`; afecta a todas las pruebas (ninguna usaba el módulo nuevo)

## Criterios de aceptación
- [x] Con certificado no confiable la conexión falla con error controlado (`tests/directory/test_tls.py`)
- [x] Sin TLS configurado la app no arranca con el directorio activo (`test_create_app_no_arranca_con_directorio_sin_tls` y casos de `LDAP_URL`)
- [x] Un filtro con `*`, `(`, `)` o `\` se escapa (`test_filtro_escapa_…`, `test_comodin_o_parentesis_no_amplian_la_busqueda`)
- [x] La contraseña de bind nunca se registra en logs ni en respuestas (pruebas de bind rechazado, ocultación en el detalle y `repr`)
- [x] Criterios comunes backend (FNC-037): sin endpoints nuevos; revisor y auditor-seguridad atendidos
- Pendiente fuera de esta ficha: SEC-LDAP-01 (un solo módulo usa `ldap3`) se cumple al cerrar FNC-042 y FNC-043

## Commits / PR
- `e51fb64` [FNC-040] Cliente OpenLDAP centralizado de solo lectura con TLS validado (local, sin push ni PR)
- Commit de cierre de la ficha (este registro); sin push ni PR

## Impacto cruzado
- Genera → FNC-041, FNC-042, FNC-043
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, ADR-004 aceptado

## Riesgos y reversión
- Si el directorio usa un certificado interno, hace falta la CA: se documenta en `docs/operacion/ENTORNOS.md`.
- Reversión: el módulo es nuevo y nadie lo usa hasta FNC-041/042/043.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-14 | Aprobada por el dueño; implementada en `fnc/FNC-040-cliente-ldap`; 495 passed, 35 xfailed; En revisión (falta revisor y auditor-seguridad) |
- revisor (2026-10-14): Requiere cambios de cierre; corregidos (impacto real, lista de usos de `create_app`, nombre `configuracion.py`). Falta el veredicto de auditor-seguridad.
- auditor-seguridad (modo cambio, 2026-10-14): **Aprobado**, 3 hallazgos Baja, corregidos con prueba de regresión que primero falló:
  - StartTLS sin efecto: se exige `tls_started` antes del bind (`test_starttls_sin_efecto_no_envia_la_credencial`)
  - Búsqueda ambigua: el log ya no incluye el identificador, solo atributo y base (`test_busqueda_ambigua_no_registra_el_identificador`)
  - `LDAP_URL` con IPv4 abreviada o decimal (solo números y puntos) se rechaza (`test_url_con_ipv4_abreviada_se_rechaza`)
- Estatus: En revisión hasta el merge.
