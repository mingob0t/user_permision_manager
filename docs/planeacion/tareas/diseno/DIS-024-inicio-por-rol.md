# DIS-024 — Inicio por rol

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 3 |
| **Módulo / Área** | dashboard |
| **Prioridad** | Media |
| **Estatus** | En revisión |
| **Creada** | 2026-10-13 |
| **Estatus Git** | Commit local, sin push |
| **Rama** | `dis/DIS-024-inicio-por-rol` |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | No |

## Contexto
- El Panel (`dashboard.tsx`) muestra contadores y visitas iguales para todos; la tabla de pantallas pide un Inicio por rol
- Requerimientos: Pantalla "Inicio" de REQUERIMIENTOS §4

## Objetivo
- Agregar al inicio el resumen por rol de FNC-066 con accesos directos (Mis solicitudes, Aprobaciones, ejecuciones fallidas)

## Alcance
- **Incluye:**
  - Bloque de resumen en componente propio, encima de lo existente
  - Usa `usePolling` de FNC-071 (ADR-006): refresco con el intervalo de la preferencia del usuario, en pausa con la pestaña oculta.
- **No incluye:**
  - Corregir la gráfica (DIS-003)
  - Quitar contenido existente

## Archivos previstos
- `frontend/src/components/home/role-summary.tsx`
- `frontend/src/components/dashboard.tsx` (importación)

## Reutilización
- `StatTile`, `Card` de `ui.tsx`, `usePolling`

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Usado en (vistas, módulos, escenas) | ¿Validado? |
|---|---|---|---|
| `dashboard.tsx` (`Dashboard`) | Pantalla | `/` (`app/page.tsx`) | Pendiente: el resumen va arriba; `/stats` ya no bloquea la pantalla al cargar o fallar (spinner y error en línea); título nuevo "Actividad del portal" |
| `pares-contraste.ts` | Prueba compartida | `contraste.test.ts` | Sí: par nuevo `foco-primary/panel`, pasa en los 7 contextos |
| `03-reutilizacion.md`, `docs/frontend/README.md` | Documentación | — | — |

Salida de `impacto.py` (contra `develop`):

| Elemento modificado | Tipo | Definido en | Usado en (fuera de la tarea) | Áreas afectadas | ¿Validado? |
|---|---|---|---|---|---|
| `Dashboard` | función | `frontend/src/components/dashboard.tsx` | `frontend/src/app/page.tsx`, `frontend/src/styles/components.css` | frontend/src | ☐ |
| `tinte` | función/componente | `frontend/tests/accesibilidad/pares-contraste.ts` | `frontend/src/styles/tokens.css` | frontend/src | ☐ |

- `tinte`: falso positivo (no se modificó; el archivo solo recibió un par nuevo). `components.css` aparece por coincidencia de nombre.

## Implementación
- `frontend/src/components/home/role-summary.tsx` (nuevo): `RoleSummary`, `gruposDelResumen`, `resumenVacio`, `RUTAS_INICIO`, `TITULOS`, `MENSAJES_VACIO`
- `frontend/src/components/dashboard.tsx`: importa `RoleSummary` encima; lo de `/stats` pasa a `Estadisticas` sin cambios de contenido
- `frontend/tests/components/home/role-summary.test.tsx` (nuevo, 11 pruebas por rol y estados)
- Reutiliza: `StatTile`, `Spinner`, `ErrorNote`, `EmptyNote` (`ui.tsx`), `Button`, `.nexus-btn`, `usePolling`, `listLoadError`, `formatearFecha`, `RUTA_AUDITORIA`. Sin tokens ni clases CSS nuevas

## Decisiones (decisión del orquestador, pendiente de validar en la prueba de concepto)
| # | Decisión |
|---|---|
| 1 | Gráfica heredada "Plataformas por área" y "Más visitadas": se **conservan** (no duplican el resumen; la ficha excluye quitar contenido). Deuda de variables `--nx-*` sigue en DIS-003 |
| 2 | Contadores heredados "Áreas" y "Plataformas" duplican los del resumen para admins: se conservan bajo el título nuevo "Actividad del portal"; retirarlos se propone en DIS-037 |
| 3 | Grupos por campos presentes en la respuesta (no por rol de sesión): Pendientes, Tus áreas / Todo el sistema, Mis solicitudes, Mis accesos |
| 4 | Destinos: Por aprobar → `/approvals`; Accesos con falla y Accesos activos → `/inventory`; Áreas → `/areas`; Plataformas → `/admin/platforms`; mis solicitudes y mis accesos → `/requests`; botón "Ver auditoría" → `/audit` (sin conteo propio en el contrato) |
| 5 | Contador = `StatTile` dentro de `Link` (área > 48 px) con anillo de foco `ring-primary`; nombre accesible "Etiqueta: n. Ir a Pantalla" |
| 6 | Sin enlaces con filtro: las pantallas no leen parámetros de URL; se propone DIS-036 |
| 7 | Vacío: todos los contadores en 0 → `EmptyNote` por alcance; el usuario además ve "Ir al catálogo" |
| 8 | Error: mensaje de `listLoadError` (sin texto del servidor) y "Reintentar"; 403 → "No tienes permiso…" (el contrato da 200 a los tres roles) |
| 9 | "Más antigua" como texto (`text-label`), no como `hint` de `StatTile` (`text-bi-muted` falla AA en obsidian, DIS-005) |
| 10 | `/stats` deja de bloquear la pantalla: spinner y error en línea debajo del resumen |

