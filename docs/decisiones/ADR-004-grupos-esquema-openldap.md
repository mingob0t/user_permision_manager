# ADR-004 — Grupos y esquema de OpenLDAP

- **Estatus:** Propuesta · **Fecha:** 2026-10-13 · **Tarea:** FNC-037 → FNC-040, FNC-041, FNC-043, FNC-046, FNC-064

## Contexto
- OpenLDAP es la fuente de verdad; dos grupos por plataforma (usuario y admin)
- El código usa atributos de AD (`sAMAccountName`, `memberOf`) y TLS sin validar (SEG-13)

## Decisiones a tomar (pregunta P3)
- Clase de grupo: `groupOfNames`/`member` (exige ≥1 miembro) o `posixGroup`/`memberUid` o `groupOfUniqueNames`
- Convención de nombres y OUs (p. ej. `cn=<plataforma>-<nivel>,ou=<area>,ou=plataformas,<base>`)
- Quién crea los grupos: portal o administrador del directorio
- Cuenta de servicio con escritura acotada a la OU de grupos y de usuarios
- Atributos de alta de cuenta (`uid`, `cn`, `sn`, `mail`, clases)
- Origen de la configuración: conexión y credencial por variables (Vaultwarden en staging/prod); esquema no sensible por variables o BD

## Recomendación
- Configuración por variables; credencial nunca en BD; LDAPS o StartTLS con `CERT_REQUIRED`; grupos creados por el administrador del directorio en v1
