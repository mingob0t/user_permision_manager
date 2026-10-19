/**
 * Mensajes de error de las escrituras de áreas (`docs/contratos/areas-y-roles.md`,
 * tabla "Errores"). Se elige por `ApiError.code`; si el código no está en la
 * tabla, se usa el mensaje del servidor o el de respaldo.
 */

import { ApiError } from '@/lib/api';

export const MENSAJES_AREAS: Record<string, string> = {
  area_duplicada: 'Ya existe un área con ese nombre.',
  area_con_plataformas: 'El área tiene plataformas; muévelas o elimínalas antes.',
  area_con_accesos: 'El área tiene accesos vigentes.',
  area_con_otros_admins:
    'El área tiene otros administradores; solo el superadmin puede darla de baja.',
  rol_no_admin: 'El usuario no es administrador de área.',
  validacion: 'Revisa los campos marcados.',
};

export function mensajeDeError(err: unknown, respaldo: string): string {
  if (err instanceof ApiError) {
    if (err.code && MENSAJES_AREAS[err.code]) return MENSAJES_AREAS[err.code];
    return err.message || respaldo;
  }
  return err instanceof Error && err.message ? err.message : respaldo;
}

/** Mensajes por campo de un `422 validacion`; vacío en cualquier otro error. */
export function erroresDeCampo(err: unknown): Record<string, string> {
  return err instanceof ApiError ? err.fields : {};
}
