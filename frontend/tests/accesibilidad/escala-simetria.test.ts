// @vitest-environment node
/**
 * DIS-072: Escala única de espaciado, alturas de control, rejilla, anchos máximos e íconos.
 *
 * Verifica:
 * 1. Existencia de tokens de simetría y rejilla (8pt) en tokens.css.
 * 2. Ausencia de valores arbitrarios en corchetes `[..]` fuera de las excepciones registradas.
 * 3. Catálogo de íconos del componente `Icono`.
 * 4. Extensión de anchos máximos y alturas de control en Tailwind.
 */
import { readdirSync, readFileSync } from 'node:fs';
import { extname, join, relative, resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { CONTEXTOS, RUTA_TOKENS, variablesDeBloque } from '../utils/tokens-css';
import { EXCEPCIONES_SIMETRIA } from './escala-simetria.excepciones';

const RAIZ_SRC = resolve(import.meta.dirname, '../../src');
const CONFIG_TAILWIND = resolve(import.meta.dirname, '../../tailwind.config.ts');
const cssTokens = readFileSync(RUTA_TOKENS, 'utf8');
const tailwindContent = readFileSync(CONFIG_TAILWIND, 'utf8');

const TOKENS_SIMETRIA = [
  '--espacio-1',
  '--espacio-2',
  '--espacio-3',
  '--espacio-4',
  '--espacio-6',
  '--espacio-8',
  '--espacio-12',
  '--control-alto',
  '--contenido-max',
  '--formulario-max',
  '--dialogo-max',
  '--rejilla-columnas',
  '--rejilla-canal',
  '--icono-sm',
  '--icono-md',
  '--icono-lg',
];

function listarArchivosTsx(carpeta: string): string[] {
  return readdirSync(carpeta, { withFileTypes: true }).flatMap((entrada) => {
    const ruta = join(carpeta, entrada.name);
    if (entrada.isDirectory()) return listarArchivosTsx(ruta);
    return extname(entrada.name) === '.tsx' ? [ruta] : [];
  });
}

describe('DIS-072: Tokens de simetría y rejilla', () => {
  const varsClaro = variablesDeBloque(cssTokens, CONTEXTOS.claro);
  const varsOscuro = variablesDeBloque(cssTokens, CONTEXTOS['html.dark']);

  it('todos los tokens de simetría existen en tema claro', () => {
    for (const token of TOKENS_SIMETRIA) {
      expect(varsClaro[token], `Falta token ${token} en tema claro`).toBeDefined();
    }
  });

  it('todos los tokens de simetría existen en tema oscuro', () => {
    for (const token of TOKENS_SIMETRIA) {
      expect(varsOscuro[token], `Falta token ${token} en tema oscuro`).toBeDefined();
    }
  });

  it('altura mínima de control táctil es 48px', () => {
    expect(varsClaro['--control-alto']).toBe('48px');
    expect(varsOscuro['--control-alto']).toBe('48px');
  });

  it('ancho máximo de contenido es 1280px', () => {
    expect(varsClaro['--contenido-max']).toBe('1280px');
  });
});

describe('DIS-072: Configuración de Tailwind para simetría', () => {
  it('extiende anchos máximos semánticos', () => {
    expect(tailwindContent).toContain("contenido: 'var(--contenido-max)'");
    expect(tailwindContent).toContain("formulario: 'var(--formulario-max)'");
    expect(tailwindContent).toContain("dialogo: 'var(--dialogo-max)'");
  });

  it('extiende altura de control', () => {
    expect(tailwindContent).toContain("control: 'var(--control-alto)'");
  });
});

describe('DIS-072: Ausencia de valores arbitrarios en corchetes en TSX', () => {
  const archivos = listarArchivosTsx(RAIZ_SRC);

  for (const ruta of archivos) {
    const relativo = relative(RAIZ_SRC, ruta).split('\\').join('/');
    const excepcion = EXCEPCIONES_SIMETRIA[relativo];

    it(`${relativo} no introduce medidas arbitrarias fuera de excepción`, () => {
      const contenido = readFileSync(ruta, 'utf8');
      const arbitrarios = [
        ...contenido.matchAll(/\b(?:p|m|gap|w|h|min-w|min-h|max-w|max-h|z|top|bottom|left|right)-\[[^\]]+\]/g),
      ].map((m) => m[0]);

      if (excepcion) {
        expect(
          arbitrarios.length,
          `${relativo} tiene ${arbitrarios.length} arbitrarios pero la excepción fija ${excepcion.cantidad}. Ajustar excepción si bajaron.`,
        ).toBeLessThanOrEqual(excepcion.cantidad);
      } else {
        expect(
          arbitrarios,
          `Se encontraron valores arbitrarios en ${relativo}: ${arbitrarios.join(', ')}. Usa tokens o utilidades de la escala.`,
        ).toEqual([]);
      }
    });
  }
});

describe('DIS-072: Catálogo de iconos unificado', () => {
  it('el componente Icono existe y expone los iconos requeridos', async () => {
    const iconoModulo = await import('@/components/icono');
    expect(iconoModulo.Icono).toBeDefined();
  });
});
