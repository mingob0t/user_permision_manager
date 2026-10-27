/**
 * Pares que HOY no llegan al mínimo WCAG AA (FNC-025).
 *
 * No se corrigen aquí: cada grupo indica la tarea DIS que los corregirá. La
 * prueba los marca con `it.fails`, así que en cuanto una tarea DIS corrija un
 * par, su prueba empezará a fallar y habrá que quitarlo de esta lista.
 * Fuente: auditoría de accesibilidad inicial (2026-10-13), sección 1.
 */
import type { NombreContexto } from '../utils/tokens-css';

interface FallaConocida {
  par: string;
  contextos: NombreContexto[];
  tarea: string;
}

// Vacía desde DIS-004, DIS-005 y DIS-006 (2026-10-26): las 25 celdas conocidas cumplen.
// Una falla nueva se agrega aquí con la tarea DIS que la corregirá.
export const FALLAS_CONOCIDAS: FallaConocida[] = [];

/** Tarea DIS que corrige el par en ese contexto, o `undefined` si debe cumplir. */
export function tareaPendiente(par: string, contexto: NombreContexto): string | undefined {
  return FALLAS_CONOCIDAS.find((f) => f.par === par && f.contextos.includes(contexto))?.tarea;
}
