// @vitest-environment node
/**
 * Tamaño mínimo de texto (DIS-007, DIS-032): ningún texto de `src/` puede
 * quedar por debajo de 12 px. Revisa:
 * - CSS: `font-size`, el atajo `font:`, `@apply text-[…]` y los tokens de la
 *   escala `--text-*`;
 * - TS/TSX: clases Tailwind `text-[…]` (también `length:`, `calc()` y `var()`),
 *   la propiedad arbitraria `[font-size:…]`, `fontSize` (objeto o prop),
 *   `font-size=` de SVG y `font-size:` dentro de cadenas o plantillas (`style`).
 * Se mide en px (px, rem, `var(--text-*)` de tokens.css, `calc()` con esas
 * unidades). Un valor que no se pueda medir (em, %, otra variable) falla: se
 * usa la escala. Los comentarios se quitan antes de buscar.
 */
import { readdirSync, readFileSync } from 'node:fs';
import { extname, join, relative, resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const MINIMO_PX = 12;
const REM_PX = 16;
const RAIZ_SRC = resolve(import.meta.dirname, '../../src');
const TOKENS = join(RAIZ_SRC, 'styles/tokens.css');
/** Palabras clave de `font-size` que no reducen el texto. */
const CLAVES_VALIDAS = new Set([
  'inherit',
  'initial',
  'unset',
  'revert',
  'revert-layer',
  'medium',
  'large',
  'larger',
  'x-large',
  'xx-large',
  'xxx-large',
]);

function archivos(carpeta: string, extensiones: Set<string>): string[] {
  return readdirSync(carpeta, { withFileTypes: true }).flatMap((entrada) => {
    const ruta = join(carpeta, entrada.name);
    if (entrada.isDirectory()) return archivos(ruta, extensiones);
    return extensiones.has(extname(entrada.name)) ? [ruta] : [];
  });
}

const clave = (ruta: string): string => relative(RAIZ_SRC, ruta).split('\\').join('/');
const linea = (texto: string, indice: number): number => texto.slice(0, indice).split('\n').length;

/** Reemplaza los comentarios por espacios (conserva posiciones y saltos de línea). */
function sinComentarios(texto: string, js: boolean): string {
  const blanco = (m: string): string => m.replace(/[^\n]/g, ' ');
  const bloques = texto.replace(/\/\*[\s\S]*?\*\//g, blanco);
  if (!js) return bloques;
  return bloques.replace(/^(\s*)(\/\/.*)$/gm, (_m, sangria: string, resto: string) => sangria + blanco(resto));
}

/** Escala `--text-*` de tokens.css: nombre → valor en bruto. */
function escala(): Record<string, string> {
  const texto = sinComentarios(readFileSync(TOKENS, 'utf8'), false);
  const resultado: Record<string, string> = {};
  for (const m of texto.matchAll(/(--text-[\w-]+)\s*:\s*([^;]+);/g)) resultado[m[1]] = m[2].trim();
  return resultado;
}
const ESCALA = escala();

/** Valor en px, `Infinity` si es una palabra clave que no reduce, o `null` si no se puede medir. */
function aPx(valor: string, numeroEsPx = false): number | null {
  const limpio = valor.replace(/!important/, '').replace(/_/g, ' ').trim();
  if (CLAVES_VALIDAS.has(limpio)) return Infinity;
  if (numeroEsPx && /^\d*\.?\d+$/.test(limpio)) return Number(limpio);
  const variable = /^var\(\s*(--[\w-]+)\s*\)$/.exec(limpio);
  if (variable) return variable[1] in ESCALA ? aPx(ESCALA[variable[1]]) : null;
  const medida = /^(\d*\.?\d+)(px|rem)$/.exec(limpio);
  if (medida) return medida[2] === 'px' ? Number(medida[1]) : Number(medida[1]) * REM_PX;
  const calc = /^calc\((.*)\)$/.exec(limpio);
  if (calc) return calcular(calc[1]);
  return null;
}

/** `calc()` con sumas y restas de medidas o variables de la escala; si no, `null`. */
function calcular(expresion: string): number | null {
  const partes = expresion.trim().split(/\s*([+-])\s*(?=[\d.v])/);
  let total = aPx(partes[0]);
  for (let i = 1; i < partes.length && total !== null; i += 2) {
    const valor = aPx(partes[i + 1]);
    total = valor === null ? null : partes[i] === '+' ? total + valor : total - valor;
  }
  return total;
}

/** Tamaño del atajo `font:` (`[estilo] [peso] tamaño[/alto] familia`). */
function tamanoDeFont(valor: string): string {
  const limpio = valor.replace(/!important/, '').trim();
  if (CLAVES_VALIDAS.has(limpio)) return limpio;
  const m =
    /(?:^|\s)(calc\([^)]*\)|var\([^)]*\)|\d*\.?\d+[a-z%]+|[a-z-]*(?:small|large|larger|medium))(?:\s*\/\s*\S+)?\s/.exec(
      `${limpio} `,
    );
  return m ? m[1] : limpio;
}

const ES_COLOR = /^(?:color:|#|rgba?\(|hsla?\(|var\(--color|transparent$|currentcolor$|inherit$)/i;

interface Hallazgo {
  donde: string;
  valor: string;
}

/** `valor` devuelve `null` cuando no aplica (p. ej. `text-[…]` de color). */
interface Regla {
  patron: RegExp;
  valor: (m: RegExpMatchArray) => string | null;
  numeroEsPx?: boolean;
}

const REGLAS_TAILWIND: Regla[] = [
  {
    patron: /\btext-\[([^\]]+)\]/g,
    valor: (m) => (ES_COLOR.test(m[1].trim()) ? null : m[1].trim().replace(/^length:/, '')),
  },
  { patron: /\[font-size:([^\]]+)\]/g, valor: (m) => m[1] },
];

