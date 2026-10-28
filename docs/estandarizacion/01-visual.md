# Estándares Visuales (01-visual.md)

Basado en **ADR-007** y **PLAN-FASE-7** (DIS-054, DIS-055).

## 1. Arquitectura de Tokens por Capas

| Capa | Rol | Formato | Dónde vive | Quién la usa |
|---|---|---|---|---|
| **1. Primitivos** | Paleta tonal neutra y acentos (`--p-neutro-*`, `--p-marca-*`, etc.) | Canales `R G B` | Solo `tokens.css` | Exclusivamente semánticos |
| **2. Semánticos** | Rol funcional asignado (`--color-fondo`, `--color-superficie`, `--color-texto`, `--color-accion`, etc.) | Canales `R G B` | `tokens.css` y `tailwind.config.ts` | Componentes y vistas |
| **3. Alias** | Compatibilidad temporal con el esquema v2 previo (`--color-body-bg`, etc.) | `var(--color-*)` | `tokens.css` | Código en migración hasta DIS-067 |

## 2. Temas Disponibles

El sistema soporta únicamente **dos temas visuales**:
1. **Claro** (`:root, html.light`)
2. **Oscuro** (`html.dark` y `@media (prefers-color-scheme: dark)`)

La opción **«Según el sistema»** (`sistema`) conmuta automáticamente entre claro y oscuro según las preferencias del sistema operativo. La prueba automática `tokens-so-oscuro.test.ts` garantiza que el modo oscuro del sistema sea idéntico en valores a `html.dark`.

## 3. Matriz de Roles Semánticos

### Superficie
- `fondo`: fondo general de página (`bg-fondo`).
- `superficie`: paneles, tarjetas y modales (`bg-superficie`).
- `superficie-elevada`: popovers, menús y diálogos flotantes.
- `superficie-hundida`: cabeceras de tabla, fondos de inputs y barras de navegación secundarias.
- `velo`: oscurecimiento de fondo para modales (`bg-velo`).

### Texto
- `texto`: texto principal (WCAG AAA/AA).
- `texto-secundario`: subtítulos y etiquetas descriptivas (WCAG AA ≥ 4.5:1).
- `texto-tenue`: datos complementarios (WCAG AA ≥ 4.5:1 garantizado).
- `texto-sobre-accion`: texto legible sobre botones de acción.
- `texto-sobre-peligro`: texto legible sobre botones o avisos destructivos.
- `texto-enlace`: hipervínculos con énfasis visual.

### Borde
- `borde`: bordes de campos y controles interactivos (WCAG AA no textual ≥ 3:1).
- `borde-sutil`: divisores decorativos entre secciones.
- `borde-fuerte`: bordes con énfasis o foco.

### Acento y Acción
- `accion`: color primario de interacción (`bg-accion`).
- `accion-hover`: estado hover de elementos primarios.
- `accion-presionada`: estado active/presionado.
- `accion-tenue`: tinte translúcido para selección o foco.
- `accion-texto`: color de texto primario con contraste garantizado.

### Estados
Para cada estado (`exito`, `aviso`, `peligro`, `info`, `neutro`):
- `<estado>-relleno`: color base de fondo o indicador.
- `<estado>-tenue`: fondo atenuado para notas o chips.
- `<estado>-borde`: borde delimitador de avisos.
- `<estado>-texto`: color de texto con contraste ≥ 4.5:1 sobre superficie y sobre `<estado>-tenue`.

## 4. Reglas de Uso en Código (Obligatorio)
1. **Prohibido el uso de primitivos en TSX o CSS**: Ningún archivo `.tsx`, `global.css` o `components.css` debe invocar `--p-*`. La prueba `tokens-completitud.test.ts` valida esto automáticamente.
2. **Prohibido `dark:` en TSX**: Los componentes no conocen el tema; el cambio de color ocurre por variables CSS asignadas al tema activo.
3. **Prohibidos colores arbitrarios o literales**: No usar `text-blue-500`, `bg-[#2563eb]` o estilos inline `style={{...}}`.

## 5. Matriz de Estados e Interacción (DIS-056)

| Estado / Rol | Token CSS | Utilidad Tailwind / CSS | Propósito |
|---|---|---|---|
| **Foco visible** | `--foco-anillo`, `--foco-ancho`, `--foco-separacion` | `.foco-visible`, `ring-foco-anillo` | Anillo accesible de 2px con 2px de separación, contraste ≥ 3:1 |
| **Hover** | `--hover-capa` | — | Capa sutil de oscurecimiento (claro) o aclarado (oscuro) |
| **Presionado** | `--presionado-capa` | — | Capa táctil feedback visual inmediato |
| **Seleccionado** | `--seleccionado-fondo`, `--seleccionado-borde` | `border-seleccionado-borde` | Indicación clara de pestañas o filas activas |
| **Deshabilitado** | `--deshabilitado-fondo`, `--deshabilitado-texto`, `--deshabilitado-borde` | `.estado-deshabilitado` | Sin opacidad artificial (`opacity-40`); contraste y legibilidad definidos por token |
| **Inválido** | `--invalido-borde` | `.estado-invalido`, `border-invalido-borde` | Borde rojo accesible (≥ 3:1) ante `aria-invalid="true"` |
| **Solo lectura** | `--solo-lectura-fondo` | `.solo-lectura` | Fondo diferenciado para campos `[readonly]` |
| **Movimiento** | `--duracion-corta`, `--duracion-media`, `--curva` | `duration-corta`, `duration-media`, `ease-curva` | Transiciones normalizadas (150ms/250ms); 0ms en `prefers-reduced-motion` |

## 6. Escalas Visuales (DIS-057)

### Tipografía y Fuentes
- **Pila Sans del Sistema** (`--fuente-texto`): `ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`. Sin dependencias de Google Fonts ni bloqueo de red.
- **Pila Mono** (`--fuente-mono`): `ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace`.
- **Escala de Tamaños**:
  - `text-xs`: 12 px (umbral mínimo accesible WCAG AA)
  - `text-sm`: 14 px
  - `text-base`: 16 px
  - `text-lg`: 18 px
  - `text-xl`: 20 px
  - `text-2xl`: 24 px
  - `text-3xl`: 30 px

### Radios de Borde
- `rounded-control` (`--radio-control`): 8 px (botones, inputs, selectores)
- `rounded-tarjeta` (`--radio-tarjeta`): 12 px (paneles contenedores y tarjetas)
- `rounded-dialogo` (`--radio-dialogo`): 16 px (ventanas modales y cuadros de diálogo)
- `rounded-pastilla` (`--radio-pastilla`): 9999 px (insignias, chips)

### Bordes y Sombras
- `border-base` (`--borde-ancho`): 1 px estándar.
- `shadow-1` (`--sombra-1`): elevación sutil para tarjetas en reposo.
- `shadow-2` (`--sombra-2`): elevación media para tarjetas activas y dropdowns.
- `shadow-3` (`--sombra-3`): elevación alta para modales y diálogos superpuestos.