## Criterios de aceptación
- [x] Cada rol ve sus contadores y enlaces (pruebas Vitest por rol)
- [ ] Criterios comunes de diseño (FNC-037): tokens y clases existentes, sin estilos inline nuevos; no verificado en navegador

## Verificación
| Comando (en `frontend/`) | Resultado |
|---|---|
| `npm run typecheck` | salida 0 |
| `npm run lint` | salida 0, sin advertencias |
| `npx vitest run` | salida 0: 21 archivos, 784 passed, 25 expected fail (las 25 conocidas) |
| `npx vitest run tests/components/home` | 11 passed |
| `npx vitest run tests/accesibilidad` | 511 passed, 25 expected fail; par nuevo `foco-primary/panel` pasa en los 7 contextos |
| `npx next build` | salida 0; `/` 104 kB |
| `grep` de `style=`, `<style`, `.style.`, `#hex`, `rgb(` numérico e IPs en `role-summary.tsx` | sin coincidencias |

- No verificado en navegador (temas claro/oscuro, móvil y escritorio): no se levantó la app. Responsive por clases (`sm:grid-cols-2 lg:grid-cols-3`).
- `dashboard.tsx` conserva los literales heredados de la gráfica (`#6366f1`, `contentStyle`): deuda DIS-003, sin cambios.
- Sin revisor, tester ni auditores (por instrucción del orquestador).

## Correcciones del auditor-accesibilidad (2026-10-21)
| # | Hallazgo | Corrección | Prueba (falló antes) |
|---|---|---|---|
| 1 | Medio: tras un error, el reintento del sondeo desmontaba el contenido (`useAsync` deja `data` en null y `usePolling` solo devolvía el último dato con `error`), se perdía el foco y se repetía el aviso | `usePolling` devuelve `data ?? ultimoDato.current` | `tests/lib/use-polling.test.ts` ("durante el reintento…"); `role-summary.test.tsx` ("reintento del sondeo…": contador montado y con foco) |
| 2 | `dashboard.tsx`: "Plataformas por área" y "Más visitadas" eran h2 | h3 bajo el h2 "Actividad del portal" | `tests/components/dashboard.test.tsx` (nueva) |
| 3 | Estado vacío del resumen sin región viva | Envuelto en `role="status"` | `role-summary.test.tsx` (vacío) |
| 4 | Contador sin indicación de hover | `[&:hover>div]:border-primary` en el `Link` (borde del `Card`, token `--color-primary`; contraste ya medido en `foco-primary/panel` y `tab-indicador/body-bg`) | `role-summary.test.tsx` (usuario) |
| 5 | `.nexus-btn-primary:hover` con `filter: brightness(1.1)`: 3,97:1 en rose | Quitado el filtro en `components.css`; el hover usa los mismos tokens que el par `nexus-btn-primary`, ya medido en los 7 contextos | `tests/accesibilidad/hover-botones.test.ts` (nueva) |

- Observación: durante el reintento el `ErrorNote` se oculta porque `useAsync` limpia `error` al empezar cada consulta, y vuelve a anunciarse si falla de nuevo. No se cambió `useAsync` porque es compartido por todas las pantallas; si hace falta, va en DIS-033.

### Compartidos de esta corrección (validar)
| Elemento | Cambio | Pantallas que lo usan |
|---|---|---|
| `usePolling` (`lib/use-polling.ts`) | `data` conserva el último válido también mientras reintenta | `/requests` (`my-requests.tsx`, `my-access.tsx`), `/approvals` (`approvals-inbox.tsx`), `/users` panel de accesos (`users/user-access-panel.tsx`), `/` (`home/role-summary.tsx`) |
| `.nexus-btn-primary:hover` (`styles/components.css`) | Sin `filter: brightness(1.1)` (se mantienen elevación y sombra) | Todo `Button` `primary` y `danger` de `form.tsx` (formularios, diálogos de aprobar, rechazar, revocar y confirmar, login, ajustes, áreas, usuarios, plataformas) y los enlaces `nexus-btn-primary` |

Salida de `impacto.py` tras la corrección: `Dashboard` (`app/page.tsx`), `nexus-btn-primary` (`form.tsx`), y `Grupo`, `enlace` y `tinte`, que son falsos positivos por coincidencia de nombre. `usePolling` no aparece en la salida y se agregó a mano en la tabla anterior.

### Verificación tras la corrección (en `frontend/`)
| Comando | Resultado |
|---|---|
| `npm run typecheck` | salida 0 |
| `npm run lint` | salida 0 |
| `npx vitest run` | salida 0: 23 archivos, 788 passed, 25 expected fail (las 25 conocidas) |
| `npx next build` | salida 0; la regla `[&:hover>div]:border-primary` aparece en el CSS generado |
- Sigue sin verificarse en navegador.

## Tareas generadas
- DIS-036 (Propuesta): enlaces con filtro
- DIS-037 (Propuesta): contadores heredados duplicados

## Impacto cruzado
- Origen ← FNC-037
- Depende de → FNC-036, FNC-024, FNC-025, FNC-069, FNC-071, FNC-066
- Contrato → docs/contratos/inicio.md

## Riesgos y reversión
- Puede avanzar con los datos simulados de FNC-069; se integra después del backend.
- Reversión: revertir la rama.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta (FNC-037) |
| 2026-10-20 | Aprobada en modo autónomo por el orquestador; En curso |
| 2026-10-21 | Retomada tras corte por límite de uso; implementada y verificada (typecheck, lint, vitest, build en 0); En revisión |
| 2026-10-21 | Corregidos 5 hallazgos del auditor-accesibilidad, con prueba que falló antes; compartidos: `usePolling` y `.nexus-btn-primary:hover` |
