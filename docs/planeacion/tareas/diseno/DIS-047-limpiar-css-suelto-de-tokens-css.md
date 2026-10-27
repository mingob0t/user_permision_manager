# DIS-047 — Limpiar el CSS suelto de `tokens.css` (`.dt-*`, `table.dataTable`, `.animate-shake`)

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | estilos |
| **Prioridad** | Baja |
| **Estatus** | En revisión |
| **Rama** | `dis/DIS-047-css-suelto-tokens` |
| **Creada** | 2026-10-27 |

## Contexto
- `tokens.css` mezcla tokens con reglas de componente que nadie usa: `.dt-container`, `.dt-layout-row…`, `table.dataTable tbody tr`, `.animate-shake` y `@keyframes shake` (origen: DIS-009, que solo depuró `components.css` y `global.css`).
- `html, body { background; color }` también está ahí y puede pasar a `global.css`.

## Objetivo
- Borrar lo muerto y dejar `tokens.css` solo con variables; extender `css-sin-uso.test.ts` para cubrirlo.

## Impacto cruzado
- Origen ← DIS-009

## Implementación
- `tokens.css` −50 líneas: se borran `.dt-container`, `.dt-layout-row…`, `table.dataTable tbody tr`, `.animate-shake` y `@keyframes shake`. Búsqueda en `frontend/` (src, tests, config): sin ningún llamador fuera del propio archivo.
- `html, body { color; margin; padding }` pasa a `global.css` (se carga justo después; `background-color` ya estaba allí). Sin cambio visible.
- `css-sin-uso.test.ts`: bloque nuevo que exige `tokens.css` solo con declaraciones `--*`, sin `@keyframes` y con selectores `:root`/`html`.
- Tokens: ninguno creado, cambiado ni eliminado (VARIABLES e HISTORIAL sin cambios).

## Decisiones
- Decisión del orquestador (pendiente de validar en la prueba de concepto): aprobada en modo autónomo; lo muerto se borra, `html, body` va a `global.css`; la prueba nueva es aparte porque `tokens.css` no puede pasar por la regla de «clase con llamador» (`html.dark`, `theme-*` los pone JS).

## Impacto en elementos compartidos
- `tokens.css` y `global.css` se cargan en todas las pantallas: solo se movió `html, body`, mismas declaraciones y mismo orden de cascada. Sin otros consumidores de lo borrado.

## Verificación
- typecheck 0, lint 0, vitest 0 (40 archivos, 1496 pruebas; incluye css-sin-uso y el resto de accesibilidad), build 0.
- No verificado en navegador.
