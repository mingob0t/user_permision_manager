/**
 * Petición del gestor de accesos: reutiliza `apiRequest` de `lib/api.ts` y,
 * solo en desarrollo con `NEXT_PUBLIC_ACCESS_MOCKS=1`, devuelve los datos
 * simulados del contrato para avanzar pantallas sin backend.
 */

import { apiRequest } from '../api';

/** Valor de `NEXT_PUBLIC_ACCESS_MOCKS` que activa los datos simulados. */
const MOCKS_ACTIVOS = '1';

/** Datos simulados activos: nunca en un build de producción. */
export function mocksEnabled(): boolean {
  return process.env.NODE_ENV !== 'production'
    && process.env.NEXT_PUBLIC_ACCESS_MOCKS === MOCKS_ACTIVOS;
}

export function accessRequest<T>(
  path: string,
  init: RequestInit | undefined,
  mock: () => T,
): Promise<T> {
  if (mocksEnabled()) return Promise.resolve(mock());
  return apiRequest<T>(path, init);
}
