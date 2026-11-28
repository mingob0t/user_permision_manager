/**
 * SelectorToolbar (DIS-158): estándar de la barra de Plataformas en un componente reutilizable.
 */
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { SelectorToolbar } from '@/components/selector-toolbar';

const OPCIONES = [
  { valor: 'todas', texto: 'Todas' },
  { valor: 'a', texto: 'Alfa' },
  { valor: 'b', texto: 'Beta' },
];

function pintar(valor = 'todas', onChange = vi.fn()) {
  render(
    <div>
      <SelectorToolbar id="sel" etiqueta="Estado" icono="inventario" valor={valor}
        opciones={OPCIONES} onChange={onChange} ariaLabel="Filtrar por estado" />
      <p>fuera</p>
    </div>,
  );
  return { onChange, boton: screen.getByLabelText('Filtrar por estado') };
}

afterEach(cleanup);

describe('SelectorToolbar', () => {
  it('muestra «Etiqueta: valor», anuncia el valor y usa las clases del estándar', () => {
    const { boton } = pintar('a');
    expect(boton.textContent).toContain('Estado:');
    expect(boton.textContent).toContain('Alfa');
    expect(document.getElementById(boton.getAttribute('aria-describedby') ?? '')?.textContent).toBe('Alfa');
    expect(boton.className).toContain('h-12');
    expect(boton.className).toContain('w-48');
    // Valor distinto del primero: destacado.
    expect(boton.className).toContain('border-primary/60');
  });

  it('abre el menú con la opción elegida marcada y con foco; elegir llama onChange y cierra', () => {
    const { boton, onChange } = pintar();
    expect(boton.getAttribute('aria-expanded')).toBe('false');
    fireEvent.click(boton);
    expect(boton.getAttribute('aria-expanded')).toBe('true');
    const elegida = screen.getByRole('option', { name: 'Todas' });
    expect(elegida.getAttribute('aria-selected')).toBe('true');
    expect(document.activeElement).toBe(elegida);
    fireEvent.click(screen.getByRole('option', { name: 'Beta' }));
    expect(onChange).toHaveBeenCalledWith('b');
    expect(screen.queryByRole('listbox')).toBeNull();
    expect(document.activeElement).toBe(boton);
  });

  it('flechas, Inicio y Fin recorren; Escape cierra y devuelve el foco', () => {
    const { boton } = pintar();
    fireEvent.click(boton);
    const lista = screen.getByRole('listbox');
    fireEvent.keyDown(lista, { key: 'ArrowDown' });
    expect(document.activeElement?.textContent).toBe('Alfa');
    fireEvent.keyDown(lista, { key: 'End' });
    expect(document.activeElement?.textContent).toBe('Beta');
    fireEvent.keyDown(lista, { key: 'Home' });
    expect(document.activeElement?.textContent).toContain('Todas');
    fireEvent.keyDown(lista, { key: 'Escape' });
    expect(screen.queryByRole('listbox')).toBeNull();
    expect(document.activeElement).toBe(boton);
  });

  it('clic fuera cierra; elegir el mismo valor no llama onChange', () => {
    const { boton, onChange } = pintar();
    fireEvent.click(boton);
    fireEvent.mouseDown(screen.getByText('fuera'));
    expect(screen.queryByRole('listbox')).toBeNull();
    fireEvent.click(boton);
    fireEvent.click(screen.getByRole('option', { name: 'Todas' }));
    expect(onChange).not.toHaveBeenCalled();
  });
});
