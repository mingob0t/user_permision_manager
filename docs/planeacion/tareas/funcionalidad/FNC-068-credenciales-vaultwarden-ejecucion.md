# FNC-068 — Credenciales de conectores y del bind LDAP desde Vaultwarden en staging y producción

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | infra |
| **Agente** | devops |
| **Fase** | 3 |
| **Módulo / Área** | secretos |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-068-credenciales-vaultwarden-ejecucion` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (gestión de secretos) |

## Contexto
- Las credenciales de los conectores y la de bind con escritura en OpenLDAP no pueden estar en el repositorio ni en la BD (RNF-03)
- ADR-005 decide cómo las obtiene la app en ejecución
- Requerimientos: F-CON-01, RNF-03

## Objetivo
- Preparar en staging y producción el acceso de la app a Vaultwarden (cuenta de servicio de mínimo privilegio o inyección al `EnvironmentFile`, según ADR-005), con su rotación documentada

## Alcance
- **Incluye:**
  - Cuenta de servicio o mecanismo de ADR-005 con acceso solo a la colección del portal
  - Procedimiento de alta de un ítem de conector y de rotación en `docs/operacion/`
  - Verificación de que el agente ni el repositorio contienen valores
- **No incluye:**
  - Crear los ítems de cada plataforma (lo hace el superadmin)
  - Código del resolvedor (FNC-050)

## Archivos previstos
- `deploy/` (solo lo que ADR-005 requiera)
- `docs/operacion/ENTORNOS.md`
- `docs/operacion/SECRETOS.md` (nuevo, sin valores)

## Reutilización
- Vaultwarden existente del dueño

## Variables y configuración
- Las de ADR-005, marcadas como sensibles en `VARIABLES.md`.

## Criterios de aceptación
- [ ] La app de staging resuelve una credencial de prueba sin que su valor aparezca en logs (evidencia)
- [ ] Procedimiento de rotación probado una vez
- [ ] Criterios comunes infra (FNC-037)

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, ADR-005, FNC-050

## Riesgos y reversión
- Reversión: retirar la cuenta de servicio.

## Requisitos de seguridad heredados de FNC-050 (auditor-seguridad)
- Al rotar una credencial, llamar a `connectors.credenciales.limpiar_cache()` (o esperar `CONNECTOR_CREDENTIAL_CACHE_SECONDS`) para no seguir usando el valor anterior (B4).
- Implementar `ProveedorSecretosVaultwarden.obtener` respetando el mapeo de errores: no encontrada → `CredencialNoEncontrada`; caído → `GestorNoDisponible`; sin configurar → `GestorNoConfigurado`; nunca el valor en el texto.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-20 | Recomendaciones de auditor-seguridad sobre FNC-050 agregadas (sección «Requisitos de seguridad heredados de FNC-050») |
