// @vitest-environment node
/**
 * Tamaño mínimo de texto (DIS-007, DIS-032): ningún texto de `src/` puede
 * quedar por debajo de 12 px. Revisa:
 * - CSS: cada `font-size` (px, rem o `var(--text-*)` de tokens.css) y los
 *   tokens de la escala tipográfica `--text-*`;
 * - TS/TSX: clases Tailwind arbitrarias (`text-[10px]`, `text-[0.6rem]`) y
 *   `fontSize: N` / `fontSize={N}` (p. ej. ejes de Recharts).
 * Un valor que no se pueda medir (calc, em, %) también falla: se usa la escala.
 */
import { readdirSync, readFileSync } from 'node:fs';
import { extname, join, relative, resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const MINIMO_PX = 12;
const REM_PX = 16;
const RAIZ_SRC = resolve(import.meta.dirname, '../../src');
const TOKENS = join(RAIZ_SRC, 'styles/tokens.css');

function archivos(carpeta: string, extensiones: Set<string>): string[] {
  return readdirSync(carpeta, { withFileTypes: true }).flatMap((entrada) => {
    const ruta = join(carpeta, entrada.name);
    if (entrada.isDirectory()) return archivos(ruta, extensiones);
    return extensiones.has(extname(entrada.name)) ? [ruta] : [];
  });
}

const clave = (ruta: string): string => relative(RAIZ_SRC, ruta).split('\\').join('/');
const linea = (texto: string, indice: number): number => texto.slice(0, indice).split('\n').length;

/** Escala `--text-*` de tokens.css: nombre → valor en bruto. */
function escala(): Record<string, string> {
  const texto = readFileSync(TOKENS, 'utf8');
  const resultado: Record<string, string> = {};
  for (const m of texto.matchAll(/(--text-[\w-]+)\s*:\s*([^;]+);/g)) resultado[m[1]] = m[2].trim();
  return resultado;
}
const ESCALA = escala();

/** Valor en px, o `null` si no se puede medir. */
function aPx(valor: string): number | null {
  const limpio = valor.replace(/!important/, '').trim();
  const variable = /^var\(\s*(--[\w-]+)\s*\)$/.exec(limpio);
  if (variable) return variable[1] in ESCALA ? aPx(ESCALA[variable[1]]) : null;
  const medida = /^(\d*\.?\d+)(px|rem)$/.exec(limpio);
  if (!medida) return null;
  return medida[2] === 'px' ? Number(medida[1]) : Number(medida[1]) * REM_PX;
}

interface Hallazgo {
  donde: string;
  valor: string;
}

function revisarCss(): Hallazgo[] {
  const hallazgos: Hallazgo[] = [];
  for (const ruta of archivos(RAIZ_SRC, new Set(['.css']))) {
    const texto = readFileSync(ruta, 'utf8');
    for (const m of texto.matchAll(/font-size\s*:\s*([^;}]+)/g)) {
      const px = aPx(m[1]);
      if (px === null || px < MINIMO_PX) hallazgos.push({ donde: `${clave(ruta)}:${linea(texto, m.index)}`, valor: m[1].trim() });
    }
  }
  return hallazgos;
}

function revisarTsx(): Hallazgo[] {
  const hallazgos: Hallazgo[] = [];
  const patrones = [/\btext-\[([^\]]+)\]/g, /\bfontSize\s*[:=]\s*\{?\s*['"]?([\w.]+)/g];
  for (const ruta of archivos(RAIZ_SRC, new Set(['.ts', '.tsx']))) {
    const texto = readFileSync(ruta, 'utf8');
    for (const patron of patrones) {
      for (const m of texto.matchAll(patron)) {
        const valor = m[1].replace(/^length:/, '');
        // `text-[...]` también sirve para colores (`text-[rgb(...)]`): solo medidas.
        if (patron.source.startsWith('\\btext') && !/^\d*\.?\d+[a-z%]*$/.test(valor)) continue;
        const px = /^\d*\.?\d+$/.test(valor) ? Number(valor) : aPx(valor);
        if (px === null || px < MINIMO_PX) hallazgos.push({ donde: `${clave(ruta)}:${linea(texto, m.index)}`, valor: m[0] });
      }
    }
  }
  return hallazgos;
}

describe('tamaño mínimo de texto (12 px)', () => {
  it('lee la escala tipográfica de tokens.css', () => {
    expect(ESCALA['--text-xs']).toBe('12px');
  });

  it('ningún token de la escala --text-* baja de 12 px', () => {
    const chicos = Object.entries(ESCALA).filter(([, valor]) => (aPx(valor) ?? 0) < MINIMO_PX);
    expect(chicos, 'Usa --text-xs (12 px) como mínimo').toEqual([]);
  });

  it('ningún font-size de los CSS de src baja de 12 px', () => {
    expect(revisarCss(), 'Usa var(--text-xs) o mayor (src/styles/tokens.css)').toEqual([]);
  });

  it('ninguna clase Tailwind ni fontSize de src baja de 12 px', () => {
    expect(revisarTsx(), 'Usa text-xs (12 px) o mayor').toEqual([]);
  });
});
