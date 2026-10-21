# DIS-033 — Mis solicitudes y mis accesos: refrescar solo con estados transitorios

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | solicitudes |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-20 |

## Contexto
- Contratos `solicitudes.md` y `accesos.md` (tabla Refresco): polling "mientras haya `pendiente` o `en_proceso`/`revocando`"
- DIS-014 refresca siempre al intervalo del usuario: `usePolling` no tiene opción para pausarse según los datos

## Objetivo
- `usePolling` admite pausarse según los datos
- `MyRequests` y `MyAccess` consultan periódicamente solo con estados transitorios en la página mostrada

## Impacto cruzado
- Origen ← DIS-014
- Incluye la opción de pausa (`enabled` o equivalente) en `usePolling` (`lib/use-polling.ts`): es frontend, va en esta misma tarea sin FNC aparte (decisión del orquestador)
- Elemento compartido: `usePolling` (DIS-015, DIS-018, DIS-022, DIS-024)
