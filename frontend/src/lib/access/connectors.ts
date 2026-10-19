/** Conector de una plataforma, solo superadmin (`docs/contratos/conectores-y-ejecuciones.md`). */

import { accessRequest } from './client';
import { MOCK_CONNECTOR } from './mocks';
import { jsonBody } from './query';
import type { Connector, ConnectorInput, ConnectorTestResult, StatusOk } from './types';

export const connectorsApi = {
  get: (platformId: number) =>
    accessRequest<Connector>(
      `/platforms/${platformId}/connector`, undefined,
      () => ({ ...MOCK_CONNECTOR, platform_id: platformId })),

  /** Crea o reemplaza; `credential_ref` es la referencia, nunca el secreto. */
  save: (platformId: number, input: ConnectorInput) =>
    accessRequest<{ status: 'success'; connector: Connector }>(
      `/platforms/${platformId}/connector`, jsonBody('PUT', input),
      () => ({ status: 'success', connector: { ...MOCK_CONNECTOR, ...input, platform_id: platformId } })),

  remove: (platformId: number) =>
    accessRequest<StatusOk>(
      `/platforms/${platformId}/connector`, { method: 'DELETE' },
      () => ({ status: 'success' })),

  /** Un fallo de conexión llega como `200` con `result: "error"`. */
  test: (platformId: number) =>
    accessRequest<ConnectorTestResult>(
      `/platforms/${platformId}/connector/test`, jsonBody('POST'),
      () => ({ status: 'success', result: 'ok', message: 'Conexión correcta.' })),
};
