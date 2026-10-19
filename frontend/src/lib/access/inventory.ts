/** Inventario de permisos (`GET /access/inventory`, `docs/contratos/accesos.md`). */

import { accessRequest } from './client';
import { MOCK_ACCESS, page } from './mocks';
import { withQuery } from './query';
import type { Access, InventoryParams, Paginated } from './types';

export const inventoryApi = {
  list: (params: InventoryParams = {}) =>
    accessRequest<Paginated<Access>>(
      withQuery('/access/inventory', { ...params }), undefined, () => page([MOCK_ACCESS])),
};
