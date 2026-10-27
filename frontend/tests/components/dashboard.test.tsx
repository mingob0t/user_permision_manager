/**
 * DIS-024: el Panel muestra el resumen por rol y, debajo, "Actividad del
 * portal" (`/stats`) con sus secciones como h3 bajo ese h2 (auditor-accesibilidad).
 */
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const permisos = vi.hoisted(() => ({ is_admin: true, is_area_admin: false }));
const estado = vi.hoisted(() => ({ cargando: false, resumenFalla: false }));

vi.mock('@/lib/api', async (original) => ({
  ...(await original<typeof import('@/lib/api')>()),
  api: {
    stats: vi.fn().mockResolvedValue({
      areas: 1, platforms: 2, visits: 3,
      platforms_by_area: [{ area: 'TI', count: 2, color: '' }],
      most_visited: [{ id: 1, name: 'Wiki', visits: 3 }],
    }),
  },
}));
vi.mock('@/lib/access/home', () => ({
  homeApi: { summary: vi.fn(() => (estado.resumenFalla
    ? Promise.reject(new Error('falla'))
    : Promise.resolve({ scope: 'global', pending_approvals: 0, failed_access: 0, totals: { areas: 1, platforms: 2, active_access: 0 } }))) },
}));
vi.mock('@/components/session-provider', () => ({
  useSession: () => ({
    loading: estado.cargando, error: null,
    session: { preferences: { refresh_interval: 60 }, permissions: permisos },
  }),
}));

import { Dashboard } from '@/components/dashboard';

// recharts (`ResponsiveContainer`) necesita ResizeObserver, que jsdom no trae.
beforeEach(() => {
  vi.stubGlobal('ResizeObserver', class { observe() {} unobserve() {} disconnect() {} });
});

afterEach(() => {
  cleanup();
  permisos.is_admin = true;
  permisos.is_area_admin = false;
  estado.cargando = false;
  estado.resumenFalla = false;
});

/** Contadores (`StatTile`): solo los `<p>`, sin el encabezado de la tabla alternativa. */
const contadores = (etiqueta: string) =>
  screen.queryAllByText(etiqueta).filter((el) => el.tagName === 'P');

describe('Dashboard', () => {
  it('secciones de /stats como h3 bajo el h2 "Actividad del portal"', async () => {
    render(<Dashboard />);
    expect(await screen.findByRole('heading', { level: 2, name: 'Actividad del portal' })).toBeTruthy();
    expect(screen.getByRole('heading', { level: 3, name: 'Plataformas por área' })).toBeTruthy();
    expect(screen.getByRole('heading', { level: 3, name: 'Más visitadas' })).toBeTruthy();
  });

  it('la gráfica tiene una tabla alternativa con los mismos datos (DIS-003)', async () => {
    render(<Dashboard />);
    const tabla = await screen.findByRole('table', { name: 'Plataformas por área' });
    expect(tabla.textContent).toContain('TI');
    expect(tabla.textContent).toContain('2');
  });

  it('el admin no ve Áreas y Plataformas repetidos; sí Visitas (DIS-037)', async () => {
    render(<Dashboard />);
    await screen.findByRole('heading', { level: 2, name: 'Actividad del portal' });
    // Una sola vez: la del resumen por rol.
    expect(await screen.findAllByText('Áreas')).toHaveLength(1);
    expect(contadores('Plataformas')).toHaveLength(1);
    expect(screen.getByText('Visitas')).toBeTruthy();
  });

  it('quien no tiene resumen de totales conserva Áreas y Plataformas (DIS-037)', async () => {
    permisos.is_admin = false;
    render(<Dashboard />);
    await screen.findByRole('heading', { level: 2, name: 'Actividad del portal' });
    expect(contadores('Áreas')).toHaveLength(2);
    expect(contadores('Plataformas')).toHaveLength(2);
  });

  it('no muestra Áreas ni Plataformas mientras carga la sesión (DIS-037)', async () => {
    permisos.is_admin = false;
    estado.cargando = true;
    render(<Dashboard />);
    await screen.findByRole('heading', { level: 2, name: 'Actividad del portal' });
    // Solo los del resumen por rol (el mock es global): ninguno de /stats.
    expect(contadores('Áreas')).toHaveLength(1);
    expect(contadores('Plataformas')).toHaveLength(1);
  });

  it('si el resumen falla, el admin recupera Áreas y Plataformas de /stats (DIS-037)', async () => {
    estado.resumenFalla = true;
    render(<Dashboard />);
    await screen.findByRole('heading', { level: 2, name: 'Actividad del portal' });
    await waitFor(() => expect(contadores('Áreas')).toHaveLength(1));
    expect(contadores('Plataformas')).toHaveLength(1);
  });
});
