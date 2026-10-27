/**
 * DIS-036: filtros que llegan por la URL.
 * - Los contadores del Inicio enlazan con su filtro (`status`, `tab`).
 * - `/requests`, `/inventory` y `/approvals` leen el filtro al montar; un valor
 *   inválido se ignora y queda el valor por defecto.
 */
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Paginated } from '@/lib/access/types';

const url = vi.hoisted(() => ({ consulta: '' }));
vi.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(url.consulta),
  usePathname: () => '/',
}));
vi.mock('@/lib/access/requests', () => ({ requestsApi: { mine: vi.fn(), inbox: vi.fn() } }));
vi.mock('@/lib/access/grants', () => ({ grantsApi: { mine: vi.fn() } }));
vi.mock('@/lib/access/inventory', () => ({ inventoryApi: { list: vi.fn() } }));
vi.mock('@/lib/api', async (original) => ({
  ...(await original<typeof import('@/lib/api')>()),
  api: { areas: vi.fn(), platforms: vi.fn() },
}));
vi.mock('@/components/session-provider', () => ({
  useSession: () => ({
    loading: false,
    error: null,
    session: {
      id: 2,
      role: 'admin_area',
      managed_areas: [{ id: 3, name: 'Finanzas' }],
      preferences: { refresh_interval: 60 },
      permissions: { is_admin: false, is_area_admin: true, can_manage_areas: false, can_manage_system: false },
    },
  }),
}));

import { api } from '@/lib/api';
import { grantsApi } from '@/lib/access/grants';
import { inventoryApi } from '@/lib/access/inventory';
import { requestsApi } from '@/lib/access/requests';
import { ApprovalsInbox } from '@/components/access/approvals-inbox';
import { rutaConFiltro, valorPermitido } from '@/components/access/filtro-url';
import { Inventory } from '@/components/access/inventory';
import { MyRequestsView } from '@/components/access/my-requests-view';

const VACIA: Paginated<never> = { items: [], page: 1, per_page: 25, total: 0 };

beforeEach(() => {
  vi.clearAllMocks();
  url.consulta = '';
  vi.mocked(requestsApi.mine).mockResolvedValue(VACIA);
  vi.mocked(requestsApi.inbox).mockResolvedValue(VACIA);
  vi.mocked(grantsApi.mine).mockResolvedValue(VACIA);
  vi.mocked(inventoryApi.list).mockResolvedValue(VACIA);
  vi.mocked(api.areas).mockResolvedValue([]);
  vi.mocked(api.platforms).mockResolvedValue([]);
});
afterEach(cleanup);

describe('ayudas de la URL', () => {
  it('valorPermitido acepta solo los de la lista', () => {
    expect(valorPermitido('fallido', ['activo', 'fallido'] as const)).toBe('fallido');
    expect(valorPermitido('otro', ['activo', 'fallido'] as const)).toBeUndefined();
    expect(valorPermitido(null, ['activo'] as const)).toBeUndefined();
  });
  it('rutaConFiltro arma la consulta', () => {
    expect(rutaConFiltro('/requests', { tab: 'accesos', status: 'activo' })).toBe('/requests?tab=accesos&status=activo');
    expect(rutaConFiltro('/requests', {})).toBe('/requests');
  });
});

describe('/requests', () => {
  it('sin parámetros: Mis solicitudes sin filtro', async () => {
    render(<MyRequestsView />);
    await waitFor(() => expect(requestsApi.mine).toHaveBeenCalledWith({ status: undefined, page: 1 }));
    expect(screen.getByRole('tab', { name: 'Mis solicitudes' }).getAttribute('aria-selected')).toBe('true');
  });

  it('status=pendiente filtra Mis solicitudes', async () => {
    url.consulta = 'status=pendiente';
    render(<MyRequestsView />);
    await waitFor(() => expect(requestsApi.mine).toHaveBeenCalledWith({ status: 'pendiente', page: 1 }));
    expect((screen.getByLabelText('Filtrar mis solicitudes por estado') as HTMLSelectElement).value).toBe('pendiente');
  });

  it('tab=accesos&status=fallido abre Mis accesos con ese filtro', async () => {
    url.consulta = 'tab=accesos&status=fallido';
    render(<MyRequestsView />);
    expect(screen.getByRole('tab', { name: 'Mis accesos' }).getAttribute('aria-selected')).toBe('true');
    await waitFor(() => expect(grantsApi.mine).toHaveBeenCalledWith(expect.objectContaining({ status: 'fallido' })));
    expect(requestsApi.mine).not.toHaveBeenCalled();
  });

  it('valores inválidos se ignoran', async () => {
    url.consulta = 'tab=zzz&status=zzz';
    render(<MyRequestsView />);
    await waitFor(() => expect(requestsApi.mine).toHaveBeenCalledWith({ status: undefined, page: 1 }));
  });
});

describe('/inventory', () => {
  it('status=fallido filtra el inventario', async () => {
    url.consulta = 'status=fallido';
    render(<Inventory />);
    await waitFor(() => expect(inventoryApi.list).toHaveBeenCalledWith(expect.objectContaining({ status: 'fallido' })));
  });

  it('sin parámetro o inválido: vigente', async () => {
    url.consulta = 'status=zzz';
    render(<Inventory />);
    await waitFor(() => expect(inventoryApi.list).toHaveBeenCalledWith(expect.objectContaining({ status: 'vigente' })));
  });
});

describe('/approvals', () => {
  it('status=aprobada filtra la bandeja', async () => {
    url.consulta = 'status=aprobada';
    render(<ApprovalsInbox />);
    await waitFor(() => expect(requestsApi.inbox).toHaveBeenCalledWith(expect.objectContaining({ status: 'aprobada' })));
  });

  it('sin parámetro o inválido: pendiente', async () => {
    url.consulta = 'status=zzz';
    render(<ApprovalsInbox />);
    await waitFor(() => expect(requestsApi.inbox).toHaveBeenCalledWith(expect.objectContaining({ status: 'pendiente' })));
  });
});
