/** Tipos del contrato con la API v1 de Flask (`app/modules/api/routes.py`). */

export type Role = 'administrador' | 'admin_area' | 'usuario';

export interface AreaRef {
  id: number;
  name: string;
}

export interface Session {
  id: number;
  email: string;
  name: string;
  role: Role;
  auth_source: string;
  areas: AreaRef[];
  managed_areas: AreaRef[];
  permissions: {
    is_admin: boolean;
    is_area_admin: boolean;
    can_manage_areas: boolean;
    can_manage_system: boolean;
  };
  preferences: {
    notifications: boolean;
    email_notifications: boolean;
    refresh_interval: number;
    tour_enabled: boolean;
  };
}

export interface Area {
  id: number;
  name: string;
  description: string | null;
  icon: string;
  color: string;
  status: string;
  platforms_count: number;
  users_count: number;
}

export interface Platform {
  id: number;
  name: string;
  description: string;
  area_id: number;
  area_name: string | null;
  area_color: string;
  area_icon: string;
  direct_link: string | null;
  icon: string;
  logo_url: string | null;
  bg_color: string;
  text_color: string;
  status: string;
  visits: number;
  is_favorite: boolean;
  // Campos del contrato v1 (plataformas-integracion.md, FNC-046).
  integration_type: IntegrationType;
  /** Grupo del nivel `usuario`; null solo si `conector`. */
  ldap_group_user_dn: string | null;
  /** Grupo del nivel `admin`; null solo si `conector`. */
  ldap_group_admin_dn: string | null;
  groups_status: 'ok' | 'no_existe' | 'sin_verificar';
  has_connector: boolean;
  /** Accesos vigentes (accesos.md). */
  active_grants: number;
}

/** Cómo se aprovisiona el acceso a una plataforma (contrato v1). */
export type IntegrationType = 'ldap' | 'conector';

/** Aviso no bloqueante de una escritura de plataforma (`warnings`). */
export interface PlatformWarning {
  code: string;
  message: string;
}

export interface ManagedUser {
  id: number;
  email: string;
  name: string;
  role: Role;
  is_active: boolean;
  auth_source: string;
  areas: AreaRef[];
  managed_areas: AreaRef[];
  last_login_at: string | null;
}

export interface Stats {
  areas: number;
  platforms: number;
  visits: number;
  users?: number;
  most_visited: { id: number; name: string; visits: number }[];
  platforms_by_area: { area: string; color: string; count: number }[];
}

export interface AuditEntry {
  id: number;
  time: string;
  user: string;
  action: string;
  module: string | null;
  target: string | null;
  detail: string | null;
  ip: string | null;
  status: string;
}

export interface SystemSettings {
  portal_name: string;
  portal_identity_type: 'icon' | 'image';
  portal_icon: string | null;
  bg_color: string;
  text_color: string;
}

export interface SmtpConfig {
  server: string;
  port: number;
  encryption: string;
  auth_enabled: boolean;
  username: string | null;
  sender_name: string;
  sender_email?: string | null;
  /** De dónde sale la configuración en vigor. */
  source?: 'env' | 'db' | 'none';
  /** SMTP_FORCE_ENV fija los valores desde el entorno del servidor. */
  forced_by_env?: boolean;
  /** false cuando el entorno manda: la interfaz no puede cambiarla. */
  editable?: boolean;
  warning?: string;
}

export interface EmailTemplate {
  slug: string;
  name: string;
  subject: string;
  body: string;
  is_html: boolean;
  updated_at: string | null;
}

export interface AppNotification {
  id: number;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  is_read: boolean;
  time: string;
  timestamp: string;
}

/** Campos editables de un área. */
export interface AreaInput {
  name?: string;
  description?: string | null;
  icon?: string;
  color?: string;
  status?: string;
}

/** Campos editables de una plataforma. */
export interface PlatformInput {
  name?: string;
  description?: string;
  area_id?: number;
  direct_link?: string | null;
  icon?: string;
  logo_url?: string | null;
  bg_color?: string;
  text_color?: string;
  status?: string;
  /** Obligatorio en `POST /platforms`, igual que `name`, `description` y `area_id`. */
  integration_type?: IntegrationType;
  /** Solo superadmin (`403 dn_solo_superadmin` para un admin de área). */
  ldap_group_user_dn?: string;
  /** Solo superadmin. */
  ldap_group_admin_dn?: string;
}

/**
 * Campos editables de un usuario (`POST /users`, `PUT /users/<id>`).
 * Sin `auth_source` ni `managed_area_ids`: el backend responde
 * `400 campo_no_permitido` (FNC-044). Las áreas administradas van por
 * `setManagedAreas` (`lib/access/users.ts`).
 */
export interface UserInput {
  email?: string;
  name?: string;
  role?: Role;
  password?: string;
  is_active?: boolean;
  area_ids?: number[];
}

export interface AuthContext {
  sso_enabled: boolean;
  /** Identidad que ya aporta Authelia, si el proxy la inyectó. */
  sso_user: string | null;
  authenticated: boolean;
  ldap_available: boolean;
}

export interface InactiveUser {
  id: number;
  email: string;
  name: string;
  role: Role;
  last_login_at: string | null;
}

export interface DirectoryUser {
  name: string;
  email: string;
  account: string;
  /** Ya existe una cuenta en Nexus con ese correo. */
  exists: boolean;
}
