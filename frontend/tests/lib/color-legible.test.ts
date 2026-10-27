/** DIS-048: la elección de texto del chip de plataforma cumple AA con cualquier fondo (por canales). */
import { describe, expect, it } from 'vitest';
import { eleccionPorCanales, textoLegible, variablesChipPlataforma } from '@/lib/color-legible';
import { MIN_TEXTO, razonContraste } from '../utils/wcag';

type Canales = [number, number, number];
const rgba = ([r, g, b]: Canales) => ({ r, g, b, a: 1 });
/** Canal del texto: 255 (blanco) si la elección es `claro`, 0 (negro) si es `oscuro`. */
const texto = (e: 'claro' | 'oscuro'): Canales => (e === 'claro' ? [255, 255, 255] : [0, 0, 0]);
const razon = (fondo: Canales) => razonContraste(rgba(fondo), rgba(texto(eleccionPorCanales(fondo))));

/** El primero es el color por defecto de las áreas (99, 102, 241), el que motivó la tarea. */
const FONDOS: Canales[] = [[99, 102, 241], [255, 255, 255], [0, 0, 0], [128, 128, 128], [119, 119, 119],
  [255, 255, 0], [37, 99, 235], [239, 68, 68], [16, 185, 129], [245, 158, 11], [15, 23, 42],
  [118, 118, 118], [89, 89, 89]];

describe('eleccionPorCanales', () => {
  it.each(FONDOS)('fondo %i,%i,%i: la elección da al menos 4,5:1', (...f) => {
    expect(razon(f)).toBeGreaterThanOrEqual(MIN_TEXTO);
  });

  it('el color por defecto de las áreas lleva texto oscuro (el claro daba 4,47:1)', () => {
    expect(eleccionPorCanales([99, 102, 241])).toBe('oscuro');
  });

  it('barrido de grises y primarios: nunca baja de 4,5:1', () => {
    for (let v = 0; v < 256; v += 5) {
      const fondos: Canales[] = [[v, v, v], [v, 0, 0], [0, v, 0], [0, 0, v], [v, v, 0]];
      for (const f of fondos) expect(razon(f)).toBeGreaterThanOrEqual(MIN_TEXTO);
    }
  });

  it('extremos: fondo negro, texto claro; fondo blanco, texto oscuro', () => {
    expect(eleccionPorCanales([0, 0, 0])).toBe('claro');
    expect(eleccionPorCanales([255, 255, 255])).toBe('oscuro');
  });
});

describe('sin fondo válido', () => {
  it.each(['', null, undefined, 'rojo', 'no-es-color'])('%s: sin elección ni variables', (v) => {
    expect(textoLegible(v)).toBeNull();
    expect(Object.keys(variablesChipPlataforma(v))).toHaveLength(0);
  });
});
