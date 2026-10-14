# DIS-022 — Configuración de conectores y bitácora de ejecuciones

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | configuracion-conectores |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `dis/DIS-022-configuracion-conectores-ejecuciones` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- El superadmin configura los conectores (tabla de pantallas, "Configuración"); no existe pantalla, y las ejecuciones fallidas no se ven
- Requerimientos: F-CON-01

## Objetivo
- Pantalla `/admin/connectors`: lista de plataformas `conector` con su configuración (tipo, host, parámetros, referencia de credencial — nunca el valor), probar conexión, y bitácora de ejecuciones con intentos y reintento manual

## Alcance
- **Incluye:**
  - Formulario dinámico por tipo de conector
  - Botón "Probar conexión" con resultado genérico
  - Bitácora filtrable y detalle de intentos
  - Reintentar según P10
  - Usa `usePolling` de FNC-071 (ADR-006): refresco con el intervalo de la preferencia del usuario, en pausa con la pestaña oculta.
- **No incluye:**
  - Editar ítems de Vaultwarden
  - Pestañas de Ajustes existentes

## Archivos previstos
- `frontend/src/components/connectors/connector-list.tsx`
- `frontend/src/components/connectors/connector-form.tsx`
- `frontend/src/components/connectors/jobs-log.tsx`
- `frontend/src/app/admin/connectors/page.tsx`

## Reutilización
- `Modal`, `Field`, `Select`, `Button`, `usePolling`

## Criterios de aceptación
- [ ] Ningún campo pide ni muestra contraseñas
- [ ] Criterios comunes de diseño (FNC-037)

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-024, FNC-025, FNC-069, FNC-070, FNC-071, FNC-061, FNC-062
- Contrato → docs/contratos/conectores-y-ejecuciones.md

## Riesgos y reversión
- Puede avanzar con los datos simulados de FNC-069; se integra después del backend.
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
