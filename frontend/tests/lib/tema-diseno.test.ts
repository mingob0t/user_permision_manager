/** FNC-032: `color-scheme` por tema y selector que no desborda la cabecera a 320 px. */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { CONTEXTOS, RUTA_TOKENS } from '../utils/tokens-css';

const css = readFileSync(resolve(RUTA_TOKENS, '../global.css'), 'utf8').replace(/\/\*[\s\S]*?\*\//g, '');
const leer = (ruta: string) => readFileSync(resolve(import.meta.dirname, '../../src', ruta), 'utf8');

/** `color-scheme` de la regla de `global.css` cuyo selector incluye el del contexto. */
function esquema(selector: string): string | undefined {
  for (const [, lista, valor] of css.matchAll(/([^{}]+)\{\s*color-scheme:\s*([\w ]+?);\s*\}/g)) {
    if (lista.split(',').map((x) => x.trim()).includes(selector)) return valor;
  }
  return undefined;
}

describe('color-scheme por tema', () => {
  const esperado: Record<string, string> = {
    ':root': 'light dark', 'html.light': 'light', 'html.dark': 'dark',
    'html.theme-emerald-light': 'light', 'html.theme-obsidian-dark': 'dark',
    'html.theme-rose-light': 'light', 'html.theme-violet-dark': 'dark',
  };
  for (const [selector, valor] of Object.entries(esperado)) {
    it(`${selector} declara ${valor}`, () => {
      expect(esquema(selector)).toBe(valor);
    });
  }

  it('cubre todos los temas de tokens.css', () => {
    for (const selector of Object.values(CONTEXTOS)) {
      if (selector.includes('not(')) continue; // SO oscuro: lo cubre `:root`
      for (const parte of selector.split(',').map((x) => x.trim())) {
        expect(esperado[parte], parte).toBeDefined();
      }
    }
  });
});

describe('cabecera a 320 px', () => {
  it('el selector es angosto, puede encogerse y crece desde sm', () => {
    expect(leer('components/theme-selector.tsx')).toContain('w-28 min-w-0 sm:w-40');
  });

  it('el bloque derecho de la cabecera puede encogerse (sin shrink-0)', () => {
    const shell = leer('components/app-shell.tsx');
    expect(shell).toContain('flex min-w-0 items-center gap-2 sm:gap-3');
    expect(shell).not.toContain('flex shrink-0 items-center gap-3');
  });
});
