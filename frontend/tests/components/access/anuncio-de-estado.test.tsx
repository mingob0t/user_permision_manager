/**
 * DIS-050: región `polite` que anuncia solo los cambios de estado entre
 * respuestas en Mis solicitudes y Mis accesos.
 * - Anuncia un cambio; no anuncia sin cambios; no anuncia la carga inicial.
 */
import { act, cleanup, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Access, AccessRequest, Paginated } from '@/lib/access/types';

vi.mock('@/lib/access/requests', () => ({ requestsApi: { mine: vi.fn() } }));
vi.mock('@/lib/access/grants', () => ({ grantsApi: { mine: vi.fn() } }));
vi.mock('@/components/session-provider', () => ({
  useSession: () => ({ session: { preferences: { refresh_interval: 60 } } }),
}));

import { grantsApi } from '@/lib/access/grants';
import { requestsApi } from '@/lib/access/requests';
import { MOCK_ACCESS, MOCK_REQUEST } from '@/lib/access/mocks';
import { MyAccess } from '@/components/access/my-access';
import { MyRequests } from '@/components/access/my-requests';

function pagina<T>(items: T[]): Paginated<T> {
  return { items, page: 1, per_page: 25, total: items.length };
}

const EN_PROCESO: Access = { ...MOCK_ACCESS, id: 5, status: 'en_proceso' };
const SOLICITUD: AccessRequest = {
  ...MOCK_REQUEST, id: 8, status: 'aprobada', access: { id: 5, status: 'en_proceso' },
};

function region() {
  return document.querySelector('[data-region-anuncios]') as HTMLElement;
}

async function avanzar(ms: number) {
  await act(async () => { await vi.advanceTimersByTimeAsync(ms); });
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.useFakeTimers({ shouldAdvanceTime: true });
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

describe('Anuncio de cambios de estado (DIS-050)', () => {
  it('accesos: anuncia el cambio de estado entre dos respuestas', async () => {
    vi.mocked(grantsApi.mine)
      .mockResolvedValueOnce(pagina([EN_PROCESO]))
      .mockResolvedValue(pagina([{ ...EN_PROCESO, status: 'activo' }]));
    render(<MyAccess />);
    await avanzar(0);
    await avanzar(61_000);
    expect(region().textContent).toBe(`Acceso a ${EN_PROCESO.platform.name}: Con acceso`);
    expect(region().getAttribute('aria-live')).toBe('polite');
  });

  it('accesos: un refresco sin cambios no anuncia nada', async () => {
    vi.mocked(grantsApi.mine).mockResolvedValue(pagina([EN_PROCESO]));
    render(<MyAccess />);
    await avanzar(0);
    await avanzar(61_000);
    expect(vi.mocked(grantsApi.mine).mock.calls.length).toBeGreaterThanOrEqual(2);
    expect(region().textContent).toBe('');
  });

  it('accesos: no anuncia en la carga inicial', async () => {
    vi.mocked(grantsApi.mine).mockResolvedValue(pagina([{ ...EN_PROCESO, status: 'activo' }]));
    render(<MyAccess />);
    await avanzar(0);
    expect(grantsApi.mine).toHaveBeenCalledTimes(1);
    expect(screen.getAllByText(/Con acceso/).length).toBeGreaterThan(0);
    expect(region().textContent).toBe('');
  });

  it('solicitudes: anuncia el cambio del acceso derivado y no la carga inicial', async () => {
    vi.mocked(requestsApi.mine)
      .mockResolvedValueOnce(pagina([SOLICITUD]))
      .mockResolvedValue(pagina([{ ...SOLICITUD, access: { id: 5, status: 'activo' } }]));
    render(<MyRequests />);
    await avanzar(0);
    expect(region().textContent).toBe('');
    await avanzar(61_000);
    expect(region().textContent).toBe(`Acceso a ${SOLICITUD.platform.name}: Con acceso`);
  });
});
