/**
 * Tipos de los contratos v1 del gestor de accesos (`docs/contratos/`).
 *
 * Los tipos heredados que el contrato extiende (`Platform`, `PlatformInput`,
 * `AuditEntry`, `ManagedUser`, `Area`) siguen en `lib/types.ts`.
 */

import type { AuditEntry, ManagedUser } from '../types';

// --- Comunes (README.md) ---

/** Lista paginada estándar. */
export interface Paginated<T> {
  items: T[];
  page: number;
  per_page: number;
  total: number;
}

/** Parámetros de paginación (`per_page` 1–100, por defecto 25). */
export interface PageParams {
  page?: number;
  per_page?: number;
}

/** Escritura correcta sin recurso en la respuesta. */
export interface StatusOk {
  status: 'success';
}

export interface Ref {
  id: number;
  name: string;
}

export interface UserRef {
  id: number;
  name: string;
  email: string;
}

export interface ActorRef {
  id: number;
  email: string;
}

// --- Solicitudes (solicitudes.md) ---

export type AccessLevel = 'usuario' | 'admin';
export type RequestStatus = 'pendiente' | 'aprobada' | 'rechazada';

export interface CatalogItem {
  platform: { id: number; name: string; description: string; icon: string };
  area: Ref;
  my_level: AccessLevel | null;
  my_access_status: AccessStatus | null;
  pending_request_id: number | null;
  can_request: boolean;
  requestable_levels: AccessLevel[];
}

export interface CatalogParams {
  area_id?: number;
  q?: string;
}

export interface AccessRequest {
  id: number;
  status: RequestStatus;
  level: AccessLevel;
  justification: string;
  requester: UserRef;
  platform: Ref;
  area: Ref;
  current_level: AccessLevel | null;
  created_at: string;
  decided_at: string | null;
  decided_by: Ref | null;
  rejection_reason: string | null;
  access: { id: number; status: AccessStatus } | null;
}

export interface AccessRequestInput {
  platform_id: number;
  level: AccessLevel;
  /** 10–500 caracteres. */
  justification: string;
}

export interface RequestListParams extends PageParams {
  status?: RequestStatus;
  area_id?: number;
  platform_id?: number;
}

// --- Accesos e inventario (accesos.md) ---

export type AccessStatus =
  | 'en_proceso' | 'activo' | 'fallido' | 'revocando' | 'revocado' | 'fallo_revocacion';
export type AccessOrigin = 'solicitud' | 'admin_de_area';

export interface Access {
  id: number;
  status: AccessStatus;
  level: AccessLevel;
  origin: AccessOrigin;
  user: UserRef;
  platform: Ref & { integration_type: 'ldap' | 'conector' };
  area: Ref;
  request_id: number | null;
  /** null = `sistema` (origen `admin_de_area`). */
  granted_by: Ref | null;
  granted_at: string;
  revoked_by: Ref | null;
  revoked_at: string | null;
  revoke_reason: string | null;
  /** Se omite en `/me/access` para el rol usuario. */
  last_job_id?: number | null;
}

export interface AccessListParams extends PageParams {
  /** Por defecto `vigente`. */
  status?: AccessStatus | 'vigente';
}

export interface InventoryParams extends AccessListParams {
  area_id?: number;
  platform_id?: number;
  user_id?: number;
  level?: AccessLevel;
  origin?: AccessOrigin;
  q?: string;
}

// --- Auditoría (auditoria.md) ---

export type AuditResult = 'success' | 'error' | 'warning' | 'info';

/** `AuditEntry` heredado más los campos nuevos del contrato v1. */
export interface AuditEntryV1 extends AuditEntry {
  /** null = sistema. */
  actor: ActorRef | null;
  area: Ref | null;
  platform: Ref | null;
  target_user: ActorRef | null;
  before: Record<string, unknown> | null;
  after: Record<string, unknown> | null;
}

