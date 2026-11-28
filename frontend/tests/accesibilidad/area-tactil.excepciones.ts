/**
 * Controles que `area-tactil.test.ts` no puede medir por sus clases pero que
 * miden 44 px o más por su contenido (DIS-008). Es un número exacto por
 * archivo: la prueba falla si aparece otro control sin tamaño en ese archivo
 * y también si sobra la excepción (hay que bajar el número).
 */

export interface ExcepcionAreaTactil {
  cantidad: number;
  motivo: string;
}

export const EXCEPCIONES: Record<string, ExcepcionAreaTactil> = {
  'components/areas/tarjeta-area.tsx': {
    cantidad: 10,
    motivo: 'En cada una de las 10 variantes de diseño, «Ver plataformas» es el control de teclado de la tarjeta; con el ratón o el dedo abre toda la tarjeta (más de 48 px de alto y todo su ancho), DIS-114. El KPI «Solicitudes pendientes» (DIS-162) es un enlace con `min-h-12` (48 px) y no cuenta aquí.',
  },
  'components/estado-badge-boton.tsx': {
    cantidad: 1,
    motivo: 'El botón mide lo del badge, pero `.nx-estado-boton::after` (components.css) amplía su área clicable a 44 × 44 px como mínimo, DIS-114.',
  },
  'components/home/role-summary.tsx': {
    cantidad: 1,
    motivo: 'El contador del inicio es un `Link` `block` que envuelve un `StatTile` completo (más de 48 px de alto y a todo lo ancho de su celda).',
  },
  'components/platform-card.tsx': {
    cantidad: 1,
    motivo: 'El enlace es el nombre, pero su pseudo-elemento `after:absolute after:inset-0` cubre toda la tarjeta (más de 48 px de alto y a todo lo ancho), DIS-051.',
  },
};
