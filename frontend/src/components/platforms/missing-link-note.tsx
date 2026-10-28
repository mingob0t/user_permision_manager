/** Aviso de plataformas sin enlace directo configurado. */

import { Note } from '../note';

export function MissingLinkNote({ count }: { count: number }) {
  if (count === 0) return null;
  return (
    <Note tone="warning">
      <p className="text-sm">
        <strong>{count}</strong>{' '}
        {count === 1 ? 'plataforma no tiene' : 'plataformas no tienen'}{' '}
        enlace configurado, así que no se pueden abrir desde el catálogo.
      </p>
    </Note>
  );
}