export interface AuditParams extends PageParams {
  action?: string;
  result?: AuditResult;
  area_id?: number;
  platform_id?: number;
  user_id?: number;
  /** Fecha ISO 8601; rango ≤ 366 días. */
  from?: string;
  to?: string;
  q?: string;
}

// --- Conectores y ejecuciones (conectores-y-ejecuciones.md) ---

export type ConnectorType = 'api' | 'ssh' | 'bd';

export interface Connector {
  platform_id: number;
  type: ConnectorType;
  host: string;
  port: number;
  params: Record<string, unknown>;
  /** Referencia del ítem en Vaultwarden; nunca el valor. */
  credential_ref: string;
  credential_status: 'ok' | 'no_encontrada' | 'sin_verificar';
  active: boolean;
  updated_at: string;
}

export interface ConnectorInput {
  type: ConnectorType;
  host: string;
  port: number;
  params: Record<string, unknown>;
  credential_ref: string;
  active?: boolean;
}

export interface ConnectorTestResult {
  status: 'success';
  result: 'ok' | 'error';
  message: string;
}

export type JobStatus = 'pendiente' | 'en_ejecucion' | 'reintentando' | 'exitoso' | 'fallido';
export type JobOperation = 'otorgar' | 'revocar';

export interface JobAttempt {
  n: number;
  started_at: string;
  finished_at: string | null;
  result: 'exitoso' | 'sin_cambios' | 'error_transitorio' | 'error_permanente';
  error: string | null;
}

/** Ejecución en la lista (sin `attempts`). */
export interface Job {
  id: number;
  status: JobStatus;
  operation: JobOperation;
  provider: 'ldap' | 'conector';
  access_id: number;
  user: Ref;
  platform: Ref;
  area: Ref;
  attempts_count: number;
  max_attempts: number;
  next_attempt_at: string | null;
  created_at: string;
  finished_at: string | null;
}

/** Detalle de una ejecución. */
export interface JobDetail extends Job {
  attempts: JobAttempt[];
}

export interface JobParams extends PageParams {
  status?: JobStatus;
  operation?: JobOperation;
  provider?: 'ldap' | 'conector';
  area_id?: number;
  platform_id?: number;
  user_id?: number;
  access_id?: number;
  from?: string;
  to?: string;
}

// --- Usuarios y directorio (areas-y-roles.md, usuarios-directorio.md) ---

export interface DirectoryAccountInput {
  /** 3–64; `^[a-z][a-z0-9._-]*$`. */
  uid: string;
  email: string;
  given_name: string;
  surname: string;
  /** Obligatorio para un admin de área; el superadmin puede enviarlo vacío. */
  area_ids: number[];
}

export interface UserWriteResult {
  status: 'success';
  user: ManagedUser;
}

/** Configuración efectiva del directorio (`GET /auth-config`, FNC-043). */
export interface DirectoryConfig {
  active: boolean;
  source: 'env';
  editable: false;
  config: {
    url: string;
    host: string;
    port: number;
    tls: 'ldaps' | 'starttls';
    ca_cert: 'custom' | 'system';
    bind_dn: string;
    users_base_dn: string;
    groups_base_dn: string;
    user_attr: string;
    group_object_class: string;
    group_member_attr: string;
    timeout_seconds: number;
    user_object_classes: string[];
    placeholder_member: string;
  } | null;
  /** Por campo: `env` o `default`. */
  origins: Record<string, 'env' | 'default'>;
  /** Campo → nombre de la variable `LDAP_*`. */
  variables: Record<string, string>;
  error: 'configuracion_invalida' | null;
}

// --- Inicio (inicio.md) ---

export interface HomeSummary {
  scope: 'propio' | 'areas' | 'global';
  my_access?: { activo: number; en_proceso: number; fallido: number };
  my_requests?: { pendiente: number; aprobada: number; rechazada: number };
  pending_approvals?: number;
  failed_access?: number;
  oldest_pending_at?: string | null;
  totals?: { areas: number; platforms: number; active_access: number };
}
