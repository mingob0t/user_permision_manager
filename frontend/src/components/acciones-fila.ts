/**
 * Clases de las acciones de fila y de tarjeta (DIS-008, DIS-035, DIS-058).
 * Absorbidas en Button / ButtonLink variant="fila" y variant="fila-peligro".
 */

/** Acción normal (Editar, Accesos, Historial…). */
export const ACCION_FILA = 'nexus-btn nexus-btn-fila min-h-12 min-w-12 text-primary-text focus-visible:ring-primary';

/** Acción destructiva (Eliminar): abre siempre una confirmación. */
export const ACCION_FILA_PELIGRO = 'nexus-btn nexus-btn-fila-peligro min-h-12 min-w-12 text-error-text focus-visible:ring-primary';
