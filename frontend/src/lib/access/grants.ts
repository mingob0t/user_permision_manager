/** Accesos otorgados y revocación (`docs/contratos/accesos.md`). */

import { accessRequest } from './client';
import { MOCK_ACCESS, page } from './mocks';
import { jsonBody, withQuery } from './query';
import type { Access, AccessListParams, Paginated } from './types';

export const grantsApi = {
  /** Mis accesos; por defecto `status=vigente`. */
  mine: (params: AccessListParams = {}) =>
    accessRequest<Paginated<Access>>(
      withQuery('/me/access', { ...params }), undefined, () => page([MOCK_ACCESS])),

  /** Accesos de un usuario (admin: solo plataformas de sus áreas). */
  ofUser: (userId: number, params: AccessListParams = {}) =>
    accessRequest<Paginated<Access>>(
      withQuery(`/users/${userId}/access`, { ...params }), undefined, () => page([MOCK_ACCESS])),

  /** Revoca un acceso `activo`; el motivo es opcional (P7, ≤ 500). */
  revoke: (accessId: number, reason?: string | null) =>
    accessRequest<{ status: 'success'; access: Access }>(
      `/access/${accessId}/revoke`, jsonBody('POST', reason ? { reason } : {}),
      () => ({ status: 'success', access: { ...MOCK_ACCESS, id: accessId, status: 'revocando' } })),
};
