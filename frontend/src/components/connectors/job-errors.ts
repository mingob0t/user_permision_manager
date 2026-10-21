/**
 * Mensajes de error de las ejecuciones (DIS-022, `GET /provisioning/jobs/<id>`
 * y `POST /provisioning/jobs/<id>/retry`, contrato 1.1). Sin texto del servidor.
 */

import { ApiError } from '@/lib/api';

const SESION = 'Tu sesión terminó. Vuelve a iniciar sesión.';

export interface RetryErrorView {
  message: string;
  /** La ejecución cambió o ya no es visible: recargar la lista. */
  stale: boolean;
}

export function describeRetryError(err: unknown): RetryErrorView {
  const generico = 'No se pudo reintentar la ejecución. Inténtalo de nuevo.';
  if (!(err instanceof ApiError)) return { message: generico, stale: false };
  if (err.code === 'estado_invalido') {
    return {
      message: 'Ya no se puede reintentar: solo se reintenta una ejecución fallida y sin cambios posteriores. La lista se actualizó.',
      stale: true,
    };
  }
  if (err.status === 404) return { message: 'La ejecución ya no está en tu alcance. La lista se actualizó.', stale: true };
  if (err.isUnauthenticated) return { message: SESION, stale: false };
  if (err.isForbidden) return { message: 'Solo el superadmin reintenta ejecuciones.', stale: false };
  if (err.status === 400 || err.status === 415) {
    return { message: 'La petición no es válida. Recarga la página e inténtalo de nuevo.', stale: false };
  }
  return { message: generico, stale: false };
}

/** Error al cargar el detalle de una ejecución. */
export function describeJobLoadError(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 404) return 'La ejecución no existe o está fuera de tu alcance.';
    if (err.isForbidden) return 'No tienes permiso para ver esta ejecución.';
    if (err.isUnauthenticated) return SESION;
  }
  return 'No se pudo cargar el detalle de la ejecución.';
}

/** El mismo error con el mensaje propio; conserva el estado HTTP (`usePolling` se detiene con `401`). */
export function jobLoadError(err: unknown): Error {
  const message = describeJobLoadError(err);
  return err instanceof ApiError
    ? new ApiError(err.status, message, { code: err.code ?? undefined })
    : new Error(message);
}
