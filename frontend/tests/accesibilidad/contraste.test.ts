// @vitest-environment node
/**
 * Prueba automática de contraste WCAG AA de los tokens (FNC-025).
 *
 * Lee `src/styles/tokens.css`, arma cada tema y mide los pares texto/fondo.
 * Mínimo 4.5:1 para texto y 3:1 para bordes de control. Los pares que hoy
 * fallan se marcan con `it.fails` y la tarea DIS que los corregirá
 * (ver `fallas-contraste-conocidas.ts`).
 */
import { describe, expect, it } from 'vitest';
import { CONTEXTOS, cargarContextos, type NombreContexto } from '../utils/tokens-css';
import { MIN_TEXTO, parseColor, razonContraste } from '../utils/wcag';
import { FALLAS_CONOCIDAS, tareaPendiente } from './fallas-contraste-conocidas';
import { medir } from './medir';
import { PARES } from './pares-contraste';

const contextos = cargarContextos();
const nombres = Object.keys(contextos) as NombreContexto[];

describe('cálculo WCAG', () => {
  it('negro sobre blanco da 21:1 y un color consigo mismo 1:1', () => {
    const negro = parseColor('0 0 0');
    const blanco = parseColor('255 255 255');
    expect(razonContraste(negro, blanco)).toBeCloseTo(21, 5);
    expect(razonContraste(blanco, blanco)).toBeCloseTo(1, 5);
  });

  it('gris 118 sobre blanco queda justo en 4.5:1', () => {
    const gris = parseColor('118 118 118');
    expect(razonContraste(gris, parseColor('255 255 255'))).toBeGreaterThanOrEqual(MIN_TEXTO);
  });
});

describe('bloque de SO oscuro', () => {
  it('solo existen 3 contextos: claro, oscuro del sistema y html.dark (DIS-054)', () => {
    expect(Object.keys(CONTEXTOS)).toEqual(['claro', 'so-oscuro', 'html.dark']);
    expect(CONTEXTOS['so-oscuro']).toBe(':root:not(.light)');
  });
});

describe('lista de fallas conocidas', () => {
  it('solo nombra pares que existen', () => {
    const ids = new Set(PARES.map((p) => p.id));
    expect(FALLAS_CONOCIDAS.map((f) => f.par).filter((id) => !ids.has(id))).toEqual([]);
  });
});

for (const contexto of nombres) {
  describe(`contraste en el tema "${contexto}"`, () => {
    for (const par of PARES) {
      const tarea = tareaPendiente(par.id, contexto);
      const nombre = `${par.id} >= ${par.minimo}:1`;
      const comprobar = () => {
        expect(medir(contextos[contexto], par)).toBeGreaterThanOrEqual(par.minimo);
      };
      if (tarea) {
        // Deuda conocida: la corrige la tarea indicada. Al corregirse, quitarla de la lista.
        it.fails(`${nombre} (falla conocida, la corrige ${tarea})`, comprobar);
      } else {
        it(nombre, comprobar);
      }
    }
  });
}
