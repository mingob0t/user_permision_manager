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

/**
 * Error al cargar una lista propia (DIS-014: `GET /access-requests/mine`,
 * `GET /me/access`). `nombre` va tras el verbo: "tus solicitudes".
 */
export function describeListError(err: unknown, nombre: string): string {
  if (err instanceof ApiError) {
    if (err.isForbidden) return `No tienes permiso para ver ${nombre}.`;
    if (err.isUnauthenticated) return MENSAJES_POR_ESTADO[401];
  }
  return `No se pudieron cargar ${nombre}.`;
}

/**
 * El mismo error con el mensaje de `describeListError`. Conserva el estado
 * HTTP para que `usePolling` se detenga con un `401`.
 */
export function listLoadError(err: unknown, nombre: string): Error {
  const message = describeListError(err, nombre);
  return err instanceof ApiError
    ? new ApiError(err.status, message, { code: err.code ?? undefined })
    : new Error(message);
}

/**
 * Motivo obligatorio del rechazo (DIS-015, RF-06; contrato 1.1;
 * `ACCESS_REQUEST_REJECTION_MIN_LENGTH` / `_MAX_LENGTH`). El servidor lo recorta.
 */
export const MOTIVO_MIN = 10;
export const MOTIVO_MAX = 500;

export const MENSAJE_MOTIVO = `Escribe entre ${MOTIVO_MIN} y ${MOTIVO_MAX} caracteres.`;

/** Errores de aprobar o rechazar, desde la vista del administrador (DIS-015). */
export const MENSAJES_DECISION: Record<string, string> = {
  solicitud_propia: 'No puedes decidir tu propia solicitud.',
  solicitud_ya_decidida: 'Esta solicitud ya fue decidida. La lista se actualizó.',
  plataforma_no_disponible:
    'La plataforma está inactiva o sin integración configurada: no se puede aprobar. Puedes rechazarla.',
  nivel_vigente: 'El solicitante ya tiene ese nivel o uno superior.',
  estado_invalido:
    'El acceso actual del solicitante todavía no está activo. Inténtalo cuando termine de aplicarse.',
  cuenta_inactiva: 'La cuenta del solicitante está inactiva: no se puede aprobar.',
  validacion: 'Revisa el motivo del rechazo.',
};

const MENSAJES_DECISION_POR_ESTADO: Record<number, string> = {
  401: MENSAJES_POR_ESTADO[401],
  403: 'No tienes permiso para decidir esta solicitud.',
  404: 'La solicitud ya no está en tu bandeja. La lista se actualizó.',
};

const MENSAJE_DECISION_GENERICO = 'No se pudo guardar la decisión. Inténtalo de nuevo.';

/** Códigos tras los que la lista ya no refleja la solicitud: se recarga. */
const DECISION_DESACTUALIZADA = new Set(['solicitud_ya_decidida']);

export interface DecisionErrorView extends RequestErrorView {
  /** La solicitud cambió o ya no es visible: recargar la bandeja. */
  stale: boolean;
}

export function describeDecisionError(err: unknown): DecisionErrorView {
  if (!(err instanceof ApiError)) {
    return { message: MENSAJE_DECISION_GENERICO, fields: {}, stale: false };
  }
  const stale = err.status === 404 || DECISION_DESACTUALIZADA.has(err.code ?? '');
  const fields: Record<string, string> = err.fields.reason ? { reason: MENSAJE_MOTIVO } : {};
  const message = (err.code && MENSAJES_DECISION[err.code])
    ?? MENSAJES_DECISION_POR_ESTADO[err.status] ?? MENSAJE_DECISION_GENERICO;
  return { message, fields, stale };
}
