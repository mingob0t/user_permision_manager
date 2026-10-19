/**
 * SEG-24 del frontend (DIS-017): `PlatformCard` solo pinta en `href` enlaces
 * https://; cualquier otro esquema deja la tarjeta sin enlace.
 */
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { Platform } from '@/lib/types';

vi.mock('@/lib/api', () => ({ api: { toggleFavorite: vi.fn(), registerVisit: vi.fn() } }));

import { PlatformCard } from '@/components/platform-card';
import { enlaceSeguro } from '@/lib/enlace-seguro';

const BASE = {
  id: 1, name: 'Wiki', description: 'Wiki interna', area_name: null, status: 'Activo',
  is_favorite: false, bg_color: '', text_color: '',
} as unknown as Platform;

afterEach(() => cleanup());

describe('PlatformCard: SEG-24', () => {
  it('https: es un enlace', () => {
    render(<PlatformCard platform={{ ...BASE, direct_link: 'https://wiki.ejemplo.local' }} />);
    expect(screen.getByRole('link').getAttribute('href')).toBe('https://wiki.ejemplo.local/');
  });

  it.each(['javascript:alert(1)', 'http://wiki.ejemplo.local', 'data:text/html,x'])(
    '%s: sin enlace', (url) => {
      render(<PlatformCard platform={{ ...BASE, direct_link: url }} />);
      expect(screen.queryByRole('link')).toBeNull();
      expect(screen.getByText('Sin enlace')).toBeTruthy();
    });
});

describe('enlaceSeguro', () => {
  it.each([
    ['https://a.ejemplo.local/x', 'https://a.ejemplo.local/x'],
    ['  https://a.ejemplo.local  ', 'https://a.ejemplo.local/'],
    ['https://user:pw@a.ejemplo.local', null],
    ['HTTP://a.ejemplo.local', null],
    ['https:// a.ejemplo.local', null],
    ['', null],
    [null, null],
  ])('%s → %s', (entrada, esperado) => {
    expect(enlaceSeguro(entrada)).toBe(esperado);
  });
});

describe('enlaceSeguro: normalizado (auditor-seguridad)', () => {
  it('devuelve el href normalizado, no el texto crudo', () => {
    expect(enlaceSeguro('https://A.Ejemplo.LOCAL')).toBe('https://a.ejemplo.local/');
  });
});
