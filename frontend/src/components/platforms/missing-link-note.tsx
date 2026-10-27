/** Aviso de plataformas sin enlace directo configurado. */

import { Card } from '../ui';

export function MissingLinkNote({ count }: { count: number }) {
  if (count === 0) return null;
  return (
    <Card className="border-warning/40 bg-warning/10">
      <p className="text-sm">
        <strong>{count}</strong>{' '}
        {count === 1 ? 'plataforma no tiene' : 'plataformas no tienen'}{' '}
        enlace configurado, así que no se pueden abrir desde el catálogo.
      </p>
    </Card>
  );
}
