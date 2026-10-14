# ADR-005 — Credenciales de conectores desde Vaultwarden en ejecución

- **Estatus:** Propuesta · **Fecha:** 2026-10-13 · **Tarea:** FNC-037 → FNC-050, FNC-068

## Contexto
- Cada conector necesita credenciales; no pueden ir en repo ni en BD (RNF-03)
- El agente nunca lee secretos

## Alternativas
- **A. API de Vaultwarden** con cuenta de servicio limitada a una colección; la BD guarda solo la referencia
- **B. CLI `bw`** en el servidor: sesión desbloqueada como dependencia frágil
- **C. Inyección al `EnvironmentFile`** en el despliegue: simple, pero cada conector nuevo exige redesplegar

## Recomendación
- A, con caché breve en memoria; C como alternativa si no se permite cuenta de servicio
