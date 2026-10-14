# FNC-050 — Conectores: interfaz, registro, configuración por plataforma y credenciales desde Vaultwarden (según ADR-005)

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | conectores |
| **Prioridad** | Alta |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-050-conectores-interfaz-configuracion-credenciales` |
| **Requiere migración BD** | Sí (tabla `platform_connectors`) |
| **Requiere auditor-seguridad** | Sí (credenciales de sistemas externos) |

## Contexto
- Las plataformas sin Authelia necesitan que el portal cree o quite la cuenta con un conector (API, SSH o BD) (F-CON-01)
- Las credenciales no pueden estar en el repositorio ni en claro en la BD (RNF-03, SEG-08)
- Requerimientos: F-CON-01, RNF-03

## Objetivo
- Definir la interfaz común de conector (`grant`, `revoke`, `check` opcional), su registro por tipo, el modelo de configuración por plataforma (tipo, nombre de host, parámetros no sensibles, **referencia** al ítem de Vaultwarden) y el resolvedor de credenciales en ejecución que decida ADR-005, conectado al ejecutor de FNC-049 como proveedor `conector`

## Alcance
- **Incluye:**
  - Tabla `platform_connectors` (una por plataforma `conector`): tipo, host por nombre, puerto, parámetros JSON validados por esquema del tipo, referencia de credencial, activo
  - `base.py` (interfaz y resultado tipificado igual que FNC-041), `registry.py`, `credentials.py` (resolvedor por ADR-005, con caché breve en memoria y sin registrar valores)
  - Proveedor `conector` del ejecutor que carga la configuración y llama al tipo correspondiente
  - Un conector de prueba (`noop`) solo para pruebas y dev
- **No incluye:**
  - Tipos concretos API, SSH, BD (FNC-051 a FNC-053)
  - Endpoints de configuración (FNC-061)
  - Configuración de Vaultwarden en servidores (FNC-068)

## Archivos previstos
- `app/modules/connectors/models.py`
- `app/modules/connectors/base.py`
- `app/modules/connectors/registry.py`
- `app/modules/connectors/credentials.py`
- `app/modules/connectors/provider.py`
- Migración (ADR-002)
- `tests/connectors/`

## Reutilización
- Registro de proveedores y resultado tipificado de FNC-049

## Variables y configuración
- Las de ADR-005 para acceder a Vaultwarden (p. ej. `VAULTWARDEN_URL`, identificador y secreto de la cuenta de servicio, sensibles) y `CONNECTOR_CREDENTIAL_CACHE_SECONDS` — registrar.

## Integración (lineamiento técnico 11)
- Llamadas salientes del portal a cada plataforma (no se reciben cambios); no aplica webhook ni polling
- Tiempo de espera por tipo de conector como variable registrada

## Criterios de aceptación
- [ ] La tabla no guarda secretos, solo referencias (prueba de esquema)
- [ ] Una referencia inexistente en Vaultwarden da error permanente sin exponer detalles (prueba con resolvedor simulado)
- [ ] El conector `noop` recorre el flujo completo otorgar → revocar con el ejecutor (prueba)
- [ ] Ningún valor de credencial aparece en logs, auditoría ni respuestas (prueba)
- [ ] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Genera → FNC-051, FNC-052, FNC-053, FNC-061, FNC-068
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-049, FNC-046, ADR-005

## Riesgos y reversión
- Disponibilidad de Vaultwarden en el camino crítico: error transitorio con reintento.
- Reversión: bajar la migración; las plataformas `conector` quedan sin aprovisionar.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
