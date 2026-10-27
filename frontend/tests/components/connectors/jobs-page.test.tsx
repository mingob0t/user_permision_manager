/**
 * DIS-041: pantalla /admin/jobs (bitácora de ejecuciones del admin de área).
 * - Por rol: usuario sin permiso (sin llamar a la API); admin de área la ve de solo
 *   lectura (sin "Reintentar"); superadmin la ve con "Reintentar".
 * - Estados: carga, vacío y error.
 */
import { cleanup, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Job, Paginated } from '@/lib/access/types';

vi.mock('@/lib/access/provisioning', () => ({
  provisioningApi: { jobs: vi.fn(), job: vi.fn(), retry: vi.fn() },
}));
vi.mock('@/lib/api', async (original) => ({
  ...(await original<typeof import('@/lib/api')>()),
  api: { platforms: vi.fn(), areas: vi.fn() },
}));
vi.mock('@/components/app-shell', () => ({ AppShell: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

type Rol = 'usuario' | 'admin_area' | 'administrador';
let rol: Rol = 'admin_area';
vi.mock('@/components/session-provider', () => ({
  useSession: () => ({
    loading: false,
    error: null,
    session: {
      id: 1, role: rol, managed_areas: [{ id: 3, name: 'Finanzas' }],
      preferences: { refresh_interval: 15 },
      permissions: {
        is_admin: rol === 'administrador', is_area_admin: rol === 'admin_area',
        can_manage_areas: rol !== 'usuario', can_manage_system: rol === 'administrador',
      },
    },
  }),
}));

import { ApiError, api } from '@/lib/api';
import { provisioningApi } from '@/lib/access/provisioning';
import Page from '@/app/admin/jobs/page';
import { FORBIDDEN_MESSAGE } from '@/components/require-role';
import { VACIO_EJECUCIONES } from '@/components/connectors/jobs-log';

const FALLIDA: Job = {
  id: 301, status: 'fallido', operation: 'otorgar', provider: 'conector', access_id: 77,
  user: { id: 8, name: 'Ana Ruiz' }, platform: { id: 12, name: 'Contabilidad' },
  area: { id: 3, name: 'Finanzas' }, attempts_count: 5, max_attempts: 5,
  next_attempt_at: null, created_at: '2026-10-14T15:10:00Z', finished_at: '2026-10-14T15:40:00Z',
};
const pagina = (items: Job[]): Paginated<Job> => ({ items, page: 1, per_page: 25, total: items.length });
const jobs = vi.mocked(provisioningApi.jobs);

beforeEach(() => {
  rol = 'admin_area';
  vi.mocked(api.areas).mockResolvedValue([{ id: 3, name: 'Finanzas' }] as never);
  vi.mocked(api.platforms).mockResolvedValue([]);
  jobs.mockResolvedValue(pagina([FALLIDA]));
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('pantalla Ejecuciones por rol', () => {
  it('usuario: sin permiso y sin llamar a la API', () => {
    rol = 'usuario';
    render(<Page />);
    expect(screen.getByRole('alert').textContent).toBe(FORBIDDEN_MESSAGE);
    expect(jobs).not.toHaveBeenCalled();
  });

  it('admin de área: ve la bitácora de solo lectura (sin Reintentar)', async () => {
    render(<Page />);
    const ul = await screen.findByRole('list', { name: 'Bitácora de ejecuciones' });
    expect(within(ul).getByText('Fallida')).toBeTruthy();
    expect(within(ul).getByRole('button', { name: /Ver el detalle/ })).toBeTruthy();
    expect(screen.queryByRole('button', { name: /Reintentar la ejecución/ })).toBeNull();
    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('Ejecuciones');
  });

  it('superadmin: ve la bitácora con Reintentar en la fallida', async () => {
    rol = 'administrador';
    render(<Page />);
    const ul = await screen.findByRole('list', { name: 'Bitácora de ejecuciones' });
    expect(within(ul).getByRole('button', { name: /Reintentar/ })).toBeTruthy();
  });
});

describe('estados', () => {
  it('carga', () => {
    jobs.mockReturnValue(new Promise(() => {}));
    render(<Page />);
    expect(screen.getByText('Cargando las ejecuciones…')).toBeTruthy();
  });

  it('vacío', async () => {
    jobs.mockResolvedValue(pagina([]));
    render(<Page />);
    expect(await screen.findByText(VACIO_EJECUCIONES)).toBeTruthy();
  });

  it('error sin texto del servidor', async () => {
    jobs.mockRejectedValue(new ApiError(500, 'detalle interno'));
    render(<Page />);
    const alerta = await screen.findByRole('alert');
    expect(alerta.textContent).not.toContain('detalle interno');
  });
});
