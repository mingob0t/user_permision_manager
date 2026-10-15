# FNC-041 — Servicio de escritura en OpenLDAP: membresía de grupos y alta de cuentas

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
| **Estatus Git** | Commit local, sin push |
| **Rama** | `fnc/FNC-041-escritura-ldap` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (escritura en el directorio de identidad) |

## Contexto
- El portal hoy solo lee del directorio
- Otorgar acceso es agregar al usuario al grupo LDAP de la plataforma y del nivel; revocar es quitarlo (RF-02, F-ACC-01/02), y las cuentas creadas en el portal deben vivir en OpenLDAP (F-USR-02)
- Requerimientos: RF-02, F-ACC-01, F-ACC-02, F-USR-02

## Objetivo
- Agregar a `app/modules/directory/` un servicio de escritura idempotente: agregar y quitar un miembro de un grupo, y crear una cuenta de usuario en la OU configurada, con resultado tipificado (hecho, ya estaba, no existe, error transitorio, error permanente) para que el ejecutor decida si reintenta

## Alcance
- **Incluye:**
  - `writer.py`: `add_member(group_dn, user)`, `remove_member(group_dn, user)`, `create_user(datos)` según la clase de grupo y los atributos de ADR-004
  - Idempotencia: agregar a quien ya es miembro o quitar a quien ya no lo es se reporta como éxito
  - Clasificación de errores LDAP en transitorios (red, tiempo de espera, servidor ocupado) y permanentes (DN inexistente, permisos insuficientes, violación de esquema)
  - Cuando la clase de grupo exige al menos un miembro (`groupOfNames`), manejo del último miembro según ADR-004
  - Pruebas con doble de `ldap3`
- **No incluye:**
  - Crear o borrar grupos de plataforma (ADR-004 decide si los crea el portal o el administrador del directorio; si es el portal, se agrega como tarea)
  - Contraseñas: la cuenta se crea sin contraseña conocida por el portal (pregunta P8)
  - Cola y reintentos (FNC-049)
  - Endpoints

## Archivos previstos
- `app/modules/directory/writer.py`
- `app/modules/directory/errors.py`
- `tests/directory/test_writer.py`

## Reutilización
- Cliente y configuración de FNC-040

## Variables y configuración
- Las de FNC-040; `LDAP_USER_OBJECT_CLASSES` y atributos obligatorios de alta si ADR-004 los define.
- Agregadas: `LDAP_USER_OBJECT_CLASSES` (vacía = `inetOrgPerson`) y `LDAP_GROUP_PLACEHOLDER_MEMBER` (vacía = no se quita el último miembro); en `.env.example`, `VARIABLES.md` y `HISTORIAL.md`
- Sin credencial de escritura aparte: se usa la cuenta de `LDAP_BIND_DN` con conexión de escritura (la ficha no pide otra); su ACL acotada es del administrador del directorio (SEC-LDAP-03, P3)

## Implementación
- `writer.py`: `EscritorDirectorio` (`add_member`, `remove_member`, `create_user`), `DatosCuenta`; reutiliza `ClienteDirectorio` (TLS, espera, log) con `conexion_servicio(solo_lectura=False)`
- `errors.py`: `Resultado` (`hecho`, `ya_estaba`, `no_existe`, `error_transitorio`, `error_permanente`), `ResultadoEscritura` (`exito`, `reintentable`, `motivo`), `clasificar_error`
- `ldap_client.py`: `conexion_servicio(solo_lectura=True)` (por defecto igual que antes); `ErrorDirectorio(mensaje, causa=None)` para clasificar fallos de conexión
- `configuracion.py`: `clases_usuario` y `miembro_relleno` desde dos variables nuevas, validadas al arrancar
- Bases: grupo bajo `LDAP_GROUPS_BASE_DN` y usuario bajo `LDAP_USERS_BASE_DN` (RDN normalizados) o `error_permanente` sin conectar (SEC-LDAP-04); el registro en una plataforma lo valida FNC-049
- Membresía: lectura previa + un solo `MODIFY_ADD`/`MODIFY_DELETE`; `AttributeOrValueExists`/`NoSuchAttribute` (carreras) → `ya_estaba` (SEC-LDAP-07/08)
- Último miembro (`groupOfNames`/`groupOfUniqueNames`): ADR-004 no lo define; con `LDAP_GROUP_PLACEHOLDER_MEMBER` se agrega el relleno y se quita al usuario en la misma operación; sin él, `error_permanente` `ultimo_miembro` (**por confirmar con el dueño**)
- Alta: DN con `escapar_valor_dn`; `cn`, `sn`, `givenName`, `mail`; sin `userPassword` (P8); existente → `ya_estaba` (FNC-064 decide el 409)

