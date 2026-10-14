# FNC-024 — Línea base web: instalar dependencias, configurar ESLint y ejecutar typecheck y lint

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | web |
| **Agente** | desarrollador |
| **Fase** | 2 |
| **Módulo / Área** | pruebas |
| **Prioridad** | Alta |
| **Estatus** | En revisión |
| **Responsable** | desarrollador |
| **Creada** | 2026-10-13 |
| **Inicio** | 2026-10-13 |
| **Finalizada** | |
| **Estatus Git** | Commit local, sin push |
| **Rama** | `fnc/FNC-024-linea-base-web` |
| **Commits / PR** | `edb8f45`, `56e0112` (locales, sin push) |
| **Requiere migración BD** | No |
| **Requiere auditor-seguridad** | Sí (devDependencies nuevas) — Con observaciones |

## Contexto
No se pudo verificar `typecheck` ni `lint` (sin `node_modules`; ESLint sin configurar).

Origen (diagnóstico inicial, FNC-001):
- [`docs/planeacion/diagnostico-pruebas-2026-10-13.md`](../../../planeacion/diagnostico-pruebas-2026-10-13.md): tarea 8
- [`docs/backend/README.md`](../../../backend/README.md): verificación

## Objetivo
- Instalar dependencias, dejar `npm run lint` funcionando sin preguntas y registrar la **línea base** real de `typecheck`, `lint` y `build`.
- El objetivo es medir, no corregir: los errores encontrados quedan registrados, no arreglados.

## Alcance
- **Incluye:** `npm ci`; ESLint estándar de Next.js (`eslint`, `eslint-config-next`, `@eslint/eslintrc` y `eslint.config.mjs`); ejecutar y registrar typecheck, lint y build.
- **No incluye:** corregir errores de tipos o lint en componentes; tocar `next.config.ts` (FNC-005); `npm audit fix` (FNC-016); crear `.env`.

## Criterios de aceptación
- [x] `npm ci` instala sin errores
- [x] `npm run lint` corre sin preguntas interactivas
- [x] typecheck, lint y build ejecutados y su código de salida registrado
- [x] No aplica prueba de regresión (no corrige defectos)
- [x] Sin direcciones IP ni secretos

## Cambios
- `frontend/package.json`: 3 devDependencies nuevas, versión exacta: `eslint` 9.39.4, `eslint-config-next` 15.5.7 (igual que `next`), `@eslint/eslintrc` 3.3.5.
- `frontend/package-lock.json`: regenerado por npm (274 paquetes nuevos; ninguna versión existente cambió).
- `frontend/eslint.config.mjs` (nuevo): `next/core-web-vitals` + `next/typescript`, sin reglas propias.

## Línea base (2026-10-13, Node 22.23.2, npm 10.9.8)
| Comando | Salida | Resultado |
|---|---|---|
| `npm ci` | 0 | Instala bien antes y después de agregar ESLint |
| `npm run typecheck` | 0 | Sin errores de tipos |
| `npm run lint` | 1 | 1 error, 3 avisos |
| `npm run build` | 1 | Compila, pero falla en el paso de lint por el error de `error.tsx` |
| `npx next build --no-lint` (solo diagnóstico) | 0 | 14 páginas generadas; confirma que solo falla el lint |

Hallazgos de lint (por regla y archivo):
- Error `@next/next/no-html-link-for-pages`: `src/app/error.tsx:36` (usa `<a href="/">` en vez de `Link`).
- Aviso `@typescript-eslint/no-unused-vars`: `src/components/dashboard.tsx:11` (`EmptyNote` sin usar).
- Aviso `@next/next/no-img-element`: `src/components/settings-panel.tsx:106`.
- Aviso `react-hooks/exhaustive-deps`: `src/lib/use-async.ts:30`.

Notas:
- **Ojo:** antes de esta tarea `next build` omitía el lint (ESLint no estaba instalado). Ahora lo ejecuta y el error de `error.tsx` rompe `npm run build`. Hay que decidir antes de unir a `develop` (ver "Decisión pendiente").
- `next lint` está obsoleto y desaparece en Next.js 16; migrar a la CLI de ESLint cuando se actualice Next.
- `npm audit`: 13 vulnerabilidades (1 crítica en `next`, 10 altas, 2 moderadas). Antes de esta tarea eran 11; las 2 altas nuevas son `eslint-config-next` y `@next/eslint-plugin-next`, por `fast-glob` → `braces` (aviso ya existente). Se atienden en FNC-016.

## Decisión pendiente (del dueño)
- Opción A (recomendada): tarea nueva que cambie el `<a>` por `Link` en `error.tsx` (1 línea; toca un componente, por eso no se hizo aquí).
- Opción B: `"build": "next build --no-lint"` en `package.json` y dejar el lint como paso aparte.
- Opción C: `eslint.ignoreDuringBuilds` en `next.config.ts` (no recomendada: FNC-005 tiene ese archivo abierto).

## Tareas propuestas
- Corregir los 4 hallazgos de lint de la línea base (1 error, 3 avisos). Plataforma web. Sin ID todavía: se asigna en la base para no chocar con otros worktrees.

## Verificación
- Comandos de la tabla de línea base, ejecutados en `frontend/` con su código de salida real.
- No verificado: arranque con `npm run dev` ni contra el backend (fuera de alcance).

## Impacto en elementos compartidos
- `impacto.py` (contra `develop`, 9 archivos): ninguno detectado.
- Nota manual: `package.json` y el lockfile son de todo el frontend; el cambio visible es que `npm run build` ahora corre ESLint en todas las páginas.

## Impacto cruzado
- Depende de → —

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-13 | Creada como Propuesta desde el diagnóstico inicial |
| 2026-10-13 | Aprobada por el dueño; implementada por desarrollador. Línea base registrada; build roto por 1 error de lint, decisión pendiente |

- auditor-seguridad (modo cambio, 2026-10-13): Con observaciones; sin hallazgos críticos ni altos introducidos.
- revisor (2026-10-13): Con observaciones; documentación corregida (conteo de npm audit, commits, impacto, auditor-seguridad).
- Condición de merge: build limpio vía FNC-072.
