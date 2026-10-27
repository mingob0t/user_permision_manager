// @vitest-environment node
/**
 * DIS-038: el velo (`--color-overlay`, con su opacidad) detrás de `Modal` y del menú
 * móvil. No es texto: lo que se exige es que el panel se distinga del velo (no
 * textual, 3:1 WCAG 1.4.11) por su relleno o por su borde, en los 7 temas y con el
 * velo compuesto tanto sobre el fondo de página como sobre un `Card`.
 *
 * - `Modal`: relleno `--color-panel-fill` y borde de 2 px `--color-panel-border` (`.nx-modal-glass`).
 * - Menú móvil: relleno `--color-panel-fill` y borde de 2 px `--color-primary` (`border-primary`).
 * En los temas claros se distingue el relleno; en los oscuros, el borde.
 */
import { describe, expect, it } from 'vitest';
import { cargarContextos, resolver, type NombreContexto } from '../utils/tokens-css';
import { MIN_NO_TEXTO, componer, parseColor, razonContraste } from '../utils/wcag';

const contextos = cargarContextos();
const PANELES = {
  modal: ['--color-panel-fill', '--color-panel-border'],
  'menú móvil': ['--color-panel-fill', '--color-primary'],
} as const;
const DEBAJO = ['--color-body-bg', '--color-panel-fill'] as const;

for (const contexto of Object.keys(contextos) as NombreContexto[]) {
  describe(`velo en el tema "${contexto}"`, () => {
    const color = (nombre: string) => parseColor(resolver(contextos[contexto], nombre));

    it('el velo tiene opacidad parcial (deja ver el contexto)', () => {
      const velo = color('--color-overlay');
      expect(velo.a).toBeGreaterThan(0);
      expect(velo.a).toBeLessThan(1);
    });

    for (const [panel, partes] of Object.entries(PANELES)) {
      for (const debajo of DEBAJO) {
        it(`${panel}: relleno o borde >= ${MIN_NO_TEXTO}:1 contra el velo sobre ${debajo}`, () => {
          const velo = componer(color('--color-overlay'), color(debajo));
          const mejor = Math.max(...partes.map((parte) => razonContraste(color(parte), velo)));
          expect(mejor).toBeGreaterThanOrEqual(MIN_NO_TEXTO);
        });
      }
    }
  });
}
