/** Solicitudes de acceso (`docs/contratos/solicitudes.md`). */

import { accessRequest } from './client';
import { MOCK_CATALOG, MOCK_INBOX_STATS, MOCK_REQUEST, page } from './mocks';
import { jsonBody, withQuery } from './query';
import type {
  AccessRequest, AccessRequestInput, CatalogItem, CatalogParams, InboxStats, Paginated,
  InboxListParams,
  RequestListParams,
} from './types';

type RequestResult = { status: 'success'; request: AccessRequest };

export const requestsApi = {
  /** Catálogo del actor (P1): plataformas activas de sus áreas. */
  catalog: (params: CatalogParams = {}) =>
    accessRequest<CatalogItem[]>(
      withQuery('/access-requests/catalog', { ...params }), undefined, () => MOCK_CATALOG),

  create: (input: AccessRequestInput) =>
    accessRequest<RequestResult>(
      '/access-requests', jsonBody('POST', input),
      () => ({ status: 'success', request: { ...MOCK_REQUEST, status: 'pendiente' } })),

  mine: (params: RequestListParams = {}) =>
    accessRequest<Paginated<AccessRequest>>(
      withQuery('/access-requests/mine', { ...params }), undefined, () => page([MOCK_REQUEST])),

  /** Bandeja del admin; por defecto `status=pendiente` (lo aplica el backend). */
  inbox: (params: InboxListParams = {}) =>
    accessRequest<Paginated<AccessRequest>>(
      withQuery('/access-requests/inbox', { ...params }), undefined, () => page([MOCK_REQUEST])),

  /** Resumen de la bandeja para la pantalla Solicitudes (todos los estados, mismo alcance que `inbox`). */
  inboxStats: () =>
    accessRequest<InboxStats>('/access-requests/inbox/stats', undefined, () => MOCK_INBOX_STATS),

  approve: (id: number) =>
    accessRequest<RequestResult>(
      `/access-requests/${id}/approve`, jsonBody('POST'),
      () => ({ status: 'success', request: { ...MOCK_REQUEST, id, status: 'aprobada' } })),

  /** `reason`: 10–500 caracteres. */
  reject: (id: number, reason: string) =>
    accessRequest<RequestResult>(
      `/access-requests/${id}/reject`, jsonBody('POST', { reason }),
      () => ({ status: 'success', request: { ...MOCK_REQUEST, id, rejection_reason: reason } })),
};
