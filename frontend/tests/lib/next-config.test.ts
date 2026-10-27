import { afterEach, describe, expect, it, vi } from 'vitest';

async function cargar(env: string, backend?: string) {
  vi.resetModules();
  vi.stubEnv('NODE_ENV', env);
  if (backend !== undefined) vi.stubEnv('BACKEND_URL', backend);
  else vi.stubEnv('BACKEND_URL', '');
  const { default: config } = await import('../../next.config');
  return config.rewrites!();
}

afterEach(() => vi.unstubAllEnvs());

describe('next.config.ts: rewrites hacia el backend (FNC-005, FNC-118)', () => {
  it('en production no hay rewrites', async () => {
    expect(await cargar('production')).toEqual([]);
  });

  it('en development existe /api y no existe /auth', async () => {
    const r = (await cargar('development')) as { source: string; destination: string }[];
    expect(r.map((x) => x.source)).toEqual(['/api/:path*']);
    expect(r[0].destination).toBe('http://localhost:5001/api/:path*');
  });

  it('BACKEND_URL con nombre de host se respeta', async () => {
    const r = (await cargar('development', 'http://api.local:8000/')) as { destination: string }[];
    expect(r[0].destination).toBe('http://api.local:8000/api/:path*');
  });

  it.each([`http://${['10', '0', '0', '5'].join('.')}:5001`, 'http://[::1]:5001', 'ftp://host', 'no-es-url'])(
    'BACKEND_URL inválida o con IP (%s) falla', async (valor) => {
      await expect(cargar('development', valor)).rejects.toThrow(/BACKEND_URL/);
    },
  );
});
