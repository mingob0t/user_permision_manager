# FNC-071 — Refresco periódico de datos con pausa en segundo plano (según ADR-006)

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | web |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | lib-datos |
| **Prioridad** | Media |
| **Estatus** | En revisión |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Commit local, sin push |
| **Rama** | `fnc/FNC-071-refresco-periodico` (worktree `pokemon-wt-071`) |
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
- `frontend/tests/lib/use-polling.test.ts` (Vitest solo incluye `tests/**`; ver decisiones)

## Reutilización
- `useAsync`, preferencia `refresh_interval` de la sesión

## Integración (lineamiento técnico 11)
- Datos que cambian en nuestro propio servidor y se muestran en nuestro frontend
- Según ADR-006 (recomendado): **HTTP polling periódico** contra la API propia con el intervalo `pref_refresh_interval` (ya registrado, 15–3600 s), pausa cuando la pestaña está oculta (`visibilitychange`), *backoff* exponencial con *jitter* ante errores y sin peticiones al desmontar
- Motivo: latencia tolerable de segundos a minutos, pocos recursos por pantalla, y Gunicorn con workers síncronos no conviene para conexiones SSE largas

## Implementación
- `usePolling(load, { intervalSeconds, deps })` compone sobre `useAsync` (sin cambiarlo); devuelve `data`, `loading`, `error`, `refresh`
- Constantes: `INTERVALO_POLLING_MIN_S` 15, `INTERVALO_POLLING_MAX_S` 3600, `INTERVALO_POLLING_POR_DEFECTO_S` 60, `JITTER_POLLING` 0.1
- Funciones puras exportadas: `normalizarIntervalo`, `esperaPolling`
- Sin consulta en curso se programa la siguiente; con pestaña oculta no hay temporizador; al volver, consulta inmediata
- Error: espera = intervalo × 2^fallos hasta 3600 s, menos *jitter* de hasta 10 %; éxito restablece; `401` detiene
- `refresh()` durante una consulta se encola y se ejecuta al terminar (sin solapar)

## Decisiones del orquestador (pendientes de validar en la prueba de concepto)
- El intervalo llega por parámetro (`session.preferences.refresh_interval`); `lib/` no importa `useSession` de `components/`
- Sin preferencia o inválida: 60 s (por defecto del backend); fuera de rango se acota a 15–3600 s
- *Jitter* restado (0–10 %) para no superar nunca el máximo de 3600 s; solo en esperas tras error
- La carga inicial al montar ocurre aunque la pestaña esté oculta (la hace `useAsync`); solo se pausa el polling
- `401` detiene; `refresh()` lo reintenta; `403` y otros errores siguen con *backoff*
- `loading` es `true` en cada consulta y `data` conserva el valor anterior; la pantalla muestra carga solo sin datos
- Pruebas en `frontend/tests/lib/` en lugar de `src/lib/__tests__/` (configuración vigente de Vitest)

## Verificación
| Comando (en `frontend/`) | Resultado real |
|---|---|
| `npm ci` | código 0 |
| `npx vitest run tests/lib/use-polling.test.ts` | 10 passed, código 0 |
| `npm test` | 9 archivos, 234 passed, 88 expected fail (conocidas de contraste), código 0 |
| `npm run lint` | sin avisos ni errores, código 0 |
| `npx eslint tests/lib/use-polling.test.ts` | código 0 |
| `npm run typecheck` | código 0 |
| `npm run build` | código 0 |
| Mutaciones (quitar pausa, quitar *backoff*, quitar cola de `refresh`, quitar parada por 401) | cada una: 1 failed (las pruebas detectan la regresión); código restaurado |

- No verificado: en navegador ni contra el backend real (ninguna pantalla usa aún el hook; lo aplican DIS-014/015/018/022/024)
- No se lanzaron `tester` ni `revisor` (indicación del orquestador)

## Impacto en elementos compartidos
Salida real de `impacto.py` (contra `develop`, 2026-10-19):

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `avanzar` | función | `frontend/tests/lib/use-polling.test.ts` | `frontend/src/lib/access/client.ts` | frontend/src | ☑ homónimo |

- `avanzar` es una función local de la prueba; en `client.ts` solo aparece la palabra en un comentario ("para avanzar pantallas"): falso positivo
- Elementos compartidos reales modificados: ninguno (`useAsync` se reutiliza sin cambios; `usePolling` es nuevo y aún sin usos)

## Commits / PR
- Commit local `[FNC-071]` en `fnc/FNC-071-refresco-periodico`; sin push, merge ni PR

## Criterios de aceptación
- [x] Con la pestaña oculta no hay peticiones (prueba `con la pestaña oculta no consulta…`)
- [x] Tras errores el intervalo crece hasta un máximo y se restablece al primer éxito (prueba de *backoff*)
- [x] El intervalo respeta la preferencia del usuario (pruebas de intervalo y mínimo de 15 s)
- [ ] Criterios comunes web (FNC-037): sin UI en esta tarea; aplican a las pantallas DIS

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
| 2026-10-19 | Aprobada (modo autónomo, vía orquestador); implementada; En revisión |
