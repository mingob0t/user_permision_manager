/** Ejecuciones de aprovisionamiento (`docs/contratos/conectores-y-ejecuciones.md`). */

import { accessRequest } from './client';
import { MOCK_JOB, MOCK_JOB_DETAIL, page } from './mocks';
import { jsonBody, withQuery } from './query';
import type { Job, JobDetail, JobParams, Paginated } from './types';

export const provisioningApi = {
  jobs: (params: JobParams = {}) =>
    accessRequest<Paginated<Job>>(
      withQuery('/provisioning/jobs', { ...params }), undefined, () => page([MOCK_JOB])),

  job: (jobId: number) =>
    accessRequest<JobDetail>(
      `/provisioning/jobs/${jobId}`, undefined, () => ({ ...MOCK_JOB_DETAIL, id: jobId })),

  /** Solo superadmin (P10) y solo desde `fallido`. */
  retry: (jobId: number) =>
    accessRequest<{ status: 'success'; job: JobDetail }>(
      `/provisioning/jobs/${jobId}/retry`, jsonBody('POST'),
      () => ({ status: 'success', job: { ...MOCK_JOB_DETAIL, id: jobId, status: 'pendiente' } })),
};
