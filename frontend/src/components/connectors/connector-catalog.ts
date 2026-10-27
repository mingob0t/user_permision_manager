/**
 * Tipos, parámetros y reglas del formulario de conector (DIS-022, F-CON-01,
 * `PUT /platforms/<id>/connector`, contrato `conectores-y-ejecuciones.md` 1.1).
 *
 * - Las reglas son espejo de `app/modules/connectors/validacion.py`; el
 *   servidor las vuelve a validar (host de la lista blanca, tipo registrado,
 *   `params` sin secretos).
 * - La credencial es solo la referencia del ítem del gestor (ADR-005): el
 *   portal nunca pide ni muestra el secreto.
 * - Parámetros por tipo (`api`, `ssh` y `bd`, contrato 1.4): en
 *   `connector-params.ts` (DIS-042); aquí se re-exportan.
 */

import type { Connector, ConnectorInput, ConnectorType } from '@/lib/access/types';
import type { Badge } from '../ui';
import {
  PARAMETROS_POR_TIPO, construirParams, parametrosDe, parametrosSinEditor, validarParametros, valoresDesde,
} from './connector-params';

export { PARAMETROS_POR_TIPO, validarParametros };
export type { CampoParametro } from './connector-params';

type Tono = React.ComponentProps<typeof Badge>['tone'];

export const TIPOS_CONECTOR: Record<ConnectorType, string> = {
  api: 'API',
  ssh: 'SSH',
  bd: 'Base de datos',
};

export const ESTADOS_CREDENCIAL: Record<Connector['credential_status'], { texto: string; tono: Tono }> = {
  ok: { texto: 'Credencial verificada', tono: 'success' },
  no_encontrada: { texto: 'Credencial no encontrada', tono: 'error' },
  sin_verificar: { texto: 'Credencial sin verificar', tono: 'warning' },
};

/** Largos y límites del contrato (`app/modules/connectors/tipos.py`). */
export const HOST_MAX = 253;
export const REFERENCIA_MAX = 200;
export const PUERTO_MIN = 1;
export const PUERTO_MAX = 65535;

/** Segmentos separados por "/" (`PATRON_REFERENCIA` del backend). */
const PATRON_REFERENCIA = /^[A-Za-z0-9][A-Za-z0-9._-]*(\/[A-Za-z0-9][A-Za-z0-9._-]*)*$/;
/** Caracteres de un nombre de host; el servidor decide si está autorizado. */
const PATRON_HOST = /^[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?(\.[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?)*$/;

export type CampoConector = 'type' | 'host' | 'port' | 'credential_ref' | 'params' | 'active';

export interface FormularioConector {
  type: string;
  host: string;
  port: string;
  credential_ref: string;
  /** Valores de texto de los parámetros del tipo elegido (clave con puntos). */
  params: Record<string, string>;
  active: boolean;
}

export const OBLIGATORIO = 'Es obligatorio.';

/** Mensaje fijo por campo (no se repite el del servidor). */
export const MENSAJES_CAMPO: Record<CampoConector, string> = {
  type: 'Este tipo de conector no está disponible en el servidor.',
  host: 'Usa un nombre de host autorizado por el despliegue (nunca una dirección IP).',
  port: `Usa un puerto entre ${PUERTO_MIN} y ${PUERTO_MAX}.`,
  credential_ref: `Usa la referencia del ítem en el gestor de secretos (segmentos separados por "/", hasta ${REFERENCIA_MAX} caracteres), nunca la contraseña.`,
  params: 'Revisa los parámetros: no deben incluir secretos.',
  active: 'Indica si el conector está activo.',
};

export const FORMULARIO_VACIO: FormularioConector = {
  type: 'api', host: '', port: '', credential_ref: '', params: {}, active: true,
};

/** ¿El tipo tiene editor en esta pantalla? */
export function esTipoConocido(tipo: string): tipo is ConnectorType {
  return tipo in TIPOS_CONECTOR;
}

/** Formulario con la configuración guardada (o vacío si no hay). */
export function formularioDesde(connector: Connector | null): FormularioConector {
  if (!connector) return { ...FORMULARIO_VACIO, params: {} };
  return {
    type: connector.type,
    host: connector.host,
    port: String(connector.port),
    credential_ref: connector.credential_ref,
    params: valoresDesde(connector),
    active: connector.active,
  };
}

/**
 * Parámetros guardados sin editor aquí (se conservan tal cual al guardar si
 * no cambia el tipo). Solo se muestran sus nombres.
 */
export const parametrosConservados = parametrosSinEditor;

export function validarConector(form: FormularioConector): Partial<Record<CampoConector, string>> {
  const errores: Partial<Record<CampoConector, string>> = {};
  if (!form.type) errores.type = OBLIGATORIO;
  const host = form.host.trim();
  if (!host) errores.host = OBLIGATORIO;
  else if (host.length > HOST_MAX || !PATRON_HOST.test(host)) errores.host = MENSAJES_CAMPO.host;
  const puerto = form.port.trim();
  if (!puerto) errores.port = OBLIGATORIO;
  else if (!/^\d+$/.test(puerto) || Number(puerto) < PUERTO_MIN || Number(puerto) > PUERTO_MAX) {
    errores.port = MENSAJES_CAMPO.port;
  }
  const referencia = form.credential_ref.trim();
  if (!referencia) errores.credential_ref = OBLIGATORIO;
  else if (referencia.length > REFERENCIA_MAX || !PATRON_REFERENCIA.test(referencia)) {
    errores.credential_ref = MENSAJES_CAMPO.credential_ref;
  }
  return errores;
}

/** Cuerpo del contrato (lista blanca): parámetros vacíos u ocultos no se envían. */
export function cuerpoConector(form: FormularioConector, guardado: Connector | null): ConnectorInput {
  const params = { ...parametrosConservados(guardado, form.type), ...construirParams(form.type, form.params) };
  return {
    type: form.type as ConnectorType,
    host: form.host.trim(),
    port: Number(form.port.trim()),
    params,
    credential_ref: form.credential_ref.trim(),
    active: form.active,
  };
}

export { parametrosDe as parametrosDelTipo };
