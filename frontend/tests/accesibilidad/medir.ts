/**
 * Mide la razón de contraste de un par de tokens en un contexto (FNC-025).
 * Compone el fondo con alpha sobre su superficie (`sobre`, o el fondo de la
 * página) y el texto con alpha sobre el fondo resultante. `alfaFondo`
 * sustituye la opacidad del fondo (utilidades `bg-x/NN`, DIS-001) y
 * `alfaTexto` la del texto (`placeholder:text-x/NN`, DIS-013).
 */
import { resolver, type Variables } from '../utils/tokens-css';
import { componer, parseColor, razonContraste } from '../utils/wcag';
import type { ParContraste } from './pares-contraste';

export function medir(variables: Variables, par: ParContraste): number {
  const color = (nombre: string) => parseColor(resolver(variables, nombre));
  const superficie = color(par.sobre ?? '--color-body-bg');
  const base = color(par.fondo);
  const fondo = componer(par.alfaFondo === undefined ? base : { ...base, a: par.alfaFondo }, superficie);
  const texto = color(par.texto);
  const frente = componer(par.alfaTexto === undefined ? texto : { ...texto, a: par.alfaTexto }, fondo);
  return razonContraste(frente, fondo);
}
