# DIS-038 — Menú móvil y `Modal`: token de velo y bloqueo de desplazamiento

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | componentes |
| **Prioridad** | Baja |
| **Estatus** | En revisión |
| **Aprobada** | 2026-10-26 (modo autónomo; junto con DIS-031 y DIS-043) |
| **Rama** | `dis/DIS-031-038-modal` (desde `develop`, d642e1f) |
| **Creada** | 2026-10-21 |

## Contexto
- `MobileMenu` (DIS-025) no tiene velo detrás del panel ni bloquea el desplazamiento del fondo
- El único velo existente es `bg-black/60` en `Modal` (color literal) y el bloqueo usa `document.body.style.overflow` (prohibido `el.style.*`)

## Objetivo
- Token de rol para el velo (p. ej. `--color-scrim`) con valor por tema, usado por `Modal` y `MobileMenu`
- Bloqueo de desplazamiento con clase o atributo en `body` (p. ej. `data-scroll-lock`), sin `el.style`

## Implementación
| Archivo | Cambio |
|---|---|
| `frontend/src/styles/tokens.css` | Token nuevo `--color-overlay: 0 0 0 / 0.6` en los 7 bloques de tema (claro, SO oscuro, `html.dark`, emerald, obsidian, rose, violet) |
| `frontend/tailwind.config.ts` | Utilidad `overlay` (`rgb(var(--color-overlay))`; el token ya trae su opacidad) |
| `frontend/src/styles/global.css` | `html.scroll-bloqueado, html.scroll-bloqueado body { overflow: hidden }` |
| `frontend/src/lib/use-scroll-lock.ts` | Nuevo: `useScrollLock(activo)` pone y quita la clase en `<html>` con `classList`, con contador (dos diálogos: se quita al cerrar el último) |
| `frontend/src/components/form.tsx` | `Modal`: `bg-black/60` → `bg-overlay`; `document.body.style.overflow` → `useScrollLock()` |
| `frontend/src/components/mobile-menu.tsx` | Velo `fixed inset-0 z-40 bg-overlay` (`aria-hidden`) detrás del panel; su clic cierra por el oyente de clic fuera; `useScrollLock(open)` |
| `frontend/tests/accesibilidad/velo.test.ts` | Nuevo (35): opacidad parcial y panel distinguible del velo (relleno o borde >= 3:1) sobre la página y sobre `Card`, en los 7 temas, para `Modal` y menú |
| `frontend/tests/accesibilidad/colores-literales.excepciones.ts` | `form.tsx` sale de las excepciones (paleta 1 → 0) |
| `frontend/tests/components/modal.test.tsx`, `menu-movil.test.tsx` | Velo por token, clase en `<html>` sin `style`, contador con dos diálogos, clic en el velo cierra |

## Decisiones
Decisión del orquestador (pendiente de validar en la prueba de concepto), en todas:
| # | Decisión | Motivo |
|---|---|---|
| 1 | Nombre `--color-overlay` (rol), con la opacidad dentro del valor (`R G B / a`, como `--badge-*-bg`) | El velo siempre lleva opacidad; una sola utilidad `bg-overlay` |
| 2 | Mismo valor `0 0 0 / 0.6` en los 7 temas, declarado en cada bloque | Es el `bg-black/60` actual: sin cambio visual hasta el diseño del dueño; cada tema puede ajustarlo |
| 3 | Criterio de contraste: el panel se distingue del velo por su relleno o su borde >= 3:1 (no textual) | El velo no es texto. Medido: temas claros, relleno 5,74–6,13:1; oscuros, borde 3,29–3,56:1 (`Modal`). Un velo más claro en oscuros bajaría el borde de 3:1 |
| 4 | Clase en `<html>` (`scroll-bloqueado`), no atributo en `body` | La ficha admite cualquiera; el selector cubre `html` y `body` |
| 5 | El velo del menú cubre también la cabecera (z-40, el panel z-50) | Un clic fuera del panel, incluido el botón "Menú", cierra |

## Observación (no corregida, fuera de alcance)
- `global.css` ya pone `overflow: hidden` en `html` y `body` (heredado). El desplazamiento real lo hace otro contenedor o no lo hay; el bloqueo por clase reproduce lo que hacía `Modal` con `body.style`, pero su efecto visible depende de eso. Propuesta DIS-044.

## Impacto en elementos compartidos
| Elemento | Cambio | Usado en |
|---|---|---|
| `--color-overlay` (nuevo) | Alta en los 7 temas | `Modal`, `MobileMenu` |
| `Modal` (`form.tsx`) | Velo por token y bloqueo por clase | Todas las pantallas con diálogo: lista completa en DIS-031 (`/platforms`, `/approvals`, `/areas`, `/admin/platforms`, `/users`, `/audit` e historiales, `/admin/connectors`, `/notifications`) |
| `MobileMenu` | Velo y bloqueo | `AppShell`: todas las autenticadas bajo `md` |
| `global.css` | Regla nueva `html.scroll-bloqueado` | Solo se activa con la clase |
| `tailwind.config.ts` | Utilidad `overlay` | `Modal`, `MobileMenu` |

Reporte de `impacto.py`: en DIS-031 (misma rama).

## Verificación
| Comando (en `frontend/`) | Resultado |
|---|---|
| `npm run typecheck` / `npm run lint` | salida 0 / salida 0 |
| `npx vitest run` | salida 0: 1194 pasan (35 de `velo.test.ts`); fallas de contraste conocidas: 0 |
| `npx next build` | salida 0; `.bg-overlay{background-color:rgb(var(--color-overlay))}` y `html.scroll-bloqueado` en el CSS generado |
| `grep` de estilos inline, colores literales e IPs en lo agregado | sin coincidencias (los valores del token están en `tokens.css`) |

No verificado: navegador real (velo y bloqueo en temas claro y oscuro, móvil y escritorio). Sin auditores (por instrucción).

## Impacto cruzado
- Origen ← DIS-025; relacionada con DIS-031

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-21 | Creada como Propuesta desde DIS-025 |
| 2026-10-26 | Aprobada en modo autónomo y En curso, junto con DIS-031 y DIS-043 |
| 2026-10-26 | Token `--color-overlay` (7 temas), `useScrollLock` por clase en `<html>`, velo en `Modal` y menú móvil; prueba de contraste del velo; propuesta DIS-044. En revisión |
