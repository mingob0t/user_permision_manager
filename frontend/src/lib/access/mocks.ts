/**
 * Datos simulados copiados de la sección "Datos simulados" de cada contrato
 * (`docs/contratos/`). PENDIENTE DE INTEGRACIÓN: solo se usan con
 * `NEXT_PUBLIC_ACCESS_MOCKS=1` fuera de producción (`client.ts`) y se retiran
 * cuando el backend de cada sección esté integrado.
 */

import type { ManagedUser } from '../types';
import type {
  Access, AccessRequest, AuditEntryV1, CatalogItem, Connector, DirectoryConfig,
  HomeSummary, Job, JobDetail, Paginated,
} from './types';

export function page<T>(items: T[]): Paginated<T> {
  return { items, page: 1, per_page: 25, total: items.length };
}

export const MOCK_CATALOG: CatalogItem[] = [
  {
    platform: { id: 12, name: 'Contabilidad', description: 'ERP contable', icon: 'box' },
    area: { id: 3, name: 'Finanzas' },
    my_level: 'usuario', my_access_status: 'activo', pending_request_id: null,
    can_request: true, requestable_levels: ['admin'],
  },
];

export const MOCK_REQUEST: AccessRequest = {
  id: 41, status: 'rechazada', level: 'usuario', justification: 'Consulta de pólizas',
  requester: { id: 8, name: 'Ana Ruiz', email: 'ana@ejemplo.local' },
  platform: { id: 12, name: 'Contabilidad' }, area: { id: 3, name: 'Finanzas' },
  current_level: null, created_at: '2026-10-13T10:00:00Z', decided_at: '2026-10-13T12:30:00Z',
  decided_by: { id: 2, name: 'Luis Paz' },
  rejection_reason: 'Usa el reporte compartido del área.', access: null,
};

export const MOCK_ACCESS: Access = {
  id: 78, status: 'en_proceso', level: 'admin', origin: 'admin_de_area',
  user: { id: 2, name: 'Luis Paz', email: 'luis@ejemplo.local' },
  platform: { id: 12, name: 'Contabilidad', integration_type: 'conector' },
  area: { id: 3, name: 'Finanzas' }, request_id: null, granted_by: null,
  granted_at: '2026-10-14T15:00:00Z', revoked_by: null, revoked_at: null,
  revoke_reason: null, last_job_id: 300,
};

export const MOCK_AUDIT: AuditEntryV1 = {
  id: 9000, time: '2026-10-14T15:00:00Z', user: 'luis@ejemplo.local',
  action: 'plataforma_creada', module: 'plataformas', target: 'Contabilidad',
  detail: 'Alta de plataforma', ip: null, status: 'success',
  actor: { id: 2, email: 'luis@ejemplo.local' }, area: { id: 3, name: 'Finanzas' },
  platform: { id: 12, name: 'Contabilidad' }, target_user: null, before: null,
  after: { name: 'Contabilidad', integration_type: 'ldap' },
};

export const MOCK_CONNECTOR: Connector = {
  platform_id: 12, type: 'api', host: 'erp.ejemplo.local', port: 443,
  params: { base_path: '/usuarios' }, credential_ref: 'pokemon/contabilidad-api',
  credential_status: 'ok', active: true, updated_at: '2026-10-14T14:00:00Z',
};

export const MOCK_JOB: Job = {
  id: 302, status: 'reintentando', operation: 'revocar', provider: 'ldap', access_id: 70,
  user: { id: 9, name: 'Eva Mora' }, platform: { id: 5, name: 'Wiki' }, area: { id: 1, name: 'TI' },
  attempts_count: 2, max_attempts: 5, next_attempt_at: '2026-10-14T16:02:00Z',
  created_at: '2026-10-14T16:00:00Z', finished_at: null,
};

export const MOCK_JOB_DETAIL: JobDetail = {
  id: 301, status: 'fallido', operation: 'otorgar', provider: 'conector', access_id: 77,
  user: { id: 8, name: 'Ana Ruiz' }, platform: { id: 12, name: 'Contabilidad' },
  area: { id: 3, name: 'Finanzas' }, attempts_count: 5, max_attempts: 5,
  next_attempt_at: null, created_at: '2026-10-14T15:10:00Z', finished_at: '2026-10-14T15:40:00Z',
  attempts: [{
    n: 5, started_at: '2026-10-14T15:39:58Z', finished_at: '2026-10-14T15:40:00Z',
    result: 'error_transitorio', error: 'Tiempo de espera agotado.',
  }],
};

export const MOCK_USER: ManagedUser = {
  id: 31, email: 'ana@ejemplo.local', name: 'Ana Ruiz', role: 'usuario', is_active: true,
  auth_source: 'ldap', areas: [{ id: 3, name: 'Finanzas' }], managed_areas: [],
  last_login_at: null,
};

export const MOCK_DIRECTORY_CONFIG: DirectoryConfig = {
  active: false, source: 'env', editable: false, config: null,
  origins: {}, variables: {}, error: null,
};

export const MOCK_HOME: HomeSummary = {
  scope: 'areas', my_access: { activo: 2, en_proceso: 0, fallido: 0 },
  my_requests: { pendiente: 1, aprobada: 3, rechazada: 0 },
  pending_approvals: 4, failed_access: 1, oldest_pending_at: '2026-10-13T09:00:00Z',
  totals: { areas: 2, platforms: 7, active_access: 35 },
};

