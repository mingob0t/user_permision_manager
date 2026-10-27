import { isIP } from 'node:net';
import type { Rewrite } from 'next/dist/lib/load-custom-routes';

/**
 * Rewrites de Next hacia el backend, solo en desarrollo (FNC-005, FNC-118).
 *
 * En producción nginx manda /api/ directo a Flask; si Next también reenviara,
 * una ruta que llegara a Next llegaría a Flask desde el proxy de confianza
 * con las cabeceras Remote-* del cliente (suplantación con SSO activo).
 */

/** Backend local de desarrollo; nombre de host, sin IP. */
export const BACKEND_URL_POR_DEFECTO = 'http://localhost:5001';

/** Valida `BACKEND_URL`: URL http(s) con nombre de host, nunca una IP. */
export function urlBackend(valor: string | undefined): string {
  const url = (valor ?? '').trim() || BACKEND_URL_POR_DEFECTO;
  let host: string;
  try {
    const u = new URL(url);
    if (u.protocol !== 'http:' && u.protocol !== 'https:') throw new Error();
    host = u.hostname.replace(/^\[|\]$/g, '');
  } catch {
    throw new Error('BACKEND_URL debe ser una URL http(s) válida con nombre de host');
  }
  if (isIP(host) !== 0) {
    throw new Error('BACKEND_URL no puede ser una dirección IP: usa un nombre de host');
  }
  return url.replace(/\/+$/, '');
}

/** Solo con `NODE_ENV=development` existe el rewrite de `/api`; no hay `/auth`. */
export function rewritesDeDesarrollo(env: NodeJS.ProcessEnv): Rewrite[] {
  const backend = urlBackend(env.BACKEND_URL);
  if (env.NODE_ENV !== 'development') return [];
  return [{ source: '/api/:path*', destination: `${backend}/api/:path*` }];
}
