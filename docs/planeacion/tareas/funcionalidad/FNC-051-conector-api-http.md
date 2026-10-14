# FNC-051 — Conector tipo API HTTP

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | conectores |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-051-conector-api-http` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (ejecución remota con credenciales) |

## Contexto
- Tipo de conector API HTTP de F-CON-01
- Qué plataformas lo usan primero lo decide el dueño (pregunta P9); sin una plataforma piloto la tarea no se aprueba
- Requerimientos: F-CON-01

## Objetivo
- Implementar el tipo API HTTP sobre la interfaz de FNC-050: Llamadas HTTPS configurables (método, ruta, cuerpo con plantilla de campos permitidos) para crear y quitar la cuenta; autenticación por token o básica tomada de la credencial; códigos de estado mapeados a éxito, transitorio o permanente

## Alcance
- **Incluye:**
  - Implementación del tipo y su esquema de parámetros
  - Clasificación de errores en transitorios y permanentes
  - Pruebas con servidor simulado
  - Guía de configuración para la plataforma piloto en `docs/backend/conectores.md`
- **No incluye:**
  - Plataformas distintas de la piloto aprobada
  - Sincronizar o conciliar cuentas existentes (fuera de la v1)
  - Pantalla (DIS-022)

## Archivos previstos
- `app/modules/connectors/types/api_http.py`
- `tests/connectors/`
- `docs/backend/conectores.md`

## Reutilización
- Interfaz, registro y credenciales de FNC-050

## Variables y configuración
- `CONNECTOR_HTTP_TIMEOUT_SECONDS` y verificación TLS obligatoria (CA configurable por conector). Registrar.

## Integración (lineamiento técnico 11)
- Llamadas salientes a la plataforma; no aplica webhook ni polling

## Criterios de aceptación
- [ ] Otorgar y revocar contra el servidor simulado (pruebas)
- [ ] Entrada maliciosa (comillas, `;`, saltos de línea) no altera la operación (prueba de inyección)
- [ ] Verificación de TLS o de llave de host obligatoria (prueba)
- [ ] Probado contra la plataforma piloto en dev, con evidencia, o declarado no verificado con motivo
- [ ] Criterios comunes backend (FNC-037)

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-019, FNC-050, Respuesta del dueño a P9 (plataforma piloto)

## Riesgos y reversión
- Cada plataforma tiene su API o esquema: el tipo es genérico y lo específico va en parámetros.
- Reversión: desregistrar el tipo.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
