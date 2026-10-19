/**
 * Auditoría paginada (`docs/contratos/auditoria.md`). `api.audit(limit)` de
 * `lib/api.ts` sigue siendo la forma compatible sin `page` (arreglo simple).
 */

import { accessRequest } from './client';
import { MOCK_AUDIT, page } from './mocks';
import { withQuery } from './query';
import type { AuditEntryV1, AuditParams, Paginated } from './types';

/** Siempre envía `page` para recibir la forma paginada de `GET /audit`. */
function paged(params: AuditParams) {
  return { ...params, page: params.page ?? 1 };
}

export const auditApi = {
  list: (params: AuditParams = {}) =>
    accessRequest<Paginated<AuditEntryV1>>(
      withQuery('/audit', paged(params)), undefined, () => page([MOCK_AUDIT])),

  ofUser: (userId: number, params: AuditParams = {}) =>
    accessRequest<Paginated<AuditEntryV1>>(
      withQuery(`/audit/users/${userId}`, paged(params)), undefined, () => page([MOCK_AUDIT])),

  ofPlatform: (platformId: number, params: AuditParams = {}) =>
    accessRequest<Paginated<AuditEntryV1>>(
      withQuery(`/audit/platforms/${platformId}`, paged(params)), undefined,
      () => page([MOCK_AUDIT])),
};
