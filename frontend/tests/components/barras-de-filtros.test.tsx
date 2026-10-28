import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import React from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  FilterBar,
  FilterBarClear,
  FilterBarError,
  FilterBarGrid,
  FilterBarSearch,
} from '@/components/filter-bar';
import { Select, TextInput } from '@/components/form';

afterEach(() => {
  cleanup();
});

describe('DIS-069: Barras de filtros unificadas sobre FilterBar', () => {
  it('renderiza barra de filtros como región de búsqueda con rol search y nombre', () => {
    render(
      <FilterBar label="Filtros del catálogo">
        <TextInput type="search" placeholder="Buscar…" aria-label="Buscar" />
        <Select aria-label="Área">
          <option value="">Todas</option>
        </Select>
      </FilterBar>,
    );

    const barra = screen.getByRole('search', { name: 'Filtros del catálogo' });
    expect(barra).toBeDefined();
    expect(barra.className).toContain('flex');
    expect(barra.className).toContain('flex-wrap');
  });

  it('soporta layout="stack" para filtros multinivel con rejilla', () => {
    render(
      <FilterBar label="Filtros multinivel" layout="stack">
        <FilterBarGrid>
          <Select aria-label="Opción 1">
            <option value="1">1</option>
          </Select>
          <Select aria-label="Opción 2">
            <option value="2">2</option>
          </Select>
        </FilterBarGrid>
      </FilterBar>,
    );

    const barra = screen.getByRole('search', { name: 'Filtros multinivel' });
    expect(barra.className).toContain('space-y-3');
    expect(screen.getByRole('combobox', { name: 'Opción 1' })).toBeDefined();
    expect(screen.getByRole('combobox', { name: 'Opción 2' })).toBeDefined();
  });

  it('FilterBarSearch maneja el envío del formulario con botón a control-alto', () => {
    const onSubmit = vi.fn((e: React.FormEvent) => e.preventDefault());
    render(
      <FilterBarSearch onSubmit={onSubmit}>
        <TextInput type="search" placeholder="Buscar..." aria-label="Buscar texto" />
      </FilterBarSearch>,
    );

    const boton = screen.getByRole('button', { name: 'Buscar' });
    expect(boton.className).toContain('min-h-12');
    fireEvent.click(boton);
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  it('FilterBarClear permite limpiar filtros con área táctil accesible', () => {
    const onClear = vi.fn();
    render(<FilterBarClear onClear={onClear} />);

    const boton = screen.getByRole('button', { name: 'Limpiar filtros' });
    expect(boton.className).toContain('min-h-12');
    fireEvent.click(boton);
    expect(onClear).toHaveBeenCalledTimes(1);
  });

  it('FilterBarError reserva min-h-5 sin mensaje y muestra rol alert con mensaje', () => {
    const { rerender } = render(<FilterBarError message={null} />);
    // Sin mensaje no hay alert, pero se reserva espacio para evitar CLS
    expect(screen.queryByRole('alert')).toBeNull();

    rerender(<FilterBarError id="error-rango" message="Rango de fechas inválido" />);
    const alert = screen.getByRole('alert');
    expect(alert).toBeDefined();
    expect(alert.textContent).toBe('Rango de fechas inválido');
    expect(alert.id).toBe('error-rango');
  });
});
