# FNC-032 — Selector de tema: aplicar la clase en <html> o retirar los temas sin uso

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | web |
| **Agente** | desarrollador |
| **Fase** | 4 |
| **Módulo / Área** | tema |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Responsable** | |
| **Creada** | 2026-10-13 |
| **Inicio** | 2026-10-27 |
| **Finalizada** | |
| **Estatus Git** | — |
| **Rama** | `fnc/FNC-032-selector-de-tema` |
| **Commits / PR** | |
| **Requiere migración BD** | No (ver FNC-120) |
| **Requiere auditor-seguridad** | No |

## Contexto
Nada aplica `dark`/`theme-*` a `<html>` (`app/layout.tsx:20`); las variantes `dark:` y los 4 temas de `tokens.css:331-537` son inalcanzables.

Origen (diagnóstico inicial, FNC-001):
- [`docs/estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-accesibilidad-inicial.md): hallazgo estructural
- [`docs/estandarizacion/auditorias/2026-10-13-auditoria-inicial.md`](../../../estandarizacion/auditorias/2026-10-13-auditoria-inicial.md): H-11

## Objetivo
Hacer alcanzables los 7 temas de `tokens.css`: aplicar su clase en `<html>`, persistirla y restaurarla sin destello.

**Decisión del orquestador (pendiente de validar en la prueba de concepto):** aplicar la clase, no retirar temas (los 7 tienen tokens completos y pruebas de contraste; el dueño hará el diseño final).

## Alcance
- **Incluye:** `lib/tema.ts` (temas, aplicar, persistir, restaurar, script anti-destello), `ThemeSelector` en la cabecera de `AppShell`, script en `<head>` de `app/layout.tsx`, pruebas.
- **No incluye:** guardar el tema en la cuenta (la API de preferencias no tiene el campo; backend, FNC-120); cambios en `settings-panel` (DIS-011 lo divide); rediseño visual.

## Decisiones (del orquestador, pendientes de validar en la prueba de concepto)
- Persistencia en `localStorage` (`nexus-tema`) por navegador: no toca el backend.
- El selector vive en la cabecera de `AppShell`, no en Ajustes/Preferencias, por la división de `settings-panel` en curso (DIS-011).
- Opciones: Según el sistema (sin clase), Claro (`light`), Oscuro (`dark`) y los 4 `theme-*`.
- Anti-destello: script en línea en `<head>` (sin `style`); el selector solo sincroniza el control al montar.

## Criterios de aceptación
- [x] Hallazgos de origen corregidos y verificados
- [x] Prueba de regresión que primero falla (si corrige un defecto)
- [x] Pruebas mínimas del lineamiento de pruebas, ejecutadas
- [x] Cumple `docs/estandarizacion/` y no duplica código existente
- [x] Sin direcciones IP ni secretos

## Impacto cruzado
- Depende de → —
- Genera → FNC-120 (backend, Propuesta): tema en la cuenta del usuario
- Relacionada con → DIS-011 (división de `settings-panel`)

## Impacto en elementos compartidos
| Elemento modificado | Tipo | Definido en | Usado en | Áreas a validar |
|---|---|---|---|---|
| `RootLayout` | función | `frontend/src/app/layout.tsx` | `tests/components/raiz-desplazable.test.tsx` | todas las páginas (agrega `<head>` con el script de tema); prueba en verde |
| `AppShell` (cabecera) | componente | `frontend/src/components/app-shell.tsx` | todas las pantallas con marco | cabecera: ahora lleva el selector junto a "Salir"; validar en móvil |

Nuevos: `lib/tema.ts`, `components/theme-selector.tsx` (reutilizan `Select` de `form.tsx`, sin modificarlo).

## Verificación (en `frontend/`)
| Comando | Resultado |
|---|---|
| `npm run typecheck` | exit 0 |
| `npm run lint` | exit 0, sin avisos |
| `npm test` (vitest, incluye `tests/accesibilidad`) | exit 0, 44 archivos, 1544 pruebas, 0 fallas |
| `npm run build` | exit 0 |

No verificado: navegador real (destello al cargar, contraste visual del selector en cada tema); `auditor-accesibilidad` y `revisor` pendientes.

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-27 | Aprobada en modo autónomo; implementada la clase en `<html>` con persistencia local. En revisión |
