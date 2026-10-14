/**
 * Mide la razón de contraste de un par de tokens en un contexto (FNC-025).
 * Compone el fondo con alpha sobre su superficie (`sobre`, o el fondo de la
 * página) y el texto con alpha sobre el fondo resultante.
 */
import { resolver, type Variables } from '../utils/tokens-css';
import { componer, parseColor, razonContraste } from '../utils/wcag';
import type { ParContraste } from './pares-contraste';

export function medir(variables: Variables, par: ParContraste): number {
  const color = (nombre: string) => parseColor(resolver(variables, nombre));
  const superficie = color(par.sobre ?? '--color-body-bg');
  const fondo = componer(color(par.fondo), superficie);
  const frente = componer(color(par.texto), fondo);
  return razonContraste(frente, fondo);
}
