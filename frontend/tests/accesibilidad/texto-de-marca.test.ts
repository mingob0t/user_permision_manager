// @vitest-environment node
/**
 * Regresión de DIS-001: los colores de marca (primary, brand, accent, sky,
 * peach, violet) son rellenos y no llegan a 4.5:1 como texto en todos los
 * temas. Como texto se usa su variante `*-text` (`text-primary-text`...),
 * que tokens.css define por tema y `contraste.test.ts` mide. En CSS
 * (`src/styles`), la propiedad `color:` usa `--color-<rol>-text`; bordes,
 * fondos y tintes siguen con el relleno (el resto del CSS heredado lo depura
 * DIS-009).
 */
import { readdirSync, readFileSync } from 'node:fs';
import { extname, join, relative, resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const RAIZ_SRC = resolve(import.meta.dirname, '../../src');
const CARPETAS = ['components', 'app'];
const EXTENSIONES = new Set(['.ts', '.tsx']);

/** `text-primary`, `hover:text-brand/80`...; no coincide con `text-primary-text`. */
const TEXTO_DE_RELLENO =
  /(?<![\w-])text-(?:primary|brand|accent|accent-sky|accent-violet|accent-peach|peach|sky|violet)(?:\/\d+)?(?![\w-])/g;

/** `color: rgb(var(--color-primary))`, `color: var(--color-accent-sky) !important`... */
const COLOR_CSS_DE_RELLENO =
  /(?<![\w-])color\s*:\s*(?:rgba?\()?\s*var\(\s*--color-(?:primary|brand|accent|accent-sky|accent-violet|accent-peach)\s*\)/g;

function archivos(carpeta: string, extensiones = EXTENSIONES): string[] {
  return readdirSync(carpeta, { withFileTypes: true }).flatMap((entrada) => {
    const ruta = join(carpeta, entrada.name);
    if (entrada.isDirectory()) return archivos(ruta, extensiones);
    return extensiones.has(extname(entrada.name)) ? [ruta] : [];
  });
}

describe('texto con colores de marca', () => {
  it('src/components y src/app usan la variante *-text, no el relleno', () => {
    const usos = CARPETAS.flatMap((carpeta) => archivos(join(RAIZ_SRC, carpeta))).flatMap((ruta) => {
      const encontrados = readFileSync(ruta, 'utf8').match(TEXTO_DE_RELLENO) ?? [];
      return encontrados.map((clase) => `${relative(RAIZ_SRC, ruta)}: ${clase}`);
    });
    expect(usos).toEqual([]);
  });

  it('la propiedad color: de src/styles usa la variante *-text, no el relleno', () => {
    const usos = archivos(join(RAIZ_SRC, 'styles'), new Set(['.css'])).flatMap((ruta) => {
      const encontrados = readFileSync(ruta, 'utf8').match(COLOR_CSS_DE_RELLENO) ?? [];
      return encontrados.map((uso) => `${relative(RAIZ_SRC, ruta)}: ${uso}`);
    });
    expect(usos).toEqual([]);
  });
});
