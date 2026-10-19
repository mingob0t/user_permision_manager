/** Resumen de inicio por rol (`docs/contratos/inicio.md`). */

import { accessRequest } from './client';
import { MOCK_HOME } from './mocks';
import type { HomeSummary } from './types';

export const homeApi = {
  summary: () => accessRequest<HomeSummary>('/home/summary', undefined, () => MOCK_HOME),
};
