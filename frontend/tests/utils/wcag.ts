/**
 * Cálculo de contraste WCAG 2.x (FNC-025).
 *
 * Luminancia relativa y razón de contraste según
 * https://www.w3.org/TR/WCAG21/#dfn-contrast-ratio. Los colores con alpha se
 * componen sobre su fondo antes de medir.
 */

export interface Rgba {
  r: number;
  g: number;
  b: number;
  a: number;
}

/** Umbral AA para texto normal. */
export const MIN_TEXTO = 4.5;
/** Umbral AA para elementos no textuales (bordes de control, íconos). */
export const MIN_NO_TEXTO = 3;

/** Interpreta `#rgb`, `#rrggbb`, `R G B` o `R G B / a` (formato de tokens.css). */
export function parseColor(valor: string): Rgba {
  const texto = valor.trim();
  if (texto.startsWith('#')) {
    let hex = texto.slice(1);
    if (hex.length === 3) hex = hex.split('').map((c) => c + c).join('');
    if (hex.length !== 6) throw new Error(`Hex no soportado: ${valor}`);
    return {
      r: parseInt(hex.slice(0, 2), 16),
      g: parseInt(hex.slice(2, 4), 16),
      b: parseInt(hex.slice(4, 6), 16),
      a: 1,
    };
  }
  const canales = texto.match(/^(\d+)\s+(\d+)\s+(\d+)(?:\s*\/\s*([\d.]+))?$/);
  if (!canales) throw new Error(`Color no soportado: ${valor}`);
  return {
    r: Number(canales[1]),
    g: Number(canales[2]),
    b: Number(canales[3]),
    a: canales[4] === undefined ? 1 : Number(canales[4]),
  };
}

/** Compone `frente` (con alpha) sobre `fondo` (opaco). */
export function componer(frente: Rgba, fondo: Rgba): Rgba {
  const a = frente.a;
  return {
    r: frente.r * a + fondo.r * (1 - a),
    g: frente.g * a + fondo.g * (1 - a),
    b: frente.b * a + fondo.b * (1 - a),
    a: 1,
  };
}

function canalLineal(canal: number): number {
  const c = canal / 255;
  return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
}

/** Luminancia relativa de un color opaco. */
export function luminancia(color: Rgba): number {
  return (
    0.2126 * canalLineal(color.r) +
    0.7152 * canalLineal(color.g) +
    0.0722 * canalLineal(color.b)
  );
}

/** Razón de contraste entre dos colores opacos (de 1 a 21). */
export function razonContraste(a: Rgba, b: Rgba): number {
  const la = luminancia(a);
  const lb = luminancia(b);
  const [claro, oscuro] = la > lb ? [la, lb] : [lb, la];
  return (claro + 0.05) / (oscuro + 0.05);
}
