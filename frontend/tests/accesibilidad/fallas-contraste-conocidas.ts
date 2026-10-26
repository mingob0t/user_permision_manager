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

const TODOS: NombreContexto[] = ['claro', 'so-oscuro', 'html.dark', 'emerald', 'obsidian', 'rose', 'violet'];

export const FALLAS_CONOCIDAS: FallaConocida[] = [
  // DIS-005: texto atenuado (muted) a 4.5:1.
  { par: 'bi-text-muted/panel', contextos: ['obsidian'], tarea: 'DIS-005' },
  { par: 'bi-text-muted/surface-container', contextos: ['claro', 'emerald', 'obsidian', 'rose'], tarea: 'DIS-005' },
  { par: 'secondary/panel', contextos: ['so-oscuro', 'html.dark', 'obsidian'], tarea: 'DIS-005' },

  // DIS-006: bordes de campo y panel a 3:1.
  { par: 'input-border/panel', contextos: TODOS, tarea: 'DIS-006' },
  { par: 'panel-border/body-bg', contextos: TODOS, tarea: 'DIS-006' },
];

/** Tarea DIS que corrige el par en ese contexto, o `undefined` si debe cumplir. */
export function tareaPendiente(par: string, contexto: NombreContexto): string | undefined {
  return FALLAS_CONOCIDAS.find((f) => f.par === par && f.contextos.includes(contexto))?.tarea;
}
