// @vitest-environment node
/**
 * Prueba de cumplimiento de tokens (FNC-025, DIS-009, DIS-012): no deben aparecer
 * colores literales en `src/components`, `src/app` ni en los CSS de
 * `src/styles` (`components.css`, `global.css`; `tokens.css` es el único lugar
 * donde viven los valores). Los que se justifican están en
 * `colores-literales.excepciones.ts` con su motivo.
 *
 * En los CSS también se buscan los nombres de color (`white`, `black`, `red`...)
 * en las declaraciones, y los comentarios no cuentan.
 */
import { readdirSync, readFileSync } from 'node:fs';
import { extname, join, relative, resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { EXCEPCIONES, type TopeLiterales } from './colores-literales.excepciones';

const RAIZ_SRC = resolve(import.meta.dirname, '../../src');
const CARPETAS = ['components', 'app', 'styles'];
/** El único archivo donde los colores literales son válidos: son los tokens. */
const ARCHIVOS_DE_TOKENS = new Set(['styles/tokens.css']);
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
  // Solo se aplica a los CSS, sobre las declaraciones (`propiedad: valor;`).
  nombre: /(?<![\w#.$-])(?:white|black|red|green|blue|gray|grey|yellow|orange|purple|pink|brown|cyan|magenta)(?![\w-])/g,
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

// Quita los comentarios de bloque del CSS conservando los saltos de línea.
const sinComentarios = (css: string): string => css.replace(/\/\*[\s\S]*?\*\//g, (m) => m.replace(/[^\n]/g, ' '));

/** Valores de las declaraciones de un CSS (`prop: valor;`), sin selectores ni comentarios. */
function declaraciones(css: string): string {
  return [...sinComentarios(css).matchAll(/[\w-]+\s*:\s*([^;{}]+)[;}]/g)].map((m) => m[1]).join('\n');
}

/** Literales encontrados por archivo (ruta relativa a `src/`). */
function contar(): Record<string, Record<Tipo, string[]>> {
  const resultado: Record<string, Record<Tipo, string[]>> = {};
  for (const carpeta of CARPETAS) {
    for (const ruta of archivos(join(RAIZ_SRC, carpeta))) {
      const clave = relative(RAIZ_SRC, ruta).split('\\').join('/');
      if (ARCHIVOS_DE_TOKENS.has(clave)) continue;
      const css = extname(ruta) === '.css';
      const bruto = readFileSync(ruta, 'utf8');
      const texto = css ? sinComentarios(bruto) : bruto;
      const literales = (tipo: Tipo): string[] =>
        tipo === 'nombre'
          ? css ? [...(declaraciones(bruto).match(PATRONES.nombre) ?? [])] : []
          : [...(texto.match(PATRONES[tipo]) ?? [])];
      resultado[clave] = {
        hex: literales('hex'),
        funcion: literales('funcion'),
        paleta: literales('paleta'),
        nombre: literales('nombre'),
      };
    }
  }
  return resultado;
}

const encontrados = contar();
const SIN_EXCEPCION: TopeLiterales = { hex: 0, funcion: 0, paleta: 0, nombre: 0, tarea: '' };

describe('colores literales en src/components, src/app y los CSS de src/styles', () => {
  it('revisa archivos de las tres carpetas, sin tokens.css', () => {
    const claves = Object.keys(encontrados);
    expect(claves.some((c) => c.startsWith('components/'))).toBe(true);
    expect(claves.some((c) => c.startsWith('app/'))).toBe(true);
    expect(claves).toContain('styles/components.css');
    expect(claves).toContain('styles/global.css');
    expect(claves).not.toContain('styles/tokens.css');
  });

  it('detecta los literales que dice detectar (el patrón no está roto)', () => {
    const veces = (texto: string, tipo: Tipo): number => (texto.match(PATRONES[tipo]) ?? []).length;
    // Los ejemplos se arman por partes para que ni esta prueba lleve un literal.
    expect(veces(`color: ${'#'}fff; a: ${'#'}ffffff80`, 'hex')).toBe(2);
    expect(veces(`background: rgba${'(0, 0, 0, .5)'}`, 'funcion')).toBe(1);
    expect(veces(declaraciones('a { border: 2px solid white; }'), 'nombre')).toBe(1);
    expect(veces(declaraciones('a { white-space: nowrap; color: rgb(var(--c)); }'), 'nombre')).toBe(0);
    expect(veces(declaraciones('/* color: white; */ .red-x { top: 0; }'), 'nombre')).toBe(0);
    expect(veces('rgb(var(--color-shadow) / 0.2)', 'funcion')).toBe(0);
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
        ).toBe(tope[tipo] ?? 0);
      }
    });
  }
});
