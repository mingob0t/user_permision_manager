/** DIS-051: sin botón dentro de enlace y foco estable al quitar un favorito en /favorites. */
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Platform } from '@/lib/types';

const api = vi.hoisted(() => ({
  favorites: vi.fn(), toggleFavorite: vi.fn(), registerVisit: vi.fn(),
}));
vi.mock('@/lib/api', () => ({ api }));
vi.mock('@/components/toast', () => ({ useToast: () => ({ avisar: vi.fn() }) }));

import { FavoritesList } from '@/components/favorites-list';
import { PlatformCard } from '@/components/platform-card';

const plataforma = (id: number, name: string) => ({
  id, name, description: 'x', area_name: null, status: 'Activo', is_favorite: true,
  bg_color: '', text_color: '', direct_link: `https://${name.toLowerCase()}.ejemplo.local`,
}) as unknown as Platform;

const A = plataforma(1, 'Alfa');
const B = plataforma(2, 'Beta');
const C = plataforma(3, 'Gama');

/** Quita `id` desde su estrella; la API devuelve la lista restante. */
async function quitar(id: number, nombre: string, restantes: Platform[]) {
  api.toggleFavorite.mockResolvedValue({ is_favorite: false });
  api.favorites.mockResolvedValue(restantes);
  const estrella = await screen.findByRole('button', { name: `Favorito: ${nombre}` });
  estrella.focus();
  await act(async () => { fireEvent.click(estrella); });
  expect(id).toBeGreaterThan(0);
}

beforeEach(() => { api.registerVisit.mockResolvedValue(undefined); });
afterEach(() => { cleanup(); vi.clearAllMocks(); });

describe('PlatformCard: sin interactivos anidados', () => {
  it.each(['https://wiki.ejemplo.local', 'http://inseguro.local'])('%s: ningún button dentro de a', (url) => {
    const { container } = render(<PlatformCard platform={{ ...A, direct_link: url }} />);
    expect(container.querySelectorAll('a button, button a')).toHaveLength(0);
    expect(screen.getByRole('button', { name: 'Favorito: Alfa' })).toBeTruthy();
  });

  it('el enlace es el nombre y cuenta la visita', () => {
    render(<PlatformCard platform={A} />);
    const enlace = screen.getByRole('link', { name: 'Alfa' });
    fireEvent.click(enlace);
    expect(api.registerVisit).toHaveBeenCalledWith(1);
  });

  it('el enlace cubre la tarjeta (sostiene la excepción de área táctil)', () => {
    render(<PlatformCard platform={A} />);
    const enlace = screen.getByRole('link', { name: 'Alfa' });
    expect(enlace.className).toContain('after:absolute');
    expect(enlace.className).toContain('after:inset-0');
  });
});

describe('FavoritesList: foco al quitar un favorito', () => {
  it('pasa a la siguiente tarjeta', async () => {
    api.favorites.mockResolvedValueOnce([A, B, C]);
    render(<FavoritesList />);
    await quitar(1, 'Alfa', [B, C]);
    await waitFor(() => expect(document.activeElement).toBe(
      screen.getByRole('button', { name: 'Favorito: Beta' })));
    expect(screen.getByText('«Alfa» quitada de favoritos.')).toBeTruthy();
  });

  it('si era la última, pasa a la anterior', async () => {
    api.favorites.mockResolvedValueOnce([A, B]);
    render(<FavoritesList />);
    await quitar(2, 'Beta', [A]);
    await waitFor(() => expect(document.activeElement).toBe(
      screen.getByRole('button', { name: 'Favorito: Alfa' })));
  });

  it('si no queda ninguna, pasa al encabezado', async () => {
    api.favorites.mockResolvedValueOnce([A]);
    render(<FavoritesList />);
    await quitar(1, 'Alfa', []);
    await waitFor(() => expect(document.activeElement).toBe(
      screen.getByRole('heading', { name: 'Favoritos' })));
    expect(screen.getByText(/Todavía no has marcado/)).toBeTruthy();
  });
});
