# FNC-041 — Servicio de escritura en OpenLDAP: membresía de grupos y alta de cuentas

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
| **Rama** | `fnc/FNC-041-escritura-openldap-grupos-cuentas` |
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

## Criterios de aceptación
- [ ] Agregar y quitar son idempotentes (pruebas)
- [ ] Error permanente y transitorio clasificados (pruebas por tipo)
- [ ] Valores de usuario escapados al formar DN (prueba con caracteres especiales)
- [ ] Ninguna operación de borrado de cuentas en v1
- [ ] Criterios comunes backend (FNC-037)

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
