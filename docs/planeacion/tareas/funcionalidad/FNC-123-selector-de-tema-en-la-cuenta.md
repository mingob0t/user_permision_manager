# FNC-123 — Selector de tema: leer y guardar el tema en la cuenta

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | web |
| **Agente** | desarrollador |
| **Fase** | 4 |
| **Módulo / Área** | tema |
| **Prioridad** | Baja |
| **Estatus** | En revisión |
| **Rama** | `fnc/FNC-123-selector-tema-en-cuenta` |
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

- 2026-10-27 (auditoría de FNC-122): condición de seguridad: `preferences.theme` de `GET /me` debe pasar por `esTemaValido`/`aplicarTema` de `lib/tema.ts`; nunca `classList.add(theme)` directo.

## Implementación
- `lib/tema.ts`: `aplicarTemaDeCuenta(valor)`; pasa por `esTemaValido` y `elegirTema` (`aplicarTema` + `localStorage`); inválido → `sistema`; ausente (`undefined`/`null`) → no hace nada (rige el del navegador).
- `components/theme-selector.tsx`: al elegir aplica, guarda en `localStorage` y envía `api.savePreferences({ theme })`; si falla, `useToast` (error) sin revertir. Al cambiar `session.preferences.theme` aplica el de la cuenta (manda sobre el del navegador). El script de `<head>` no cambió.
- `lib/types.ts`: `Session.preferences.theme?: string` (opcional: los datos de prueba y APIs previas pueden no traerlo).
- `settings/preferences-tab.tsx`: se omite `theme` al guardar Ajustes, para que el tema de la sesión (posiblemente viejo) no pise el elegido en el selector.
- Decisiones del orquestador (pendiente de validar en la prueba de concepto): el tema de la cuenta se aplica desde `ThemeSelector` (vive dentro de `SessionProvider`) y no en `session-provider`; `theme` ausente conserva el local; el fallo avisa con toast y no reintenta; Ajustes no reenvía `theme`; sin cambios visuales, ni variables, ni contrato nuevo.

## Impacto en elementos compartidos
| Elemento | Definido en | Usado en | Validar |
|---|---|---|---|
| `Session` (clave opcional `preferences.theme`) | `frontend/src/lib/types.ts` | `session-provider`, `require-role`, `api.ts`, pruebas con sesión simulada | tipo aditivo; typecheck 0 |
| `ThemeSelector` (lee la sesión, usa `useToast`, llama a la API) | `frontend/src/components/theme-selector.tsx` | cabecera de `AppShell` (todas las pantallas con shell), `tests/lib/tema.test.tsx` | cambiar tema con y sin sesión; sin `ToastProvider` el aviso no hace nada |
| `lib/tema.ts` (función nueva `aplicarTemaDeCuenta`) | `frontend/src/lib/tema.ts` | `ThemeSelector`, `tests/lib/tema.test.tsx` | aditivo |
| `PreferencesTab.save` (ya no envía `theme`) | `frontend/src/components/settings/preferences-tab.tsx` | Ajustes › Mis preferencias | guardar preferencias no cambia el tema |

## Verificación
- `npm run typecheck`: código 0. `npm run lint`: código 0 sin avisos. `npx vitest run`: código 0, 54 archivos, 1699 pruebas (incluye accesibilidad/contraste: 0 fallas). `npm run build`: código 0.
- Nuevas: `tests/components/theme-selector-cuenta.test.tsx` (7): guardado en la API, fallo con aviso sin revertir, tema de la cuenta manda al cargar, inválido cae a «sistema», ausente conserva el local.
- No verificado: navegador real (claro/oscuro, móvil/escritorio) ni integración con el backend real; sin `tester`, `revisor` ni `auditor-accesibilidad` (no se lanzan desde este agente). `auditor-seguridad` no requerido por la ficha; la condición de FNC-122 se cumple y está probada.
- Sin cambios visuales ni de tokens.

- 2026-10-27: implementada; En revisión.
