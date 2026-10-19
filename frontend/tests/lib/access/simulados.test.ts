/**
 * Datos simulados del contrato (FNC-069): solo con `NEXT_PUBLIC_ACCESS_MOCKS=1`
 * y nunca en producción.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { mocksEnabled } from '@/lib/access/client';
import { homeApi } from '@/lib/access/home';
import { requestsApi } from '@/lib/access/requests';
import { MOCK_HOME } from '@/lib/access/mocks';

const fetchSimulado = vi.fn<typeof fetch>();

beforeEach(() => {
  fetchSimulado.mockReset();
  fetchSimulado.mockImplementation(async () => new Response('{"scope":"global"}', { status: 200 }));
  vi.stubGlobal('fetch', fetchSimulado);
  vi.unstubAllEnvs();
});

describe('datos simulados', () => {
  it('sin bandera: llama al backend', async () => {
    await expect(homeApi.summary()).resolves.toEqual({ scope: 'global' });
    expect(fetchSimulado).toHaveBeenCalledOnce();
  });

  it('con bandera en desarrollo: devuelve el simulado del contrato sin red', async () => {
    vi.stubEnv('NODE_ENV', 'development');
    vi.stubEnv('NEXT_PUBLIC_ACCESS_MOCKS', '1');

    await expect(homeApi.summary()).resolves.toEqual(MOCK_HOME);
    const bandeja = await requestsApi.inbox();
    expect(bandeja).toMatchObject({ page: 1, per_page: 25, total: 1 });
    expect(fetchSimulado).not.toHaveBeenCalled();
  });

  it('con bandera en producción: se ignora', async () => {
    vi.stubEnv('NODE_ENV', 'production');
    vi.stubEnv('NEXT_PUBLIC_ACCESS_MOCKS', '1');

    expect(mocksEnabled()).toBe(false);
    await homeApi.summary();
    expect(fetchSimulado).toHaveBeenCalledOnce();
  });

  it('otro valor de la bandera no activa los simulados', () => {
    vi.stubEnv('NODE_ENV', 'development');
    vi.stubEnv('NEXT_PUBLIC_ACCESS_MOCKS', 'true');

    expect(mocksEnabled()).toBe(false);
  });
});
