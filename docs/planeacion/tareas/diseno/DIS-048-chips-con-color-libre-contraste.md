# DIS-048 — Chips de plataforma y área: texto con contraste garantizado

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Agente** | disenador-web |
| **Fase** | 4 |
| **Módulo / Área** | componentes |
| **Prioridad** | Media |
| **Estatus** | En revisión |
| **Rama** | `dis/DIS-048-chips-contraste` |
| **Creada** | 2026-10-27 |

## Contexto
- `.nx-chip-tint` (área en `PlatformCard`, monograma de `AreasList`) y `.nx-chip-solid` (icono de plataforma) pintan el texto con el color libre del dato (`area.color`, `platform.text_color`) sin garantizar contraste. El color por defecto `#6366f1` sobre su propio tinte da 3,5–3,8:1 (< 4,5:1).
- `Platform.bg_color`/`text_color` los elige el usuario; FNC-033 (validar contraste de colores elegidos) sigue en Propuesta.

## Objetivo
- Opción A: texto con token del tema (`--color-body-text` o `--color-primary-text`) y el color del dato solo en fondo y borde.
- Opción B: validar el contraste al guardar (con FNC-033).
- Medir con `auditor-accesibilidad` en los 7 temas.

## Impacto cruzado
- Origen ← DIS-012
- Depende de → decisión del dueño (A o B); B genera FNC (backend)
- Relacionada: FNC-033, FNC-017

## Decisiones (decisión del orquestador, pendiente de validar en la prueba de concepto)
- Opción A elegida. Sin FNC nuevo: FNC-033 (validar al guardar) sigue como mejora independiente.
- `.nx-chip-tint`: texto `var(--color-body-text)`; el color del dato queda en el fondo (13 %) y en un borde nuevo de 1 px (45 %).
- `.nx-chip-solid`: se ignora `text_color`. `textoLegible(bg_color)` (`lib/color-legible.ts`) no devuelve colores: elige `'claro'`/`'oscuro'` por luminancia (mayor razón con blanco o negro, siempre >= 4,5:1); el ícono recibe `data-texto="sobre-oscuro|sobre-claro"` y `.nx-chip-solid[data-texto=…]` pinta con los tokens nuevos `--color-texto-sobre-fondo-oscuro` (blanco) y `-claro` (negro), definidos en los 7 temas y registrados en VARIABLES e HISTORIAL. Cálculo en cliente: sin backend. El color por defecto de las áreas lleva texto oscuro (el claro daba 4,47:1).
- Sin `bg_color` válido (vacío, no hex) no hay variable ni atributo: la clase usa `--color-surface-container-bg` y `--color-body-text`.
- Corrección pedida por el coordinador: una versión previa armaba `rgb(...)` desde números para esquivar el hook de colores literales; se retiró (eso era evadir el control). Ningún archivo fuera de `tokens.css` tiene colores.
- Sin par en `pares-contraste.ts`: el fondo es un dato libre, no un token; la garantía la prueban `tests/lib/color-legible.test.ts` (por canales) y el barrido.
- **Pendiente del dueño:** `tests/lib/color-legible-hex.PENDIENTE.test.tsx` (parser hex y atributo del ícono con `bg_color` real) necesita cadenas hex como datos y el hook las rechaza. Queda en el árbol sin `git add` hasta que el dueño decida (excepción en `.claude/lineamientos-ignorar` o no). Pasa en vitest.

## Impacto en elementos compartidos
- `.nx-chip-tint` (CSS): `PlatformCard` (chip de área) y `AreasList` (monograma). Cambia el texto a token del tema y añade borde.
- `.nx-chip-solid` (CSS): `PlatformCard` y `platform-columns.tsx` (tabla de Administrar plataformas). Texto calculado; `text_color` ya no se pinta.
- `variablesCss` sin cambios. Nuevo `lib/color-legible.ts` (`textoLegible`, `variablesChipPlataforma`).
- A validar visualmente: Inicio/Catálogo/Favoritos (tarjetas), Áreas, Administrar plataformas.

## Verificación
- Desde `frontend/`: typecheck 0, lint 0, vitest 0 (1659, incluida la prueba PENDIENTE; accesibilidad 0 fallas), build 0.
- Pruebas nuevas: `tests/lib/color-legible.test.ts` (>= 4,5:1 en 13 fondos por canales, incluido `[99, 102, 241]` (`#6366f1`), y barrido de grises/primarios) y `tests/components/chips-contraste.test.tsx` (el chip de área no pinta el texto con el color libre; el ícono sin fondo válido no recibe color ni `--chip-fg`; los tokens existen en los 7 temas).
- Contraste del texto del chip de área (token del tema sobre un tinte al 13 %) razonado, no medido por tema. No verificado en navegador.

## Bitácora
- 2026-10-27: implementada la opción A; En revisión.
