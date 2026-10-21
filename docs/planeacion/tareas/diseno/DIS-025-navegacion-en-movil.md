# DIS-025 — Navegación en móvil

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | navegacion |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Creada** | 2026-10-19 |
| **Estatus Git** | Commit local, sin push |
| **Rama** | `dis/DIS-025-navegacion-movil` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- El menú lateral de `app-shell.tsx` está oculto bajo `md` (`hidden md:block`) sin alternativa (deuda 8 del frontend)
- Con FNC-070 el menú tiene 13 entradas por rol; en móvil no hay forma de navegar

## Objetivo
- Menú accesible en móvil que reutilice `NAV` y `meetsRequirement` (mismas entradas por rol)

## Alcance
- **Incluye:** botón de menú en la cabecera bajo `md` con panel de navegación, foco y cierre con teclado
- **No incluye:** cambiar entradas ni permisos del menú

## Archivos previstos
- `frontend/src/components/app-shell.tsx`

## Archivos cambiados
- `frontend/src/components/mobile-menu.tsx` (nuevo): botón y panel, cierre, foco y trampa de Tab
- `frontend/src/components/app-shell.tsx`: `Nav` acepta `touch` y `onNavigate`; `MobileMenu` en la cabecera
- `frontend/tests/components/menu-movil.test.tsx` (nuevo): 13 pruebas
- Docs: `docs/frontend/README.md`, `docs/estandarizacion/03-reutilizacion.md`, `CHANGELOG.md`, `docs/logs/2026-10-21.md`, tablero

## Decisiones (decisión del orquestador, pendiente de validar en la prueba de concepto)
| # | Decisión | Motivo |
|---|---|---|
| 1 | Componente nuevo `MobileMenu` en archivo propio; `Nav` se reutiliza como hijo (render prop `close`) | Una responsabilidad por archivo; la lista `NAV` y el filtro por rol no se duplican |
| 2 | Panel lateral izquierdo `role="dialog"` `aria-modal="true"`, `aria-label="Menú"`, con el mismo `aria-label="Principal"` en su `nav` | Mismo landmark que la barra lateral; solo uno es visible por breakpoint |
| 3 | Cerrado = contenedor con atributo `hidden` (sin clase de `display` propia) | `aria-controls` siempre apunta a un elemento existente; el panel no es accesible cerrado |
| 4 | Botón con texto visible "Menú" y botón "Cerrar" dentro del panel, ambos de 48 px, clases del botón "Salir" | Sin icono nuevo; clases existentes; el dueño hará el diseño final |
| 5 | Sin velo oscuro detrás del panel; borde, `bg-panel-fill` y `shadow-2xl` | El único velo existente es `bg-black/60` (color literal, la prueba de tope lo rechaza); no se crea token sin diseño del dueño → DIS-038 |
| 6 | Sin bloqueo del desplazamiento del fondo | `Modal` lo hace con `document.body.style` (prohibido `el.style.*`); queda en DIS-038 |
| 7 | Clic fuera por `pointerdown` en `document` (fuera del panel y del botón) | Sin velo no hay elemento que reciba el clic |
| 8 | Trampa de foco mínima y local (Tab/Mayús+Tab ciclan; si el foco está fuera, vuelve al panel) | No hay patrón en el proyecto; DIS-031 la definirá para `Modal` y este menú debería converger |
| 9 | Al cerrar por cualquier vía (también clic fuera y al elegir opción) el foco vuelve al botón | Lo pide la tarea; comportamiento único y predecible |
| 10 | Enlaces móviles con `flex min-h-12 items-center` solo con `touch`; la barra lateral conserva su cadena de clases exacta | En escritorio no cambia nada |

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `AppShell` (`app-shell.tsx`: `Nav` con props opcionales y cabecera con `MobileMenu`) | Layout | Todas las páginas autenticadas: `/`, `/platforms`, `/requests`, `/favorites`, `/notifications`, `/approvals`, `/admin/platforms`, `/areas`, `/users`, `/inventory`, `/audit`, `/audit/users/[id]`, `/audit/platforms/[id]`, `/admin/connectors`, `/settings` | Pendiente (validar cabecera en móvil y que escritorio no cambió) |

Salida de `python3 ~/.claude/agentes/herramientas/impacto.py` (2026-10-21):

> **Impacto en elementos compartidos:** ninguno detectado (comparado contra `develop`; 5 archivos cambiados).

- La herramienta no detecta `AppShell` como compartido; se lista arriba a mano (15 páginas de `frontend/src/app`)

## Criterios de aceptación
- [x] Bajo `md` se navega a todas las entradas del rol (prueba por rol: mismas entradas que la barra lateral)
- [ ] Criterios comunes web (FNC-037): pruebas en verde; temas, AA medido y navegador sin verificar

## Verificación (2026-10-21, en `frontend/`)
| Comando | Resultado |
|---|---|
| `npm run typecheck` | salida 0 |
| `npm run lint` | salida 0, sin avisos |
| `npx vitest run` | salida 0; 24 archivos, 802 passed + 25 expected fail (las 25 conocidas, sin aumento) |
| `npm run build` | salida 0 |
| `grep` de `style=`, `<style`, `.style.`, `style={{`, hex, `rgb(`, `white`/`black`, IPs en los dos componentes | sin coincidencias |

- Pruebas nuevas (`menu-movil.test.tsx`): estado inicial y `aria-controls`; apertura con foco en el primer enlace y `aria-expanded`; Escape con foco de vuelta; elegir opción; clic fuera y dentro; botón Cerrar y segundo clic; Tab y Mayús+Tab atrapados; mismas entradas por rol (3 roles); usuario sin entradas de admin; `aria-current="page"`; 48 px en móvil y sin cambio en la barra lateral
- **No verificado:** navegador (tema claro y oscuro, móvil y escritorio): no se levantó la app con sesión. Contraste: solo se reutilizan pares ya usados en la barra lateral y la cabecera (`text-label`, `text-primary-text` sobre `bg-panel-fill`), sin medición nueva
- Sin revisor, tester ni auditores (indicación del orquestador)

## Impacto cruzado
- Origen ← FNC-070 (revisión)
- Genera → DIS-038 (velo y bloqueo de desplazamiento del menú móvil)
- Relacionada con DIS-031 (trampa de foco compartida)

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-19 | Creada como Propuesta desde la revisión de FNC-070 |
| 2026-10-19 | DIS-001 (captura de `/platforms` a 390 px con Chrome sin interfaz): el contenido se corta a la derecha (buscador y tarjetas); no viene de los tokens, sin investigar la causa |
| 2026-10-21 | Aprobada en modo autónomo y En curso (rama `dis/DIS-025-navegacion-movil`) |
| 2026-10-21 | `MobileMenu` y pruebas; verificación en verde; genera DIS-038 (velo y bloqueo de scroll); el corte a 390 px de `/platforms` no es de esta tarea; En revisión |
