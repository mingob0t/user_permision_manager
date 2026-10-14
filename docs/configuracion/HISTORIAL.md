# Historial de cambios de variables y configuración

> Una fila por cambio de valor, de valor por defecto, de significado, de alta o de baja. **El motivo es obligatorio.** En los secretos no se escriben valores: solo "rotado". El mensaje de commit no reemplaza esta entrada.

| Fecha | Variable | Entorno | Antes | Después | Motivo | Tarea / ADR | Autor |
|---|---|---|---|---|---|---|---|
| 2026-10-13 | (todas las de VARIABLES.md) | todos | — | alta | Estructura inicial del proyecto | FNC-001 | — |
| 2026-10-13 | (todas las variables de entorno y constantes de VARIABLES.md) | todos | — | alta | Registro inicial de variables heredadas de NEXUS. Motivo: incorporación FNC-001 | FNC-001 | agente de documentación |
| 2026-10-13 | `APP_ENV`, `LOG_DIR`, `LOG_LEVEL`, `DB_PASSWORD`, `NEXT_PUBLIC_API_URL` | todos | alta (plantilla) | baja | Venían de la plantilla genérica y el código no las lee (la contraseña de BD es `DB_PASS`). Motivo: incorporación FNC-001 | FNC-001 | agente de documentación |
| 2026-10-14 | `DB_ENGINE`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASS` | todos | se leían en `app/__init__.py` | se leen en `app/utils/uri_bd.py` (misma regla, mismos valores) | Las migraciones de Alembic necesitan la misma URI que la app sin llamar a `create_app()` (ADR-002) | FNC-039 | desarrollador |
| 2026-10-14 | `SQLITE_URI_POR_DEFECTO`, `CARPETA_INSTANCIA` | todos | literal en `app/__init__.py` / — | constante con nombre (mismo valor) / alta | Nombrar el valor SQLite que comparten app y Alembic y su resolución en `instance/` (ADR-002) | FNC-039 | desarrollador |
| 2026-10-14 | `TRUSTED_PROXIES` | todos | solo SSO (`Remote-*`) | SSO y, en la auditoría, confianza en `X-Forwarded-For` (último salto) | Registrar la IP real del cliente y no la del proxy (SEG-25, SEC-AUD-04) | FNC-047 | desarrollador |
| 2026-10-14 | `ACTOR_SISTEMA` | todos | `SYSTEM` (literal) | `sistema` (constante) | El contrato `auditoria.md` v1 define `user = "sistema"` cuando actúa el sistema | FNC-047 | desarrollador |
| 2026-10-14 | `IP_INTERNA`, `FRAGMENTOS_SENSIBLES`, `VALOR_OMITIDO`, `AL_BORRAR_REFERENCIA` | todos | literal / — | constante con nombre (mismo valor) / alta | Auditoría ampliada sin datos sensibles y sin cascada al borrar (SEC-AUD-03, 05) | FNC-047 | desarrollador |
| 2026-10-14 | Largos de `audit_logs` (`user`, `action`, `target`) | todos | 100 / 50 / 100 | 255 / 150 / 255 | Un correo largo hacía fallar el INSERT en MySQL estricto y el evento se perdía (SEG-25) | FNC-047 | desarrollador |
| 2026-10-14 | `FRAGMENTOS_SENSIBLES`, `CAMPOS_NOMBRE_PAR`, `CAMPO_VALOR_PAR` | todos | sin `pass`, `pwd`, `passwd`, `key`, `private_key`, `otp`, `session`; sin forma par | con esos fragmentos (se quitan `bind_pass`/`ldap_pass`, ya cubiertos por `pass`) y forma `{key\|name, value}` | Hallazgo Bajo del revisor: credenciales con nombres cortos o en pares nombre/valor podían quedar en antes/después (SEC-AUD-05) | FNC-047 | desarrollador |
