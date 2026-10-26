/**
 * Textos y formato de la pestaña Directorio de Ajustes (DIS-023; contrato
 * `usuarios-directorio.md`, "Configuración del directorio", FNC-043).
 *
 * Solo lectura: la fuente única son las variables `LDAP_*` del entorno
 * (ADR-004). La contraseña de bind no llega al cliente ni se pide aquí.
 */

import type { DirectoryConfig } from '@/lib/access/types';

type Config = NonNullable<DirectoryConfig['config']>;
type Tono = 'success' | 'error' | 'slate';

/** Estado de la configuración, deducido de `active` y `error`. */
export type EstadoDirectorio = 'activo' | 'sin_configurar' | 'invalido';

export const ESTADOS_DIRECTORIO: Record<EstadoDirectorio, { texto: string; tono: Tono }> = {
  activo: { texto: 'Activo', tono: 'success' },
  sin_configurar: { texto: 'Sin configurar', tono: 'slate' },
  invalido: { texto: 'Configuración inválida', tono: 'error' },
};

export function estadoDirectorio(datos: DirectoryConfig): EstadoDirectorio {
  if (!datos.active) return 'sin_configurar';
  if (datos.error || !datos.config) return 'invalido';
  return 'activo';
}

/** Variable que define `host` y `port` (se deducen de la URL). */
const CAMPO_URL = 'url';

/** Campo mostrado: etiqueta, valor legible y campo de `origins`/`variables`. */
export interface CampoDirectorio {
  id: string;
  etiqueta: string;
  valor: (c: Config) => string;
  /** Campo de `origins` y `variables` del que sale el valor. */
  origen: string;
}

const SIN_DEFINIR = 'Sin definir';
const UNIDAD_SEGUNDOS = 's';

export const CAMPOS_DIRECTORIO: CampoDirectorio[] = [
  { id: 'url', etiqueta: 'URL del servidor', valor: (c) => c.url, origen: CAMPO_URL },
  { id: 'servidor', etiqueta: 'Servidor y puerto', valor: (c) => `${c.host}:${c.port}`, origen: CAMPO_URL },
  {
    id: 'tls', etiqueta: 'Cifrado',
    valor: (c) => (c.tls === 'ldaps' ? 'LDAPS' : 'StartTLS'), origen: CAMPO_URL,
  },
  {
    id: 'ca_cert', etiqueta: 'Certificado de la CA',
    valor: (c) => (c.ca_cert === 'custom' ? 'CA propia' : 'CA del sistema'), origen: 'ca_cert',
  },
  { id: 'bind_dn', etiqueta: 'Cuenta de servicio (DN)', valor: (c) => c.bind_dn, origen: 'bind_dn' },
  { id: 'users_base_dn', etiqueta: 'Base de personas', valor: (c) => c.users_base_dn, origen: 'users_base_dn' },
  { id: 'groups_base_dn', etiqueta: 'Base de grupos', valor: (c) => c.groups_base_dn, origen: 'groups_base_dn' },
  { id: 'user_attr', etiqueta: 'Atributo de usuario', valor: (c) => c.user_attr, origen: 'user_attr' },
  {
    id: 'group_object_class', etiqueta: 'Clase de los grupos',
    valor: (c) => c.group_object_class, origen: 'group_object_class',
  },
  {
    id: 'group_member_attr', etiqueta: 'Atributo de membresía',
    valor: (c) => c.group_member_attr, origen: 'group_member_attr',
  },
  {
    id: 'timeout_seconds', etiqueta: 'Tiempo de espera',
    valor: (c) => `${c.timeout_seconds} ${UNIDAD_SEGUNDOS}`, origen: 'timeout_seconds',
  },
  {
    id: 'user_object_classes', etiqueta: 'Clases de las cuentas nuevas',
    valor: (c) => c.user_object_classes.join(', ') || SIN_DEFINIR, origen: 'user_object_classes',
  },
  {
    id: 'placeholder_member', etiqueta: 'Miembro de relleno',
    valor: (c) => c.placeholder_member || SIN_DEFINIR, origen: 'placeholder_member',
  },
];

/** "LDAP_URL · definida en el entorno" o "· valor por defecto". */
export function textoOrigen(datos: DirectoryConfig, campo: string): string {
  const variable = datos.variables[campo];
  const origen = datos.origins[campo] === 'env' ? 'definida en el entorno' : 'valor por defecto';
  return variable ? `${variable} · ${origen}` : origen;
}

export const AVISO_FUENTE =
  'Esta configuración viene de las variables LDAP_* del entorno del servidor y no se edita desde el portal. Para cambiarla, edita el entorno y reinicia el servicio.';

export const ETIQUETA_CONTRASENA = 'Contraseña de la cuenta de servicio';
export const TEXTO_CONTRASENA =
  'No se muestra ni se pide aquí. En desarrollo viene de LDAP_BIND_PASSWORD (.env); en staging y producción, de Vaultwarden (LDAP_BIND_PASSWORD_REF).';

export const MENSAJE_SIN_CONFIGURAR =
  'El directorio no está configurado. Define LDAP_URL y las demás variables LDAP_* en el entorno del servidor y reinicia el servicio.';
export const MENSAJE_INVALIDA =
  'La configuración del directorio no es válida. Revisa las variables LDAP_* del entorno; el detalle queda en el registro del servidor.';

export const PISTA_PRUEBA = 'Se prueba la conexión de la cuenta de servicio con la configuración vigente.';
export const PISTA_PRUEBA_NO_DISPONIBLE = 'Disponible cuando el directorio esté configurado y sea válido.';
