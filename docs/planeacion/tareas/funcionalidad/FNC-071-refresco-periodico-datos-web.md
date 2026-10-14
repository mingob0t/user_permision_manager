# FNC-071 — Refresco periódico de datos con pausa en segundo plano (según ADR-006)

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | web |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | lib-datos |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-13 |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-071-refresco-periodico-datos-web` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- Los estados cambian en el servidor sin intervención del usuario (solicitud aprobada, acceso `en_proceso` → `activo`, nuevos pendientes)
- Existe la preferencia `pref_refresh_interval` (15–3600 s) pero ninguna pantalla la usa, y `useAsync` solo carga una vez
- Requerimientos: Pantallas Inicio, Mis solicitudes, Aprobaciones, Usuarios y accesos, Conectores

## Objetivo
- Un hook `usePolling` que extiende `useAsync` según ADR-006: intervalo de la preferencia del usuario, pausa con la pestaña oculta, *backoff* exponencial con *jitter* ante errores y parada al desmontar

## Alcance
- **Incluye:**
  - `frontend/src/lib/use-polling.ts` y sus pruebas con temporizadores simulados
- **No incluye:**
  - WebSocket o SSE (solo si ADR-006 los elige; sería otra tarea backend y web)
  - Aplicarlo a pantallas existentes

## Archivos previstos
- `frontend/src/lib/use-polling.ts`
- `frontend/src/lib/__tests__/use-polling.test.ts`

## Reutilización
- `useAsync`, preferencia `refresh_interval` de la sesión

## Integración (lineamiento técnico 11)
- Datos que cambian en nuestro propio servidor y se muestran en nuestro frontend
- Según ADR-006 (recomendado): **HTTP polling periódico** contra la API propia con el intervalo `pref_refresh_interval` (ya registrado, 15–3600 s), pausa cuando la pestaña está oculta (`visibilitychange`), *backoff* exponencial con *jitter* ante errores y sin peticiones al desmontar
- Motivo: latencia tolerable de segundos a minutos, pocos recursos por pantalla, y Gunicorn con workers síncronos no conviene para conexiones SSE largas

## Criterios de aceptación
- [ ] Con la pestaña oculta no hay peticiones (prueba)
- [ ] Tras errores el intervalo crece hasta un máximo y se restablece al primer éxito (prueba)
- [ ] El intervalo respeta la preferencia del usuario (prueba)
- [ ] Criterios comunes web (FNC-037)

## Impacto cruzado
- Genera → DIS-014, DIS-015, DIS-018, DIS-022, DIS-024
- Origen ← FNC-037
- Depende de → FNC-036, FNC-024, FNC-025, ADR-006, FNC-069

## Riesgos y reversión
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
