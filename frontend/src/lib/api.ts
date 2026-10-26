/**
 * Cliente de la API v1.
 *
 * La sesión vive en la cookie que emite Flask, así que toda petición va con
 * `credentials: 'include'`. Nada de tokens en localStorage: el navegador no
 * puede leer la cookie y así el SSO de Authelia sigue siendo la autoridad.
 */

import type {
  Area, AreaInput, AppNotification, AuditEntry, AuthContext,
  EmailTemplate,
  DirectoryUser, InactiveUser, ManagedUser, Platform, PlatformInput, PlatformWarning,
  Session, SmtpConfig, Stats,
  SystemSettings, UserInput,
} from './types';

/** Backend local de desarrollo; por nombre de host, sin IP (FNC-069, absorbe
 *  FNC-005 parcial). En staging y prod se fija `BACKEND_URL`. */
const BACKEND_URL_POR_DEFECTO = 'http://localhost:5001';

/** En el servidor hay que hablar con Flask directamente; en el navegador basta
 *  la ruta relativa, que Nginx (o el rewrite de dev) reenvía. */
const BASE = typeof window === 'undefined'
  ? (process.env.BACKEND_URL ?? BACKEND_URL_POR_DEFECTO)
  : '';

/** Detalle opcional del error estándar (`docs/contratos/README.md`). */
export interface ApiErrorDetails {
  /** Código interno del contrato (`area_duplicada`, `validacion`…). */
  code?: string;
  /** Mensaje por campo de un `422 validacion`. */
  fields?: Record<string, string>;
  /** Identificador de un `500` para cruzar con el log. */
  correlationId?: string;
}

export class ApiError extends Error {
  readonly code: string | null;
  readonly fields: Record<string, string>;
  readonly correlationId: string | null;

  constructor(readonly status: number, message: string, details: ApiErrorDetails = {}) {
    super(message);
    this.name = 'ApiError';
    this.code = details.code ?? null;
    this.fields = details.fields ?? {};
    this.correlationId = details.correlationId ?? null;
  }

  /** El usuario está autenticado pero no tiene permiso. */
  get isForbidden() {
    return this.status === 403;
  }

  /** No hay sesión: Flask redirige al login. */
  get isUnauthenticated() {
    return this.status === 401 || this.status === 302;
  }
}

/** Aplana `fields` anidados (`fields.params.<campo>`) a claves con punto. */
function flattenFields(fields: Record<string, unknown>, prefix = ''): Record<string, string> {
  const flat: Record<string, string> = {};
  for (const [key, value] of Object.entries(fields)) {
    const name = prefix ? `${prefix}.${key}` : key;
    if (typeof value === 'string') flat[name] = value;
    else if (value && typeof value === 'object' && !Array.isArray(value)) {
      Object.assign(flat, flattenFields(value as Record<string, unknown>, name));
    }
  }
  return flat;
}

/** Lee `code`, `fields` y `correlation_id` del cuerpo de error, si vienen. */
function errorDetails(body: unknown): ApiErrorDetails {
  if (!body || typeof body !== 'object') return {};
  const { code, fields, correlation_id: correlationId } = body as Record<string, unknown>;
  const details: ApiErrorDetails = {};
  if (typeof code === 'string') details.code = code;
  if (fields && typeof fields === 'object' && !Array.isArray(fields)) {
    details.fields = flattenFields(fields as Record<string, unknown>);
  }
  if (typeof correlationId === 'string') details.correlationId = correlationId;
  return details;
}

