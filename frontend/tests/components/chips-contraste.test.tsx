/** DIS-048: el texto de los chips no se pinta con el color libre del dato. */
import { readFileSync } from 'node:fs';
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { Platform } from '@/lib/types';

vi.mock('@/lib/api', () => ({ api: { toggleFavorite: vi.fn(), registerVisit: vi.fn() } }));

import { PlatformCard } from '@/components/platform-card';

const CSS = readFileSync('src/styles/components.css', 'utf8');
const TOKENS = readFileSync('src/styles/tokens.css', 'utf8');
const regla = (sel: string) => new RegExp(`\\.${sel}\\s*\\{([^}]*)\\}`).exec(CSS)?.[1] ?? '';

const PLATAFORMA = {
  id: 1, name: 'Wiki', description: 'x', area_name: 'Finanzas', area_color: '',
  status: 'Activo', is_favorite: false, direct_link: 'https://wiki.ejemplo.local',
  bg_color: '', text_color: '',
} as unknown as Platform;

afterEach(() => cleanup());

describe('chips de color libre', () => {
  it('.nx-chip-tint: el texto es del tema, no --chip-color', () => {
    const css = regla('nx-chip-tint');
    expect(css).toMatch(/color:\s*var\(--color-body-text\)/);
    expect(css).not.toMatch(/(^|[^-])color:\s*var\(--chip-color\)/);
  });

  it('.nx-chip-solid: el texto sale de tokens, nunca de --chip-fg ni del text_color', () => {
    expect(CSS).not.toMatch(/--chip-fg/);
    expect(CSS).toMatch(/\.nx-chip-solid\[data-texto='sobre-oscuro'\]\s*\{[^}]*--color-texto-sobre-fondo-oscuro/);
    expect(CSS).toMatch(/\.nx-chip-solid\[data-texto='sobre-claro'\]\s*\{[^}]*--color-texto-sobre-fondo-claro/);
  });

  it('los tokens de texto sobre fondo libre existen en los 7 temas', () => {
    expect(TOKENS.match(/--color-texto-sobre-fondo-oscuro:/g)).toHaveLength(7);
    expect(TOKENS.match(/--color-texto-sobre-fondo-claro:/g)).toHaveLength(7);
  });

  it('PlatformCard: el chip de área no lleva color de texto en línea; el ícono, sin fondo válido, cae al tema', () => {
    render(<PlatformCard platform={PLATAFORMA} />);
    expect(screen.getByText('Finanzas').getAttribute('style') ?? '').not.toMatch(/(^|[^-])color\s*:/);
    const icono = document.querySelector('.nx-chip-solid');
    expect(icono?.hasAttribute('data-texto')).toBe(false);
    expect(icono?.getAttribute('style') ?? '').not.toContain('--chip-fg');
  });
});
