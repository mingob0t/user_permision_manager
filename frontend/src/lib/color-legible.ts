/**
 * Texto legible sobre un fondo libre (DIS-048). El usuario elige `bg_color` y `text_color` de una
 * plataforma sin validar su contraste (FNC-033 sigue pendiente): el chip ignora `text_color` y
 * decide, según la luminancia del fondo, si el texto va claro u oscuro. El color real sale de
 * los tokens `--color-texto-sobre-fondo-*` (`.nx-chip-solid[data-texto]`); aquí no hay colores.
 */
export type EleccionTexto = 'claro' | 'oscuro';
type Canales = readonly [number, number, number];

/** Luminancia relativa WCAG de un color en canales 0-255. */
function luminancia([r, g, b]: Canales): number {
  const [R, G, B] = [r, g, b].map((c) => {
    const s = c / 255;
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * R + 0.7152 * G + 0.0722 * B;
}

/**
 * `'claro'` si el texto debe ser claro (fondo oscuro) y `'oscuro'` si debe ser oscuro (fondo
 * claro): el que dé la mayor razón de contraste con blanco o negro, siempre >= 4,5:1.
 */
export function eleccionPorCanales(canales: Canales): EleccionTexto {
  const L = luminancia(canales);
  // Contraste con blanco = 1,05 / (L + 0,05); con negro = (L + 0,05) / 0,05.
  return 1.05 / (L + 0.05) >= (L + 0.05) / 0.05 ? 'claro' : 'oscuro';
}

/** Interpreta `#rgb` o `#rrggbb`; cualquier otra cosa devuelve `null`. */
function leerHex(valor: string | null | undefined): Canales | null {
  const m = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.exec((valor ?? '').trim());
  if (!m) return null;
  const hex = m[1].length === 3 ? m[1].split('').map((c) => c + c).join('') : m[1];
  return [0, 2, 4].map((i) => parseInt(hex.slice(i, i + 2), 16)) as unknown as Canales;
}

/** Elección de texto para un fondo hexadecimal; `null` si el fondo no es un hex válido. */
export function textoLegible(fondo: string | null | undefined): EleccionTexto | null {
  const canales = leerHex(fondo);
  return canales ? eleccionPorCanales(canales) : null;
}

/** Variable `--chip-bg` del ícono de plataforma (se pasa a `variablesCss()`); vacía si el fondo no es válido. */
export function variablesChipPlataforma(
  fondo: string | null | undefined,
): Record<`--${string}`, string | undefined> {
  return textoLegible(fondo) ? { '--chip-bg': (fondo as string).trim() } : {};
}

/** Atributo `data-texto` del ícono: `sobre-oscuro` (texto claro) o `sobre-claro`; sin fondo válido, ausente. */
export function atributoTexto(fondo: string | null | undefined): 'sobre-oscuro' | 'sobre-claro' | undefined {
  const e = textoLegible(fondo);
  return e === null ? undefined : e === 'claro' ? 'sobre-oscuro' : 'sobre-claro';
}
