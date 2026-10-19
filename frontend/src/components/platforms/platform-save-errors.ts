/**
 * Traduce el error de `POST/PUT /platforms` a mensaje general y errores por
 * campo (DIS-017, contrato `plataformas-integracion.md`, sección "Errores").
 */

import { ApiError } from '@/lib/api';

/** Campos que el formulario muestra junto a su control. */
export const CAMPOS_DEL_FORMULARIO = [
  'name', 'description', 'area_id', 'direct_link',
  'integration_type', 'ldap_group_user_dn', 'ldap_group_admin_dn',
] as const;

/** Nombre visible de los campos que no tienen control propio en el formulario. */
const ETIQUETAS: Record<string, string> = {
  logo_url: 'Logo',
  icon: 'Icono',
  bg_color: 'Color de fondo',
  text_color: 'Color de texto',
  status: 'Estado',
};

/** Mensajes por `code` del contrato; si llega otro, se usa el del backend. */
const MENSAJES: Record<string, string> = {
  dn_solo_superadmin:
    'Solo el superadmin define los grupos del directorio o cambia el tipo de integración.',
  plataforma_con_accesos:
    'No se puede cambiar el tipo, los grupos ni el área con accesos vigentes.',
  grupos_iguales: 'Los grupos de usuario y admin deben ser distintos.',
  grupo_en_uso: 'El grupo ya pertenece a otra plataforma.',
};

const MENSAJE_404 = 'El área o la plataforma ya no está en tu alcance. Recarga la lista.';
export const MENSAJE_REVISA_CAMPOS = 'Revisa los campos marcados.';
const MENSAJE_GENERICO = 'No se pudo guardar la plataforma.';

export interface SaveErrorView {
  message: string;
  fields: Record<string, string>;
}

export function describeSaveError(err: unknown): SaveErrorView {
  if (!(err instanceof ApiError)) {
    return { message: err instanceof Error ? err.message : MENSAJE_GENERICO, fields: {} };
  }
  if (err.status === 404) return { message: MENSAJE_404, fields: {} };

  if (err.code === 'grupos_iguales') {
    return { message: MENSAJES.grupos_iguales, fields: { ldap_group_admin_dn: MENSAJES.grupos_iguales } };
  }
  if (err.code && MENSAJES[err.code]) return { message: MENSAJES[err.code], fields: {} };

  const propios = CAMPOS_DEL_FORMULARIO as readonly string[];
  const fields: Record<string, string> = {};
  const otros: string[] = [];
  for (const [campo, mensaje] of Object.entries(err.fields)) {
    if (propios.includes(campo)) fields[campo] = mensaje;
    else otros.push(`${ETIQUETAS[campo] ?? campo}: ${mensaje}`);
  }
  if (Object.keys(fields).length > 0 || otros.length > 0) {
    return { message: [MENSAJE_REVISA_CAMPOS, ...otros].join(' '), fields };
  }
  return { message: err.message || MENSAJE_GENERICO, fields: {} };
}
