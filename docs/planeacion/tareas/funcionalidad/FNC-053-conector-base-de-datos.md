# FNC-053 — Conector tipo base de datos

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
| **Rama** | `fnc/FNC-053-conector-base-de-datos` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (ejecución remota con credenciales) |

## Contexto
- Tipo de conector BD de F-CON-01
- Qué plataformas lo usan primero lo decide el dueño (pregunta P9); sin una plataforma piloto la tarea no se aprueba
- Requerimientos: F-CON-01

## Objetivo
- Implementar el tipo BD sobre la interfaz de FNC-050: Sentencias parametrizadas predefinidas por plataforma (sin SQL libre) para crear o desactivar la cuenta en la BD de la plataforma; motores admitidos según P9

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
- `app/modules/connectors/types/base_de_datos.py`
- `tests/connectors/`
- `docs/backend/conectores.md`

## Reutilización
- Interfaz, registro y credenciales de FNC-050

## Variables y configuración
- `CONNECTOR_DB_TIMEOUT_SECONDS`; controlador por motor (PyMySQL ya existe). Registrar.

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
