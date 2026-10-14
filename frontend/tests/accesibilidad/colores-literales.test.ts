// @vitest-environment node
/**
 * Prueba de cumplimiento de tokens (FNC-025): no deben aparecer colores
 * literales nuevos en `src/components` ni en `src/app`. Los que ya existían
 * están en `colores-literales.excepciones.ts` con la tarea que los corrige.
 */
import { readdirSync, readFileSync } from 'node:fs';
import { extname, join, relative, resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { EXCEPCIONES, type TopeLiterales } from './colores-literales.excepciones';

const RAIZ_SRC = resolve(import.meta.dirname, '../../src');
const CARPETAS = ['components', 'app'];
const EXTENSIONES = new Set(['.ts', '.tsx', '.css']);

const PATRONES = {
  hex: /(?<![\w&])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b/g,
  funcion: /\b(?:rgba?|hsla?)\(\s*[0-9]/g,
  paleta: new RegExp(
    '\\b(?:text|bg|border|ring|from|to|via|fill|stroke|outline|divide|placeholder|accent|caret|decoration|shadow)-' +
      '(?:white|black|(?:slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|' +
      'blue|indigo|violet|purple|fuchsia|pink|rose)-[0-9]{2,3})\\b',
    'g',
  ),
} as const;

type Tipo = keyof typeof PATRONES;
const TIPOS = Object.keys(PATRONES) as Tipo[];

function archivos(carpeta: string): string[] {
  return readdirSync(carpeta, { withFileTypes: true }).flatMap((entrada) => {
    const ruta = join(carpeta, entrada.name);
    if (entrada.isDirectory()) return archivos(ruta);
    return EXTENSIONES.has(extname(entrada.name)) ? [ruta] : [];
  });
}

/** Literales encontrados por archivo (ruta relativa a `src/`). */
function contar(): Record<string, Record<Tipo, string[]>> {
  const resultado: Record<string, Record<Tipo, string[]>> = {};
  for (const carpeta of CARPETAS) {
    for (const ruta of archivos(join(RAIZ_SRC, carpeta))) {
      const texto = readFileSync(ruta, 'utf8');
      const clave = relative(RAIZ_SRC, ruta).split('\\').join('/');
      const literales = (tipo: Tipo): string[] => [...(texto.match(PATRONES[tipo]) ?? [])];
      resultado[clave] = {
        hex: literales('hex'),
        funcion: literales('funcion'),
        paleta: literales('paleta'),
      };
    }
  }
  return resultado;
}

const encontrados = contar();
const SIN_EXCEPCION: TopeLiterales = { hex: 0, funcion: 0, paleta: 0, tarea: '' };

describe('colores literales en src/components y src/app', () => {
  it('revisa archivos de las dos carpetas', () => {
    const claves = Object.keys(encontrados);
    expect(claves.some((c) => c.startsWith('components/'))).toBe(true);
    expect(claves.some((c) => c.startsWith('app/'))).toBe(true);
  });

  it('las excepciones solo nombran archivos que existen', () => {
    expect(Object.keys(EXCEPCIONES).filter((archivo) => !(archivo in encontrados))).toEqual([]);
  });

  for (const archivo of Object.keys(encontrados).sort()) {
    it(`${archivo} no agrega colores literales`, () => {
      const tope = EXCEPCIONES[archivo] ?? SIN_EXCEPCION;
      for (const tipo of TIPOS) {
        const lista = encontrados[archivo][tipo];
        expect(
          lista.length,
          `${archivo}: ${tipo} = ${lista.length} [${lista.join(', ')}], tope ${tope[tipo]}. ` +
            'Si subió, usa tokens (src/styles/tokens.css). Si bajó, actualiza el tope en ' +
            'colores-literales.excepciones.ts.',
        ).toBe(tope[tipo]);
      }
    });
  }
});
