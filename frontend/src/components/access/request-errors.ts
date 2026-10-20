/**
 * Mensajes de error de `POST /access-requests` (DIS-013, contrato
 * `solicitudes.md` 1.1, tabla "Errores"). Se elige por `ApiError.code`; los
 * errores sin código propio usan un mensaje fijo por estado, sin detalles del
 * servidor.
 */

import { ApiError } from '@/lib/api';

/** Máximo de la justificación (contrato 1.1; `ACCESS_REQUEST_JUSTIFICATION_MAX_LENGTH`). */
export const JUSTIFICACION_MAX = 500;

export const MENSAJE_JUSTIFICACION_LARGA =
  `Escribe como máximo ${JUSTIFICACION_MAX} caracteres.`;

export const MENSAJES_SOLICITUD: Record<string, string> = {
  solicitud_duplicada: 'Ya tienes una solicitud pendiente para esta plataforma.',
  nivel_vigente: 'Ya tienes ese nivel o uno superior en esta plataforma.',
  estado_invalido:
    'Tu acceso actual todavía no está activo. Podrás pedir otro nivel cuando termine de aplicarse.',
  ya_administra_area: 'Ya administras esta área; tienes acceso automático.',
  plataforma_no_disponible: 'La plataforma está inactiva o sin integración configurada.',
  sin_permiso: 'Tu rol no puede solicitar accesos: el superadmin ya tiene acceso a todas las plataformas.',
  validacion: 'Revisa los campos marcados.',
};

const MENSAJES_POR_ESTADO: Record<number, string> = {
  401: 'Tu sesión terminó. Vuelve a iniciar sesión.',
  403: 'No tienes permiso para solicitar este acceso.',
  404: 'La plataforma ya no está en tu catálogo. Recarga la lista.',
};

const MENSAJE_GENERICO = 'No se pudo enviar la solicitud. Inténtalo de nuevo.';

export interface RequestErrorView {
  message: string;
  /** Errores por campo de un `422 validacion` (`justification`, `level`…). */
  fields: Record<string, string>;
}

export function describeRequestError(err: unknown): RequestErrorView {
  if (!(err instanceof ApiError)) return { message: MENSAJE_GENERICO, fields: {} };
  if (err.code && MENSAJES_SOLICITUD[err.code]) {
    return { message: MENSAJES_SOLICITUD[err.code], fields: err.fields };
  }
  return { message: MENSAJES_POR_ESTADO[err.status] ?? MENSAJE_GENERICO, fields: err.fields };
}

/** Error al cargar el catálogo (`GET /access-requests/catalog`). */
export function describeCatalogError(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.isForbidden) return 'No tienes permiso para ver el catálogo.';
    if (err.isUnauthenticated) return MENSAJES_POR_ESTADO[401];
  }
  return 'No se pudo cargar el catálogo.';
}
