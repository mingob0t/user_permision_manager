import { cleanup, render, screen } from '@testing-library/react';
import React from 'react';
import { afterEach, describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { RegionDeAviso, Skeleton } from '@/components/ui';

afterEach(() => {
  cleanup();
});

describe('DIS-073: Estabilidad de diseño (CLS) y movimiento reducido', () => {
  it('Skeleton renderiza con rol status y accesible en variantes fila, tarjeta y contador', () => {
    const { rerender } = render(<Skeleton variant="fila" ariaLabel="Cargando tabla…" />);
    const fila = screen.getByRole('status', { name: 'Cargando tabla…' });
    expect(fila).toBeDefined();
    expect(fila.className).toContain('min-h-12');

    rerender(<Skeleton variant="tarjeta" ariaLabel="Cargando tarjeta…" />);
    const tarjeta = screen.getByRole('status', { name: 'Cargando tarjeta…' });
    expect(tarjeta).toBeDefined();
    expect(tarjeta.className).toContain('min-h-36');

    rerender(<Skeleton variant="contador" ariaLabel="Cargando métrica…" />);
    const contador = screen.getByRole('status', { name: 'Cargando métrica…' });
    expect(contador).toBeDefined();
    expect(contador.className).toContain('min-h-24');
  });

  it('Skeleton genera múltiples elementos si count > 1', () => {
    render(<Skeleton variant="fila" count={3} ariaLabel="Cargando lista…" />);
    const items = screen.getAllByRole('status', { name: 'Cargando lista…' });
    expect(items.length).toBe(3);
  });

  it('RegionDeAviso mantiene reserva de espacio y canal aria-live', () => {
    render(
      <RegionDeAviso minHeight="min-h-8">
        <span>Aviso importante</span>
      </RegionDeAviso>,
    );
    const aviso = screen.getByText('Aviso importante');
    expect(aviso).toBeDefined();
    const contenedor = aviso.parentElement;
    expect(contenedor?.getAttribute('aria-live')).toBe('polite');
    expect(contenedor?.className).toContain('min-h-8');
  });

  it('global.css contiene scrollbar-gutter: stable en contenedores desplazables', () => {
    const css = readFileSync(resolve(__dirname, '../../src/styles/global.css'), 'utf-8');
    expect(css).toContain('scrollbar-gutter: stable');
  });

  it('components.css contiene regla de prefers-reduced-motion para nx-modal-glass', () => {
    const css = readFileSync(resolve(__dirname, '../../src/styles/components.css'), 'utf-8');
    expect(css).toContain('@media (prefers-reduced-motion: reduce)');
    expect(css).toContain('animation: none');
  });
});
