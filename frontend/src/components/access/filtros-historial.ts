/**
 * Filtros del Historial de solicitudes (DIS-163): la URL queda limpia (`/approvals/historial`).
 * - Los enlaces con filtros (`/approvals?status=pendiente&area_id=3`, DIS-036/137) se leen una vez.
 * - Después los filtros viven en `sessionStorage` (por pestaña): F5 los conserva sin mostrarlos
 *   en la barra de direcciones. Sin almacenamiento (modo privado o bloqueado) se usan los valores
 *   por defecto; nunca falla.
 */

import type { InboxStatus } from '@/lib/access/types';
import { idDeUrl, valorPermitido } from './filtro-url';

/** Ruta limpia del Historial. */
export const RUTA_HISTORIAL = '/approvals/historial';

const CLAVE = 'portal.historial-solicitudes.filtros';
const PARAMETROS = ['status', 'area_id', 'platform_id', 'q'] as const;

export interface FiltrosHistorial {
  status: InboxStatus;
  areaId: number | null;
  plataformaId: number | null;
  q: string;
}

type Lector = { get: (nombre: string) => string | null } | null | undefined;

function normalizar(leer: Lector, estados: readonly InboxStatus[], defecto: InboxStatus): FiltrosHistorial {
  return {
    status: valorPermitido(leer?.get('status'), estados) ?? defecto,
    areaId: idDeUrl(leer?.get('area_id')),
    plataformaId: idDeUrl(leer?.get('platform_id')),
    q: leer?.get('q') ?? '',
  };
}

/** Filtros de entrada: los de la URL si trae alguno; si no, los guardados; si no, por defecto. */
export function filtrosIniciales(
  params: Lector,
  estados: readonly InboxStatus[],
  defecto: InboxStatus,
): FiltrosHistorial {
  if (PARAMETROS.some((p) => params?.get(p))) return normalizar(params, estados, defecto);
  return normalizar(leerGuardados(), estados, defecto);
}

function leerGuardados(): URLSearchParams | null {
  try {
    const texto = window.sessionStorage.getItem(CLAVE);
    return texto ? new URLSearchParams(texto) : null;
  } catch {
    return null;
  }
}

/** Guarda los filtros de la pestaña y deja la URL en la ruta limpia (sin entrada nueva en el historial). */
export function guardarFiltrosHistorial(filtros: FiltrosHistorial): void {
  const consulta = new URLSearchParams({ status: filtros.status });
  if (filtros.areaId !== null) consulta.set('area_id', String(filtros.areaId));
  if (filtros.plataformaId !== null) consulta.set('platform_id', String(filtros.plataformaId));
  if (filtros.q) consulta.set('q', filtros.q);
  try {
    window.sessionStorage.setItem(CLAVE, consulta.toString());
  } catch {
    // Sin almacenamiento: los filtros se pierden al recargar; la pantalla sigue funcionando.
  }
  if (window.location.pathname !== RUTA_HISTORIAL || window.location.search) {
    window.history.replaceState(window.history.state, '', RUTA_HISTORIAL);
  }
}
