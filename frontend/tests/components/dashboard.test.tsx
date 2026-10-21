/**
 * DIS-024: el Panel muestra el resumen por rol y, debajo, "Actividad del
 * portal" (`/stats`) con sus secciones como h3 bajo ese h2 (auditor-accesibilidad).
 */
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

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
  homeApi: { summary: vi.fn().mockResolvedValue({ scope: 'global', pending_approvals: 0, failed_access: 0, totals: { areas: 1, platforms: 2, active_access: 0 } }) },
}));
vi.mock('@/components/session-provider', () => ({
  useSession: () => ({
    loading: false, error: null,
    session: { preferences: { refresh_interval: 60 }, permissions: { is_admin: true } },
  }),
}));

import { Dashboard } from '@/components/dashboard';

// recharts (`ResponsiveContainer`) necesita ResizeObserver, que jsdom no trae.
beforeEach(() => {
  vi.stubGlobal('ResizeObserver', class { observe() {} unobserve() {} disconnect() {} });
});

afterEach(cleanup);

describe('Dashboard', () => {
  it('secciones de /stats como h3 bajo el h2 "Actividad del portal"', async () => {
    render(<Dashboard />);
    expect(await screen.findByRole('heading', { level: 2, name: 'Actividad del portal' })).toBeTruthy();
    expect(screen.getByRole('heading', { level: 3, name: 'Plataformas por área' })).toBeTruthy();
    expect(screen.getByRole('heading', { level: 3, name: 'Más visitadas' })).toBeTruthy();
  });
});
