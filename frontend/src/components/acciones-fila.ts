/**
 * Clases de las acciones de fila y de tarjeta (DIS-008, DIS-035): botones o
 * enlaces de texto con área táctil de 48 px (`min-h-12`, `min-w-12`), foco
 * visible y el mismo aspecto en Usuarios, Áreas y Administrar plataformas.
 * Solo tokens: `primary-text` / `error-text` y sus tintes al pasar el puntero.
 */

const BASE =
  'inline-flex min-h-12 min-w-12 items-center justify-center rounded px-3 text-xs ' +
  'outline-none focus-visible:ring-2 focus-visible:ring-primary';

/** Acción normal (Editar, Accesos, Historial…). */
export const ACCION_FILA = `${BASE} text-primary-text hover:bg-primary/10`;

/** Acción destructiva (Eliminar): abre siempre una confirmación. */
export const ACCION_FILA_PELIGRO = `${BASE} text-error-text hover:bg-error/10`;
