# DIS-010 — Componentes comunes: DataTable, botón de peligro, filtros, tonos de estado y toast

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | componentes |
| **Prioridad** | Media |
| **Estatus** | Hecha |
| **Responsable** | |
| **Creada** | 2026-10-13 |
| **Inicio** | 2026-10-27 |
| **Finalizada** | |
| **Estatus Git** | Rama local, sin push |
| **Rama** | `dis/DIS-010-componentes-comunes` |
| **Commits / PR** | |
| **Requiere migración BD** | Por definir |
| **Requiere auditor-seguridad** | No |

## Contexto
Secciones resueltas de formas distintas.

Origen (diagnóstico inicial, FNC-001):
- [`docs/estandarizacion/auditorias/2026-10-13-auditoria-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-auditoria-inicial.md): H-10, H-15, H-17

## Objetivo
Una sola versión de tabla, botón de peligro, filtros, tonos de estado y feedback (toast) (H-10, H-15, H-17; D-08 a D-11).

## Alcance
- **Incluye:** `DataTable` (migra `platform-admin`), `.nexus-btn-danger`, `FilterBar` (migra `platform-catalog`), `Tone` y `SuccessNote` (7 pantallas), `Toast` (montado en `layout`; usado en favorito de `platform-card`).
- **No incluye:** dividir `settings-panel`, `users-list`, `platform-admin` (DIS-011); migrar los avisos de `settings-panel` (`Guardado.`) ni las listas de usuarios y áreas a `DataTable` (son listas de tarjetas, DIS-011); rediseño visual (lo hace el dueño).

## Criterios de aceptación
- [x] Hallazgos de origen corregidos y verificados
- [ ] Prueba de regresión que primero falla (si corrige un defecto)
- [x] Pruebas mínimas del lineamiento de pruebas, ejecutadas
- [x] Cumple `docs/estandarizacion/` y no duplica código existente
- [x] Sin direcciones IP ni secretos

## Decisiones (del orquestador, pendientes de validar en la prueba de concepto)
- La ficha no precisaba alcance: se tomó de la auditoría (H-10, H-15, H-17, D-08 a D-11) y de lo que ya habían resuelto DIS-008/014/020/035 (acciones de fila, `ResponsiveList`, auditoría).
- `Button danger` pasa de un override `!bg-error-solid` a la clase `.nexus-btn-danger` (mismos tokens, mismo contraste).
- Toast: el error no se cierra solo (no se pierde un fallo); éxito e info, a los 6 s (`TOAST_MS`); solo se usa en el favorito de `platform-card`, que fallaba en silencio.
- `SuccessNote` solo en los avisos con el mismo marcado; `settings-panel` queda para DIS-011.
- `DataTable` hoy solo la usa `platform-admin` (única `<table>` visible a mano); `dashboard` tiene una `sr-only` de datos y no migra.
- Tipo `Tone` exportado en `ui.tsx`; `css-sin-uso.test.ts` ahora lo lee de ahí.

## Impacto en elementos compartidos
Salida de `impacto.py` (sin validar por el usuario):

| Elemento | Qué cambió | Lo usan |
|---|---|---|
| `Button` (`form.tsx`) | variante `danger` con `.nexus-btn-danger` | 31 usos: diálogos de confirmar/rechazar/revocar/quitar admin/conectores, `ConfirmDialog` |
| `Badge` (`ui.tsx`) | solo el tipo `tone` pasa a `Tone` (sin cambio visual) | estados en access, areas, audit, connectors |
| `ui.tsx` | nuevo `SuccessNote` | 7 pantallas de avisos |
| `.nexus-btn-danger` (`components.css`) | clase nueva | `Button danger` |
| `PlatformCard` | `useToast` en el fallo del favorito | `/platforms`, favoritos, `request-catalog-card` |
| `PlatformCatalog` | filtros con `FilterBar`/`TextInput`/`Select` (apariencia estándar de formularios) | `/platforms` |
| `RootLayout` | `ToastProvider` envolviendo `children` | todas las páginas |

A validar visualmente: botones de peligro, filtros de `/platforms`, tabla de `/admin/platforms`, aviso de éxito en las 7 pantallas.

## Verificación (en `frontend/`)
| Comando | Resultado |
|---|---|
| `npx tsc --noEmit` | 0 |
| `npm run lint` | 0 |
| `npx vitest run` | 0 (40 archivos, 1491 pruebas; incluye contraste, texto mínimo, área táctil, css-sin-uso, sin-estilos-inline y `componentes-comunes.test.tsx`) |
| `npm run build` | 0 |

No verificado: capturas en navegador (tema claro/oscuro, móvil/escritorio); `auditor-accesibilidad`, `revisor` y `tester` no se ejecutaron en esta sesión (pendientes para el orquestador).

## Impacto cruzado
- Depende de → —

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-27 | Aprobada en modo autónomo y pasada a En curso (decisión del orquestador, pendiente de validar en la prueba de concepto) |
| 2026-10-27 | Implementada: DataTable, FilterBar, .nexus-btn-danger, Tone/SuccessNote, Toast; pruebas y build en 0; pasa a En revisión |

- 2026-10-27: `auditor-accesibilidad` Aprobado (contraste del botón de peligro 4,83:1 y 5,29:1 en obsidian; tabla, filtros, toast y SuccessNote sin fallas). Agregada la prueba de hover de `.nexus-btn-danger`; pausa y foco del toast registrados como DIS-049. Hecha (decisión del orquestador, pendiente de validar en la prueba de concepto). Sin verificar en navegador.