## Verificación
| Comando | Resultado real |
|---|---|
| `venv/bin/python -m pytest -q` (línea base, antes del cambio) | 526 passed, 35 xfailed, código 0 |
| `venv/bin/python -m pytest -q tests/directory/test_writer.py` antes de implementar | error de colección (`writer` no existe): falla |
| `venv/bin/python -m pytest -q tests/directory/` | 135 passed |
| `venv/bin/python -m pytest -q` | 592 passed, 35 xfailed, código 0 (66 pruebas nuevas) |
- No verificado: OpenLDAP real (sin servidor ni valores; ADR-004); esquema y ACL reales (el doble `MOCK_SYNC` no valida esquema: el último miembro se prueba por la lógica del servicio)
- `revisor` y `auditor-seguridad` pendientes (los lanza el orquestador)

## Impacto en elementos compartidos
Salida de `python3 ~/.claude/agentes/herramientas/impacto.py` (contra `develop`):

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `ErrorDirectorio` | clase | `app/modules/directory/ldap_client.py` | `tests/directory/test_ldap_client.py`, `tests/directory/test_tls.py` | tests/directory | ☐ |
| `__init__` | función | `app/modules/directory/ldap_client.py` | `app/modules/notifications/services.py`, `app/utils/redis_client.py`, `tests/directorio_falso.py`, `tests/directory/conftest.py`, `tests/directory/test_tls.py`, `tests/matriz_proteccion.py`, `tests/smtp_falso.py` | app/modules, app/utils, tests, tests/directory | ☐ |
| `_error` | función | `app/modules/directory/ldap_client.py` | `app/modules/api/admin.py`, `app/modules/api/crud.py`, `tests/directory/test_ldap_client.py` | app/modules, tests/directory | ☐ |
| `cargar_configuracion` | función | `app/modules/directory/configuracion.py` | `tests/directory/conftest.py`, `tests/directory/test_tls.py` | tests/directory | ☐ |
| `conexion_servicio` | función | `app/modules/directory/ldap_client.py` | `tests/directory/test_ldap_client.py` | tests/directory | ☐ |

- Homónimos: `__init__` es el de `ErrorDirectorio` (los de notificaciones, Redis y dobles son de otras clases); `_error` de `api/crud.py` (y su import en `admin.py`) es otra función
- Reales: `ErrorDirectorio`, `conexion_servicio`, `cargar_configuracion`: cambios compatibles (parámetros con valor por defecto); fuera de `directory/` no hay llamadores en `app/`; sus pruebas pasan sin cambios
- Validar al integrar con FNC-042/043 (usarán `ClienteDirectorio`): la lectura sigue siendo `read_only=True` por defecto

## Criterios de aceptación
- [x] Agregar y quitar son idempotentes (pruebas)
- [x] Error permanente y transitorio clasificados (pruebas por tipo)
- [x] Valores de usuario escapados al formar DN (prueba con caracteres especiales)
- [x] Ninguna operación de borrado de cuentas en v1
- [x] Criterios comunes backend (FNC-037): sin endpoints (no aplica 401/403); lógica en el módulo; variables registradas; sin IPs ni secretos; tabla de impacto abajo

## Commits / PR
- Commit local `[FNC-041]` en `fnc/FNC-041-escritura-ldap` (hash en el informe de cierre); sin push ni PR

## Impacto cruzado
- Genera → FNC-049 (proveedor LDAP del ejecutor)
- Genera → FNC-064 (alta de cuentas)
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-040, ADR-004

## Riesgos y reversión
- La cuenta de servicio necesita ACL de escritura acotada a la OU de grupos de plataformas y a la OU de usuarios; si es más amplia, un fallo del portal afecta todo el directorio (pregunta P3).
- Reversión: el servicio no se llama hasta FNC-049/FNC-064.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-15 | Implementada en `fnc/FNC-041-escritura-ldap` (worktree `pokemon-wt-041`); 592 passed, 35 xfailed; En revisión (falta revisor y auditor-seguridad; último miembro por confirmar) |
