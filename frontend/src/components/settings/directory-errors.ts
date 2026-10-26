/**
 * Mensajes de error de la pestaña Directorio (DIS-023; contrato
 * `usuarios-directorio.md`, FNC-043). Se eligen por `ApiError.code` o por
 * estado HTTP; nunca se muestra el texto del servidor (patrón de DIS-022).
 */

import { ApiError } from '@/lib/api';
import { MENSAJE_SIN_CONFIGURAR } from './directory-catalog';

const SESION = 'Tu sesión terminó. Vuelve a iniciar sesión.';
const SIN_PERMISO = 'Solo el superadmin consulta la configuración del directorio.';
/** `400 campo_no_permitido` / `cuerpo_invalido`: la petición no tenía la forma del contrato. */
const PETICION_INVALIDA = 'La petición no es válida. Recarga la página e inténtalo de nuevo.';

export const ERROR_CARGA = 'No se pudo cargar la configuración del directorio.';
export const ERROR_PRUEBA = 'No se pudo probar la conexión. Inténtalo de nuevo.';
export const ERROR_NO_DISPONIBLE =
  'No se pudo conectar con el directorio. Revisa las variables LDAP_* y la contraseña de la cuenta de servicio; el detalle queda en el registro del servidor.';

/** Texto propio del éxito de la prueba (no se usa el `message` del servidor). */
export const PRUEBA_OK = 'Conexión correcta con el directorio.';

function porEstado(err: ApiError, generico: string): string {
  if (err.isUnauthenticated) return SESION;
  if (err.isForbidden) return SIN_PERMISO;
  if (err.status === 400 || err.status === 415) return PETICION_INVALIDA;
  return generico;
}

export function describeDirectoryLoadError(err: unknown): string {
  if (!(err instanceof ApiError)) return ERROR_CARGA;
  return porEstado(err, ERROR_CARGA);
}

export interface DirectoryTestErrorView {
  message: string;
  /** La configuración del servidor no es la que se ve: volver a leerla. */
  stale: boolean;
}

export function describeDirectoryTestError(err: unknown): DirectoryTestErrorView {
  if (!(err instanceof ApiError)) return { message: ERROR_PRUEBA, stale: false };
  if (err.code === 'directorio_no_configurado' || err.status === 409) {
    return { message: MENSAJE_SIN_CONFIGURAR, stale: true };
  }
  if (err.code === 'directorio_no_disponible' || err.status === 503) {
    return { message: ERROR_NO_DISPONIBLE, stale: false };
  }
  return { message: porEstado(err, ERROR_PRUEBA), stale: false };
}
