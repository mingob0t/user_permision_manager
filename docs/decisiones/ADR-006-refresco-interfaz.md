# ADR-006 — Refresco de datos en la interfaz

- **Estatus:** Propuesta · **Fecha:** 2026-10-13 · **Tarea:** FNC-037 → FNC-071

## Contexto
- Estados que cambian en el servidor: solicitudes, accesos `en_proceso`, pendientes
- Existe `pref_refresh_interval` (15–3600 s) sin uso; Gunicorn con workers síncronos

## Alternativas
- **A. HTTP polling** a la API propia con el intervalo del usuario, pausa en segundo plano y *backoff*
- **B. SSE**: menor latencia; requiere workers asíncronos o proceso aparte y ajuste de nginx

## Recomendación
- A (latencia tolerable; sin cambios de infraestructura)
