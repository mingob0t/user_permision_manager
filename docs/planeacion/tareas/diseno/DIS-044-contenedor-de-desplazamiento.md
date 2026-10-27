# DIS-044 — Verificar qué contenedor se desplaza con `html, body { overflow: hidden }`

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | componentes |
| **Prioridad** | Baja |
| **Estatus** | Hecha |
| **Aprobada** | 2026-10-26 (modo autónomo; H1 de auditor-accesibilidad, resuelta dentro de DIS-031/DIS-038) |
| **Rama** | `dis/DIS-031-038-modal` |
| **Creada** | 2026-10-26 |

## Contexto
- `global.css` (heredado) pone `overflow: hidden` en `html` y `body`; `AppShell` usa `min-h-screen` sin contenedor con `overflow-y-auto`
- DIS-038 bloquea el desplazamiento con la clase `html.scroll-bloqueado` (`html` y `body`), igual que antes hacía `Modal` con `body.style`; su efecto visible depende de qué elemento se desplaza

## Objetivo
- Comprobar en navegador (móvil y escritorio) si las páginas largas se desplazan y con qué elemento
- Si es otro contenedor, que `scroll-bloqueado` lo cubra; si no se desplaza nada, corregir el marco con el dueño

## Implementación
| Archivo | Cambio |
|---|---|
| `frontend/src/lib/raiz-app.ts` | Nuevo: `RAIZ_APP_ID` (sin `'use client'`, lo lee `layout.tsx`) |
| `frontend/src/app/layout.tsx` | `<div id="raiz-app" data-desplazable class="h-dvh overflow-y-auto">` envuelve todas las páginas: se desplazan las que no usan `AppShell` |
| `frontend/src/components/app-shell.tsx` | Marco `flex h-dvh`; columna `min-h-0`; `<main data-desplazable tabIndex={-1} class="min-h-0 flex-1 overflow-y-auto p-6 outline-none">`; barra lateral con `overflow-y-auto` |
| `frontend/src/lib/use-scroll-lock.ts` | La clase `scroll-bloqueado` e `inert` van en la raíz; ya no en `html` |
| `frontend/src/styles/global.css` | `.scroll-bloqueado[data-desplazable], .scroll-bloqueado [data-desplazable] { overflow: hidden }` (gana a `overflow-y-auto` por especificidad) |
| Pruebas | `raiz-desplazable.test.tsx` (nuevo: raíz con `h-dvh overflow-y-auto`, páginas sin `AppShell` sin altura propia ni recorte), `menu-movil.test.tsx` (`<main>` desplazable, bloqueo e `inert`), `modal.test.tsx` (regla CSS, bloqueo e `inert`) |

## Decisiones
Decisión del orquestador (pendiente de validar en la prueba de concepto):
| # | Decisión | Motivo |
|---|---|---|
| 1 | Se conserva `overflow: hidden` de `html`/`body` y se desplaza una raíz propia | Es el diseño heredado ("marco estable"); la raíz permite marcarla `inert` sin tocar los portales |
| 2 | Con `AppShell`, cabecera y barra lateral fijas; solo se desplaza `<main>` | Lo pide el hallazgo; la barra lateral se desplaza aparte si no cabe |
| 3 | Atributo `data-desplazable` para marcar los contenedores | Un solo selector bloquea los dos niveles |

## Pantallas afectadas
- `AppShell`: `/`, `/platforms`, `/requests`, `/favorites`, `/notifications`, `/approvals`, `/admin/platforms`, `/areas`, `/users`, `/inventory`, `/audit`, `/audit/users/[id]`, `/audit/platforms/[id]`, `/admin/connectors`, `/settings`.
- Raíz de `layout.tsx`: todas, incluidas `/login`, `/logout`, 404 y error.

## Verificación
- typecheck 0, lint 0, vitest 0 (1207 pasan; fallas conocidas 0), `next build` 0 (regla de bloqueo en el CSS generado).
- No verificado en navegador: desplazamiento real en móvil y escritorio, ni la cabecera fija.

## Impacto cruzado
- Origen ← DIS-038; H1 de auditor-accesibilidad de DIS-031/038/043

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-26 | Creada como Propuesta desde DIS-038 |
| 2026-10-26 | Aprobada y resuelta en `dis/DIS-031-038-modal` (H1): raíz y `<main>` desplazables, bloqueo e `inert` sobre la raíz. En revisión |
