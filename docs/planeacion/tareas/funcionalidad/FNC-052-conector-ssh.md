# FNC-052 — Conector tipo SSH

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
| **Rama** | `fnc/FNC-052-conector-ssh` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (ejecución remota con credenciales) |

## Contexto
- Tipo de conector SSH de F-CON-01
- Qué plataformas lo usan primero lo decide el dueño (pregunta P9); sin una plataforma piloto la tarea no se aprueba
- Requerimientos: F-CON-01

## Objetivo
- Implementar el tipo SSH sobre la interfaz de FNC-050: Ejecución de comandos predefinidos por plataforma (lista cerrada, sin interpolar texto libre en el *shell*; argumentos escapados) con llave o contraseña tomada de la credencial y verificación obligatoria de la llave del host (`known_hosts` por conector)

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
- `app/modules/connectors/types/ssh.py`
- `tests/connectors/`
- `docs/backend/conectores.md`

## Reutilización
- Interfaz, registro y credenciales de FNC-050

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `requirements.txt` | Dependencias | Backend completo | Pendiente |

## Variables y configuración
- `CONNECTOR_SSH_TIMEOUT_SECONDS`; dependencia SSH a fijar (p. ej. `paramiko`). Registrar.

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

## Requisitos de seguridad heredados de FNC-050 (auditor-seguridad)
- Resolver el DNS del host antes de conectar y rechazar si resuelve a una IP privada, de loopback, *link-local* o no enrutable (DNS *rebinding*); conectar a la IP ya validada, no volver a resolver.
- No seguir redirecciones ni saltos a otros hosts (SEC-CON-06 por analogía): sin `ProxyJump`/`ProxyCommand` ni reenvío de agente; `known_hosts` fijo (SEC-CON-04).
- Usar el host de `Destino` (ya normalizado, B1 de FNC-050) y la lista blanca `CONNECTOR_ALLOWED_HOSTS`; nunca un host de `params`.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-20 | Recomendaciones de auditor-seguridad sobre FNC-050 agregadas (sección «Requisitos de seguridad heredados de FNC-050») |
