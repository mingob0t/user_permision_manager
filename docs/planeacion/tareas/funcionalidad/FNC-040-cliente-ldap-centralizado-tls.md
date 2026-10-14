# FNC-040 — Cliente LDAP centralizado con TLS validado y esquema de OpenLDAP configurable

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | directorio |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-040-cliente-ldap-centralizado-tls` |
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
  - `config.py`: lectura y validación al arrancar de la configuración del directorio (ADR-004)
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
- `app/modules/directory/config.py`
- `tests/directory/`

## Reutilización
- `_escape_ldap_filter` de `app/modules/api/admin.py:579` se reemplaza por la función del cliente (la migración del llamador es de FNC-043)
- `ldap3` ya está en dependencias

## Variables y configuración
- Propuestas según ADR-004: `LDAP_URL` (nombre de host, esquema `ldaps://` o `ldap://` + StartTLS), `LDAP_CA_CERT_FILE`, `LDAP_BIND_DN`, `LDAP_BIND_PASSWORD` (sensible, Vaultwarden en staging/prod), `LDAP_USERS_BASE_DN`, `LDAP_GROUPS_BASE_DN`, `LDAP_USER_ATTR` (p. ej. `uid`), `LDAP_GROUP_OBJECT_CLASS`, `LDAP_GROUP_MEMBER_ATTR`, `LDAP_TIMEOUT_SECONDS`.
- Registrar en `VARIABLES.md` y `HISTORIAL.md`; actualizar `.env.example` con marcadores.

## Criterios de aceptación
- [ ] Con certificado no confiable la conexión falla con error controlado (prueba)
- [ ] Sin TLS configurado la app no arranca con el directorio activo (validación al arrancar)
- [ ] Un filtro con `*`, `(`, `)` o `\` se escapa (prueba)
- [ ] La contraseña de bind nunca se registra en logs ni en respuestas
- [ ] Criterios comunes backend (FNC-037)

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
