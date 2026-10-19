/**
 * Validación previa y cuerpo de `POST/PUT /platforms` (DIS-017, contrato
 * `plataformas-integracion.md`). Sin estado ni interfaz.
 */

import { enlaceSeguro } from '@/lib/enlace-seguro';
import type { Platform, PlatformInput } from '@/lib/types';
import type { IntegrationValue } from './platform-integration-fields';

/** Largos de la lista blanca del contrato (`plataformas-integracion.md`). */
export const NOMBRE_MIN = 2;
export const NOMBRE_MAX = 100;
export const DESCRIPCION_MAX = 1000;
export const URL_MAX = 255;

/** Validación previa al envío; el backend vuelve a validar todo. */
export function validate(form: PlatformInput, integration: IntegrationValue, isEdit: boolean) {
  const errors: Record<string, string> = {};
  const name = form.name?.trim() ?? '';
  if (name.length < NOMBRE_MIN || name.length > NOMBRE_MAX) {
    errors.name = `El nombre debe tener entre ${NOMBRE_MIN} y ${NOMBRE_MAX} caracteres.`;
  }
  if (!form.description?.trim()) errors.description = 'La descripción es obligatoria.';
  if (!form.area_id) errors.area_id = 'Selecciona un área.';
  const link = form.direct_link?.trim();
  if (link && !enlaceSeguro(link)) errors.direct_link = 'Usa una dirección https://.';
  if (!isEdit && !integration.integration_type) {
    errors.integration_type = 'Selecciona el tipo de integración.';
  }
  const dnUsuario = integration.ldap_group_user_dn.trim().toLowerCase();
  if (dnUsuario && dnUsuario === integration.ldap_group_admin_dn.trim().toLowerCase()) {
    errors.ldap_group_admin_dn = 'Los grupos de usuario y admin deben ser distintos.';
  }
  return errors;
}

/**
 * Cuerpo de `POST/PUT /platforms`. Un admin de área nunca envía DN ni, en la
 * edición, el tipo (`403 dn_solo_superadmin`); un DN vacío o sin cambios no
 * se envía (el backend lo deriva en el alta y lo conserva en la edición).
 */
export function buildPayload(
  form: PlatformInput,
  integration: IntegrationValue,
  initial: IntegrationValue,
  { isEdit, isSuperadmin, currentType }: {
    isEdit: boolean; isSuperadmin: boolean; currentType: Platform['integration_type'] | null;
  },
): PlatformInput {
  const payload: PlatformInput = {
    ...form,
    name: form.name?.trim(),
    description: form.description?.trim(),
    direct_link: form.direct_link?.trim() ?? '',
  };
  const tipo = integration.integration_type || currentType || '';
  if (integration.integration_type && (!isEdit || isSuperadmin)) {
    payload.integration_type = integration.integration_type;
  }
  if (isSuperadmin && tipo === 'ldap') {
    for (const campo of ['ldap_group_user_dn', 'ldap_group_admin_dn'] as const) {
      const dn = integration[campo].trim();
      if (dn && dn !== initial[campo]) payload[campo] = dn;
    }
  }
  return payload;
}
