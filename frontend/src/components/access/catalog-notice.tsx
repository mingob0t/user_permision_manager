'use client';

/**
 * Región `status` del catálogo (DIS-052, extraída de `RequestCatalog`): anuncia el
 * resultado de una solicitud y recibe el foco (`tabIndex -1`). La región existe
 * siempre; solo el contenido aparece con el aviso.
 */

import type { Ref } from 'react';
import { Button } from '../form';
import { Card, SuccessNote } from '../ui';

export function CatalogNotice({
  aviso,
  onClose,
  regionRef,
}: {
  aviso: string | null;
  onClose: () => void;
  regionRef: Ref<HTMLDivElement>;
}) {
  return (
    <div role="status" ref={regionRef} tabIndex={-1} className="rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-primary">
      {aviso ? (
        <Card>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <SuccessNote>{aviso}</SuccessNote>
            <Button variant="secondary" onClick={onClose}>Cerrar aviso</Button>
          </div>
        </Card>
      ) : null}
    </div>
  );
}
