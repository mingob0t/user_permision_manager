/**
 * Mensajes de los cambios de rol (DIS-019): `PUT /users/<id>` con `role` y
 * `PUT /users/<id>/managed-areas` (contrato `areas-y-roles.md` 2.1, tabla
 * "Errores"). Se elige por `ApiError.code` o por estado HTTP; nunca se
 * muestra el texto del servidor.
 */

import { ApiError } from '@/lib/api';

export const MENSAJE_SIN_AREAS = 'Elige al menos un área.';

const MENSAJES_POR_CODIGO: Record<string, string> = {
  operacion_propia: 'No puedes cambiar tu propio rol.',
  rol_reservado: 'Ese rol no se puede asignar.',
  rol_no_admin: 'La cuenta ya no es administradora de área. La lista se actualizó.',
  validacion: 'Alguna de las áreas ya no existe. La lista se actualizó.',
  campo_no_permitido: 'No se pudo guardar el cambio. Inténtalo de nuevo.',
};

const MENSAJES_POR_ESTADO: Record<number, string> = {
  401: 'Tu sesión terminó. Vuelve a iniciar sesión.',
  403: 'Solo el superadmin cambia roles y áreas administradas.',
  404: 'La cuenta ya no está en tu alcance. La lista se actualizó.',
};

const MENSAJE_GENERICO = 'No se pudo guardar el cambio. Inténtalo de nuevo.';

export interface RoleErrorView {
  message: string;
  /** La cuenta cambió o ya no es visible: recargar la lista. */
  stale: boolean;
}

export function describeRoleError(err: unknown): RoleErrorView {
  if (!(err instanceof ApiError)) return { message: MENSAJE_GENERICO, stale: false };
  const stale = err.status === 404 || err.status === 422 || err.code === 'rol_no_admin';
  const message = (err.code && MENSAJES_POR_CODIGO[err.code])
    ?? MENSAJES_POR_ESTADO[err.status] ?? MENSAJE_GENERICO;
  return { message, stale };
}
