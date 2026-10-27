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
  'components/home/role-summary.tsx': {
    cantidad: 1,
    motivo: 'El contador del inicio es un `Link` `block` que envuelve un `StatTile` completo (más de 48 px de alto y a todo lo ancho de su celda).',
  },
};
