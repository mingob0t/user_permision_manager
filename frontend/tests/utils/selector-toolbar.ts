/**
 * Ayudas de prueba para `SelectorToolbar` (DIS-158): abrir, leer opciones y elegir por texto.
 */
import { fireEvent, screen } from '@testing-library/react';

/** Botón del selector por su nombre accesible. */
export function selector(etiqueta: string): HTMLElement {
  return screen.getByLabelText(etiqueta);
}

/** Texto del valor actual (la descripción del botón). */
export function valorSelector(etiqueta: string): string {
  const id = selector(etiqueta).getAttribute('aria-describedby') ?? '';
  return document.getElementById(id)?.textContent ?? '';
}

/** Textos de las opciones; abre y vuelve a cerrar el menú. */
export function opcionesSelector(etiqueta: string): string[] {
  fireEvent.click(selector(etiqueta));
  const textos = screen.getAllByRole('option').map((o) => o.textContent ?? '');
  fireEvent.click(selector(etiqueta));
  return textos;
}

/** Abre el selector y elige la opción con ese texto. */
export function elegirEnSelector(etiqueta: string, texto: string): void {
  fireEvent.click(selector(etiqueta));
  fireEvent.click(screen.getByRole('option', { name: texto }));
}
