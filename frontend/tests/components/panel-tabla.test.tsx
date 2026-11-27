/**
 * DIS-148: las filas de relleno de la tabla de panel no aparentan registros: van vacías
 * (sin barras ni círculos de esqueleto) y continúan la alternancia de color de las reales.
 */
import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { FilasFantasma, claseFilaPanel } from '@/components/panel-tabla';

const GRID = 'sm:grid-cols-[1fr_auto]';

function pintar(cantidad: number, desde: number) {
  const { container } = render(
    <ul>
      <FilasFantasma cantidad={cantidad} desde={desde} claseGrid={GRID} />
    </ul>,
  );
  return Array.from(container.querySelectorAll('li'));
}

describe('FilasFantasma (DIS-148)', () => {
  it('pinta tantas filas como faltan, ocultas al lector de pantalla', () => {
    const filas = pintar(2, 6);
    expect(filas).toHaveLength(2);
    filas.forEach((fila) => expect(fila.getAttribute('aria-hidden')).toBe('true'));
  });

  it('las filas van vacías: sin elementos de esqueleto que parezcan datos', () => {
    pintar(3, 1).forEach((fila) => expect(fila.childElementCount).toBe(0));
  });

  it('siguen la zebra de las filas reales según su posición y sin atenuarse', () => {
    const filas = pintar(2, 6);
    expect(filas[0].className).toContain(claseFilaPanel(6));
    expect(filas[1].className).toContain(claseFilaPanel(7));
    expect(claseFilaPanel(6)).not.toBe(claseFilaPanel(7));
    filas.forEach((fila) => expect(fila.className).not.toMatch(/\bopacity-/));
  });
});
