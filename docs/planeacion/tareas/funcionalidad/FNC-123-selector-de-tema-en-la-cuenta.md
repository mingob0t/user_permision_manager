# FNC-123 — Selector de tema: leer y guardar el tema en la cuenta

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | web |
| **Agente** | desarrollador |
| **Fase** | 4 |
| **Módulo / Área** | tema |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-27 |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- FNC-122 guarda el tema en la cuenta: `GET /me` devuelve `preferences.theme` y `PUT /me/preferences` acepta `{"theme": "<id>"}` (ids de `frontend/src/lib/tema.ts`; valor inválido → `422 validacion`).
- Hoy el selector (FNC-032) solo usa `localStorage`.

## Alcance
- Al iniciar sesión, aplicar `preferences.theme` de `/me`.
- Al elegir un tema, guardarlo con `PUT /me/preferences` (error visible si falla) y mantener `localStorage` como respaldo antes de iniciar sesión.
- Pruebas del selector. Sin cambios visuales ni de tokens.

## Impacto cruzado
- Origen ← FNC-122
- Elementos compartidos: `tema.ts`, selector de tema, tipo de `/me` en el frontend.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-27 | Creada como Propuesta desde FNC-122 |