/**
 * Petición a `/api/v1` con la sesión de Flask. Exportada como `apiRequest`
 * para que los clientes por sección (`lib/access/`) la reutilicen (FNC-069).
 */
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}/api/v1${path}`, {
    ...init,
    credentials: 'include',
    redirect: 'manual',
    headers: {
      Accept: 'application/json',
      ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      ...init?.headers,
    },
  });

  // Flask responde 302 al login cuando no hay sesión; `redirect: 'manual'`
  // lo deja como opaco (status 0) en el navegador.
  if (response.status === 0 || response.type === 'opaqueredirect') {
    throw new ApiError(401, 'Sesión no válida.');
  }

  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);
    const parsed = (body ?? {}) as { message?: unknown; error?: unknown };
    const message = parsed.message ?? parsed.error;
    throw new ApiError(
      response.status,
      typeof message === 'string' && message ? message : `Error ${response.status}`,
      errorDetails(body),
    );
  }

  return response.json() as Promise<T>;
}

export { request as apiRequest };

export const api = {
  session: () => request<Session>('/me'),
  areas: () => request<Area[]>('/areas'),
  stats: () => request<Stats>('/stats'),
  users: () => request<ManagedUser[]>('/users'),
  audit: (limit = 100) => request<AuditEntry[]>(`/audit?limit=${limit}`),
  favorites: () => request<Platform[]>('/favorites'),

  platforms: (params: { areaId?: number; q?: string } = {}) => {
    const query = new URLSearchParams();
    if (params.areaId) query.set('area_id', String(params.areaId));
    if (params.q) query.set('q', params.q);
    const suffix = query.toString();
    return request<Platform[]>(`/platforms${suffix ? `?${suffix}` : ''}`);
  },

  toggleFavorite: (platformId: number) =>
    request<{ status: string; is_favorite: boolean }>(
      `/platforms/${platformId}/favorite`, { method: 'POST' },
    ),

  registerVisit: (platformId: number) =>
    request<{ status: string; visits: number }>(
      `/platforms/${platformId}/visit`, { method: 'POST' },
    ),

  setUserAreas: (userId: number, areaIds: number[]) =>
    request<{ status: string; areas: Area[] }>(
      `/users/${userId}/areas`,
      { method: 'PUT', body: JSON.stringify({ area_ids: areaIds }) },
    ),

  // --- Áreas ---
  createArea: (input: AreaInput) =>
    request<{ status: string; area: Area }>(
      '/areas', { method: 'POST', body: JSON.stringify(input) }),
  updateArea: (id: number, input: AreaInput) =>
    request<{ status: string; area: Area }>(
      `/areas/${id}`, { method: 'PUT', body: JSON.stringify(input) }),
  deleteArea: (id: number) =>
    request<{ status: string }>(`/areas/${id}`, { method: 'DELETE' }),
  setAreaUsers: (id: number, userIds: number[]) =>
    request<{ status: string }>(`/areas/${id}/users`,
      { method: 'PUT', body: JSON.stringify({ user_ids: userIds }) }),

  // --- Plataformas ---
  createPlatform: (input: PlatformInput) =>
    request<{ status: string; platform: Platform; warnings?: PlatformWarning[] }>(
      '/platforms', { method: 'POST', body: JSON.stringify(input) }),
  updatePlatform: (id: number, input: PlatformInput) =>
    request<{ status: string; platform: Platform; warnings?: PlatformWarning[] }>(
      `/platforms/${id}`, { method: 'PUT', body: JSON.stringify(input) }),
  deletePlatform: (id: number) =>
    request<{ status: string }>(`/platforms/${id}`, { method: 'DELETE' }),
  setPlatformUsers: (id: number, userIds: number[]) =>
    request<{ status: string }>(`/platforms/${id}/users`,
      { method: 'PUT', body: JSON.stringify({ user_ids: userIds }) }),

  // --- Usuarios ---
  createUser: (input: UserInput) =>
    request<{ status: string; id: number }>(
      '/users', { method: 'POST', body: JSON.stringify(input) }),
  updateUser: (id: number, input: UserInput) =>
    request<{ status: string }>(
      `/users/${id}`, { method: 'PUT', body: JSON.stringify(input) }),
  deleteUser: (id: number) =>
    request<{ status: string }>(`/users/${id}`, { method: 'DELETE' }),
  setUserPlatforms: (id: number, platformIds: number[]) =>
    request<{ status: string }>(`/users/${id}/platforms`,
      { method: 'PUT', body: JSON.stringify({ platform_ids: platformIds }) }),

  // --- Higiene de cuentas ---
  inactiveUsers: (days = 30) =>
    request<{ days: number; count: number; users: InactiveUser[] }>(
      `/users/inactive?days=${days}`),
  purgeInactiveUsers: (days: number) =>
    request<{ status: string; count: number; purged: string[] }>(
      '/users/purge', { method: 'POST', body: JSON.stringify({ days }) }),

  // --- Directorio ---
  searchDirectory: (q: string) =>
    request<{ count: number; users: DirectoryUser[] }>(
      `/directory/search?q=${encodeURIComponent(q)}`),

  // --- Preferencias ---
  savePreferences: (prefs: Partial<Session['preferences']>) =>
    request<{ status: string; preferences: Session['preferences'] }>(
      '/me/preferences', { method: 'PUT', body: JSON.stringify(prefs) }),

  // --- Configuración del sistema ---
  settings: () => request<SystemSettings>('/settings'),
  saveSettings: (input: Partial<SystemSettings>) =>
    request<{ status: string; settings: SystemSettings }>(
      '/settings', { method: 'PUT', body: JSON.stringify(input) }),

  smtp: () => request<SmtpConfig>('/smtp'),
  saveSmtp: (input: Partial<SmtpConfig> & { password?: string }) =>
    request<{ status: string; smtp: SmtpConfig }>(
      '/smtp', { method: 'PUT', body: JSON.stringify(input) }),
  testSmtp: (email: string) =>
    request<{ status: string; message?: string }>(
      '/smtp/test', { method: 'POST', body: JSON.stringify({ email }) }),

  templates: () => request<EmailTemplate[]>('/templates'),
  saveTemplate: (slug: string, input: Partial<EmailTemplate>) =>
    request<{ status: string; template: EmailTemplate }>(
      `/templates/${slug}`, { method: 'PUT', body: JSON.stringify(input) }),

  notifications: () => request<AppNotification[]>('/notifications'),
  markNotificationsRead: (ids?: number[]) =>
    request<{ status: string }>('/notifications/read',
      { method: 'POST', body: JSON.stringify(ids ? { ids } : {}) }),
  clearNotifications: () =>
    request<{ status: string }>('/notifications', { method: 'DELETE' }),

  // --- Autenticación ---
  authContext: () => request<AuthContext>('/auth/context'),
  ssoLogin: () =>
    request<{ status: string; role: string }>('/auth/sso', { method: 'POST' }),
  login: (email: string, password: string, method: 'directory' | 'local') =>
    request<{ status: string; role: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password, method }),
    }),
  logout: () =>
    request<{ status: string; redirect: string | null }>(
      '/auth/logout', { method: 'POST' }),

  /** Descarga el respaldo. Devuelve el Blob para que el navegador lo guarde. */
  downloadBackup: async () => {
    const response = await fetch(`${BASE}/api/v1/backup`, {
      credentials: 'include',
      headers: { Accept: 'application/zip' },
    });
    if (!response.ok) throw new ApiError(response.status, 'No se pudo generar el respaldo');
    return response.blob();
  },

  /** Restaura desde un ZIP exportado. */
  uploadBackup: async (file: File) => {
    const body = new FormData();
    body.append('file', file);
    // Sin Content-Type: el navegador añade el boundary del multipart.
    const response = await fetch(`${BASE}/api/v1/backup`, {
      method: 'POST', credentials: 'include', body,
    });
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      throw new ApiError(response.status, data?.message ?? 'No se pudo restaurar');
    }
    return data as { status: string; restored: string[] };
  },
};