const REGLAS_CSS: Regla[] = [
  { patron: /(?<![\w-])font-size\s*:\s*([^;}]+)/g, valor: (m) => m[1] },
  { patron: /(?<![\w-])font\s*:\s*([^;}]+)/g, valor: (m) => tamanoDeFont(m[1]) },
  ...REGLAS_TAILWIND,
];

const REGLAS_TS: Regla[] = [
  ...REGLAS_TAILWIND,
  { patron: /\bfontSize\s*[:=]\s*\{?\s*['"`]?([^,}'"`\s)]+)/g, valor: (m) => m[1], numeroEsPx: true },
  { patron: /(?<![\w-])font-size\s*=\s*\{?\s*['"`]?([^'"`}\s]+)/g, valor: (m) => m[1], numeroEsPx: true },
  { patron: /(?<![\w-[])font-size\s*:\s*([^;'"`}\]]+)/g, valor: (m) => m[1] },
];

function revisarTexto(texto: string, reglas: Regla[], donde: (indice: number) => string): Hallazgo[] {
  const hallazgos: Hallazgo[] = [];
  for (const { patron, valor, numeroEsPx } of reglas) {
    for (const m of texto.matchAll(patron)) {
      const v = valor(m);
      if (v === null) continue;
      const px = aPx(v, numeroEsPx);
      if (px === null || px < MINIMO_PX) hallazgos.push({ donde: donde(m.index ?? 0), valor: m[0].trim() });
    }
  }
  return hallazgos;
}

function revisar(extensiones: string[], reglas: Regla[], js: boolean): Hallazgo[] {
  return archivos(RAIZ_SRC, new Set(extensiones)).flatMap((ruta) => {
    const texto = sinComentarios(readFileSync(ruta, 'utf8'), js);
    return revisarTexto(texto, reglas, (i) => `${clave(ruta)}:${linea(texto, i)}`);
  });
}

const enCss = (texto: string): Hallazgo[] =>
  revisarTexto(sinComentarios(texto, false), REGLAS_CSS, () => 'ejemplo');
const enTs = (texto: string): Hallazgo[] =>
  revisarTexto(sinComentarios(texto, true), REGLAS_TS, () => 'ejemplo');

describe('detector de texto menor a 12 px', () => {
  it.each([
    'a { font-size: 11px; }',
    'a { font-size: 0.7rem !important; }',
    'a { font-size: 1em; }',
    'a { font-size: var(--otra); }',
    'a { font-size: calc(10px + 1px); }',
    'a { font: 700 11px/1.2 Inter, sans-serif; }',
    'a { font: italic 0.6rem Inter; }',
    'a { @apply text-[10px] font-bold; }',
  ])('CSS: detecta %s', (ejemplo) => {
    expect(enCss(ejemplo)).toHaveLength(1);
  });

  it.each([
    'a { font-size: var(--text-xs); /* era 10px */ }',
    'a { font-size: /* 9px */ 12px; }',
    'a { font: 700 var(--text-sm)/1.2 Inter; }',
    'a { font-size: calc(var(--text-xs) + 2px); }',
    'a { font-size: inherit; }',
  ])('CSS: acepta %s', (ejemplo) => {
    expect(enCss(ejemplo)).toEqual([]);
  });

  it.each([
    '<p className="text-[11px]" />',
    '<p className="text-[0.6rem]" />',
    '<p className="text-[length:10px]" />',
    '<p className="text-[calc(10px+1px)]" />',
    '<p className="text-[calc(1rem_-_6px)]" />',
    '<p className="text-[var(--algo)]" />',
    '<p className="[font-size:10px]" />',
    '<p className="[font-size:var(--algo)]" />',
    'tick={{ fontSize: 11 }}',
    '<text fontSize={10}>x</text>',
    '<text font-size="9">x</text>',
    "const estilo = { fontSize: '0.6rem' };",
    'const s = `font-size: 10px; font-weight: 700`;',
    "el.setAttribute('style', 'font-size:11px')",
  ])('TS/TSX: detecta %s', (ejemplo) => {
    expect(enTs(ejemplo)).toHaveLength(1);
  });

  it.each([
    '<p className="text-xs" />',
    '<p className="text-[var(--color-label)]" />',
    '<p className="text-[13px] [font-size:var(--text-xs)]" />',
    'tick={{ fontSize: 12 }}',
    '// fontSize: 10 era el valor anterior',
    '/* text-[10px] */ const a = 1;',
  ])('TS/TSX: acepta %s', (ejemplo) => {
    expect(enTs(ejemplo)).toEqual([]);
  });
});

describe('tamaño mínimo de texto (12 px) en src', () => {
  it('lee la escala tipográfica de tokens.css', () => {
    expect(ESCALA['--text-xs']).toBe('12px');
  });

  it('ningún token de la escala --text-* baja de 12 px', () => {
    const chicos = Object.entries(ESCALA).filter(([, valor]) => (aPx(valor) ?? 0) < MINIMO_PX);
    expect(chicos, 'Usa --text-xs (12 px) como mínimo').toEqual([]);
  });

  it('ningún font-size, font: ni @apply text-[…] de los CSS de src baja de 12 px', () => {
    expect(revisar(['.css'], REGLAS_CSS, false), 'Usa var(--text-xs) o mayor (src/styles/tokens.css)').toEqual([]);
  });

  it('ninguna clase Tailwind, fontSize, font-size ni style de src baja de 12 px', () => {
    expect(revisar(['.ts', '.tsx'], REGLAS_TS, true), 'Usa text-xs (12 px) o mayor').toEqual([]);
  });
});
