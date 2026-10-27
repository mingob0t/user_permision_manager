/**
 * Mensajes de error de la configuración de conectores (DIS-022, contrato
 * `conectores-y-ejecuciones.md` 1.1, tabla "Errores"). Se elige por
 * `ApiError.code`, por campo o por estado HTTP; nunca se muestra el texto
 * del servidor.
 */

import { ApiError } from '@/lib/api';
import { type CampoConector, MENSAJES_CAMPO } from './connector-catalog';
import { claveDeError, parametrosDe } from './connector-params';

const SESION = 'Tu sesión terminó. Vuelve a iniciar sesión.';
const SIN_PERMISO = 'Solo el superadmin configura conectores.';
export const MENSAJE_REVISA = 'Revisa los campos marcados.';
/** `400 campo_no_permitido` y `415`: la petición no tenía la forma del contrato. */
const PETICION_INVALIDA = 'La petición no es válida. Recarga la página e inténtalo de nuevo.';

export interface ConnectorErrorView {
  message: string;
  fields: Partial<Record<CampoConector, string>>;
  /** Errores de `params.<ruta>` por clave del campo del tipo (DIS-042). */
  paramFields: Record<string, string>;
  /** La plataforma o su configuración cambió: recargar. */
  stale: boolean;
}

function vista(
  message: string, stale = false, fields: ConnectorErrorView['fields'] = {}, paramFields: Record<string, string> = {},
): ConnectorErrorView {
  return { message, fields, paramFields, stale };
}

function porEstado(err: ApiError, generico: string): string {
  if (err.isUnauthenticated) return SESION;
  if (err.isForbidden) return SIN_PERMISO;
  if (err.status === 400 || err.status === 415) return PETICION_INVALIDA;
  return generico;
}

/** Campo del formulario de un `fields` del servidor (`params.<clave>` → `params`). */
function campoDe(clave: string): CampoConector | null {
  const raiz = clave.split('.')[0];
  return raiz in MENSAJES_CAMPO ? (raiz as CampoConector) : null;
}

export const MENSAJES_GUARDAR: Record<string, string> = {
  plataforma_sin_conector: 'La plataforma ya no usa conector. La lista se actualizó.',
  plataforma_con_accesos: 'No puedes cambiar el tipo: hay accesos vigentes con este conector.',
  conector_concurrente: 'Otra persona configuró este conector a la vez. Se recargó la configuración: revisa y vuelve a guardar.',
};

/** Mensaje propio de un campo de parámetros que el servidor rechazó. */
function mensajeParametro(tipo: string, clave: string): string {
  const campo = parametrosDe(tipo).find((c) => c.clave === clave);
  return campo ? `Revisa «${campo.etiqueta}». ${campo.pista}` : MENSAJES_CAMPO.params;
}

export function describeConnectorSaveError(err: unknown, tipo = ''): ConnectorErrorView {
  const generico = 'No se pudo guardar el conector. Inténtalo de nuevo.';
  if (!(err instanceof ApiError)) return vista(generico);
  if (err.code === 'plataforma_con_accesos') {
    return vista(MENSAJES_GUARDAR.plataforma_con_accesos, false,
      { type: 'Con accesos vigentes no se cambia el tipo.' });
  }
  if (err.code && MENSAJES_GUARDAR[err.code]) return vista(MENSAJES_GUARDAR[err.code], true);
  if (err.status === 422) {
    const fields: ConnectorErrorView['fields'] = {};
    const paramFields: Record<string, string> = {};
    for (const clave of Object.keys(err.fields)) {
      const campo = campoDe(clave);
      if (!campo) continue;
      const propio = campo === 'params' && clave.startsWith('params.')
        ? claveDeError(tipo, clave.slice('params.'.length)) : null;
      if (propio) paramFields[propio] = mensajeParametro(tipo, propio);
      else fields[campo] = MENSAJES_CAMPO[campo];
    }
    return vista(MENSAJE_REVISA, false, fields, paramFields);
  }
  if (err.status === 404) return vista('La plataforma ya no existe. La lista se actualizó.', true);
  return vista(porEstado(err, generico));
}

export function describeConnectorDeleteError(err: unknown): ConnectorErrorView {
  const generico = 'No se pudo eliminar el conector. Inténtalo de nuevo.';
  if (!(err instanceof ApiError)) return vista(generico);
  if (err.code === 'plataforma_con_accesos') {
    return vista('No se puede eliminar: hay accesos vigentes con este conector. Revócalos primero.');
  }
  if (err.status === 404) return vista('La configuración ya no existe. Se actualizó.', true);
  return vista(porEstado(err, generico));
}

export function describeConnectorTestError(err: unknown): ConnectorErrorView {
  const generico = 'No se pudo probar la conexión. Inténtalo de nuevo.';
  if (!(err instanceof ApiError)) return vista(generico);
  if (err.status === 404) return vista('La configuración ya no existe. Se actualizó.', true);
  return vista(porEstado(err, generico));
}

/** Error al leer la configuración (el `404` es "sin configurar" y no llega aquí). */
export function describeConnectorLoadError(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.isUnauthenticated) return SESION;
    if (err.isForbidden) return SIN_PERMISO;
  }
  return 'No se pudo cargar la configuración del conector.';
}

/** Resultado de la prueba (`200` con `result`), con texto propio. */
export const PRUEBA_OK = 'Conexión correcta.';
export const PRUEBA_ERROR =
  'No se pudo conectar con la plataforma. Revisa el host, el puerto y la referencia de la credencial; el detalle queda en el registro del servidor.';
