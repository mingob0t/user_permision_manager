import { cleanup, render, screen } from '@testing-library/react';
import React from 'react';
import { afterEach, describe, expect, it } from 'vitest';
import { Brand } from '@/components/brand';
import NotFound from '@/app/not-found';

afterEach(() => {
  cleanup();
});

describe('DIS-063 Marco e Identidad', () => {
  it('renderiza Brand con el nombre Nexus y subtítulo opcional', () => {
    const { rerender } = render(<Brand size="md" />);
    expect(screen.getByText('Nexus')).toBeDefined();
    expect(screen.queryByText(/Catálogo centralizado/)).toBeNull();

    rerender(<Brand size="lg" subtitle />);
    expect(screen.getByText('Nexus')).toBeDefined();
    expect(screen.getByText('Catálogo centralizado de plataformas')).toBeDefined();
  });

  it('NotFound integra Brand y botón de retorno al inicio', () => {
    render(<NotFound />);
    expect(screen.getByText('Nexus')).toBeDefined();
    expect(screen.getByText('404')).toBeDefined();
    const link = screen.getByRole('link', { name: 'Volver al inicio' });
    expect(link).toBeDefined();
    expect(link.getAttribute('href')).toBe('/');
  });
});
