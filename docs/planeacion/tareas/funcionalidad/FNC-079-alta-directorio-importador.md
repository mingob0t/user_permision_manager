# FNC-079 — Alta de cuentas de directorio en el servidor (auth_source=ldap, sin contraseña) para el importador

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | usuarios |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-15 |

## Contexto
- Desde FNC-044, `POST /users` fija `auth_source=local` y rechaza `auth_source`; el importador de la pantalla `/users` (precarga desde el directorio) ya no puede dar de alta cuentas `ldap`.
- Falta una vía del servidor para registrar en el portal una cuenta que ya existe en el directorio: `auth_source=ldap`, `password_hash` nulo, rol `usuario`.
- Origen: revisión de FNC-044.

## Criterios de aceptación
- [ ] Endpoint o variante acordada por contrato (distinto de `POST /users/directory` de FNC-064, que crea la cuenta en OpenLDAP)
- [ ] La cuenta existe en el directorio antes de registrarla; sin contraseña local
- [ ] Prueba en la matriz y de alcance por área

## Impacto cruzado
- Origen ← FNC-044
- Relacionadas → FNC-064, FNC-069, DIS-018, DIS-019, FNC-077

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-15 | Creada como Propuesta (revisión de FNC-044) |
| 2026-10-19 | FNC-077 (En revisión): fuera de desarrollo `POST /users` ya crea `auth_source=ldap` sin contraseña, que se vincula al entrar por directorio/SSO; el alta del importador puede apoyarse en esto (falta comprobar que la cuenta existe en el directorio) |
