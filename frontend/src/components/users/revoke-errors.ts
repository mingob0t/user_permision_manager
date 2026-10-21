/**
 * Mensajes de error de `POST /access/<id>/revoke` (DIS-018, contrato
 * `accesos.md` 1.1, tabla "Errores"). Se elige por `ApiError.code` o por el
 * estado HTTP; nunca se muestra el texto del servidor.
 */

import { ApiError } from '@/lib/api';

/**
 * Máximo del motivo opcional de la revocación (P7; espejo de `LARGO_MOTIVO`
 * en `app/modules/access/tipos.py`). Sin mínimo; el servidor lo recorta.
 */
export const REVOCACION_MOTIVO_MAX = 500;

export const MENSAJE_MOTIVO_REVOCACION =
  `Escribe como máximo ${REVOCACION_MOTIVO_MAX} caracteres.`;

export const MENSAJES_REVOCACION: Record<string, string> = {
  operacion_propia: 'No puedes revocar tu propio acceso.',
  estado_invalido: 'Solo se revoca un acceso activo. La lista se actualizó.',
  validacion: 'Revisa el motivo de la revocación.',
};

const MENSAJES_REVOCACION_POR_ESTADO: Record<number, string> = {
  401: 'Tu sesión terminó. Vuelve a iniciar sesión.',
  403: 'No tienes permiso para revocar este acceso.',
  // Fuera de alcance, acceso automático del área o de otro admin del área (SEC-AUTHZ-06).
  404: 'Este acceso ya no está en tu alcance. La lista se actualizó.',
};

const MENSAJE_REVOCACION_GENERICO = 'No se pudo revocar el acceso. Inténtalo de nuevo.';

export interface RevokeErrorView {
  message: string;
  /** Errores por campo de un `422 validacion` (solo `reason`). */
  fields: Record<string, string>;
  /** El acceso cambió o ya no es visible: recargar la lista. */
  stale: boolean;
}

export function describeRevokeError(err: unknown): RevokeErrorView {
  if (!(err instanceof ApiError)) {
    return { message: MENSAJE_REVOCACION_GENERICO, fields: {}, stale: false };
  }
  const stale = err.status === 404 || err.code === 'estado_invalido';
  const fields: Record<string, string> =
    err.fields.reason ? { reason: MENSAJE_MOTIVO_REVOCACION } : {};
  const message = (err.code && MENSAJES_REVOCACION[err.code])
    ?? MENSAJES_REVOCACION_POR_ESTADO[err.status] ?? MENSAJE_REVOCACION_GENERICO;
  return { message, fields, stale };
}
