/**
 * Cliente de la API (`src/lib/api.ts`) con `fetch` simulado (FNC-025).
 * En jsdom existe `window`, así que las rutas son relativas (`/api/v1/...`).
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { api, ApiError } from '@/lib/api';

const fetchSimulado = vi.fn<typeof fetch>();

function respuesta(status: number, cuerpo: unknown): Response {
  return new Response(JSON.stringify(cuerpo), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

beforeEach(() => {
  fetchSimulado.mockReset();
  vi.stubGlobal('fetch', fetchSimulado);
});

describe('api: éxito', () => {
  it('pide /api/v1/areas con la cookie de sesión y devuelve el JSON', async () => {
    const areas = [{ id: 1, name: 'Ventas' }];
    fetchSimulado.mockResolvedValue(respuesta(200, areas));

    await expect(api.areas()).resolves.toEqual(areas);

    const [url, init] = fetchSimulado.mock.calls[0];
    expect(url).toBe('/api/v1/areas');
    expect(init?.credentials).toBe('include');
    expect(init?.redirect).toBe('manual');
    expect(init?.headers).toMatchObject({ Accept: 'application/json' });
  });

  it('agrega Content-Type JSON cuando hay cuerpo', async () => {
    fetchSimulado.mockResolvedValue(respuesta(200, { id: 7 }));

    await api.createArea({ name: 'Nueva' });

    const [, init] = fetchSimulado.mock.calls[0];
    expect(init?.method).toBe('POST');
    expect(init?.headers).toMatchObject({ 'Content-Type': 'application/json' });
  });
});

describe('api: errores', () => {
  it('error HTTP: lanza ApiError con el estado y el mensaje del backend', async () => {
    fetchSimulado.mockResolvedValue(respuesta(403, { message: 'Sin permiso' }));

    const error = await api.users().catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 403, message: 'Sin permiso' });
    expect((error as ApiError).isForbidden).toBe(true);
  });

  it('error HTTP sin cuerpo JSON: mensaje genérico con el código', async () => {
    fetchSimulado.mockResolvedValue(new Response('fallo', { status: 500 }));

    await expect(api.stats()).rejects.toMatchObject({ status: 500, message: 'Error 500' });
  });

  it('401: lanza ApiError marcado como no autenticado', async () => {
    fetchSimulado.mockResolvedValue(respuesta(401, { error: 'No autenticado' }));

    const error = (await api.session().catch((e: unknown) => e)) as ApiError;

    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(401);
    expect(error.isUnauthenticated).toBe(true);
    expect(error.message).toBe('No autenticado');
  });

  it('redirección opaca al login (status 0): se trata como 401', async () => {
    const opaca = { status: 0, type: 'opaqueredirect', ok: false } as Response;
    fetchSimulado.mockResolvedValue(opaca);

    await expect(api.session()).rejects.toMatchObject({ status: 401, isUnauthenticated: true });
  });
});
