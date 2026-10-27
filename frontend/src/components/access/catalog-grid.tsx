'use client';

/**
 * Rejilla y estados del catálogo (DIS-052, extraídos de `RequestCatalog`): carga,
 * errores con reintento, vacío y tarjetas. No conoce el origen de los datos.
 */

import type { CatalogItem } from '@/lib/access/types';
import type { Platform } from '@/lib/types';
import { Button } from '../form';
import { EmptyNote, ErrorNote, Spinner } from '../ui';
import { RequestCatalogCard, puedeSolicitar } from './request-catalog-card';
import type { MisPlataformas } from './use-catalogo-solicitable';

export interface EstadoCarga {
  data: unknown;
  loading: boolean;
  error: string | null;
  reload: () => void;
}

export function CatalogGrid({
  catalogo,
  mias,
  shown,
  filtrando,
  mine,
  motivo,
  onRequest,
}: {
  catalogo: EstadoCarga;
  mias?: MisPlataformas;
  /** Ítems ya filtrados. */
  shown: CatalogItem[];
  filtrando: boolean;
  mine: Map<number, Platform>;
  motivo: (item: CatalogItem) => string;
  onRequest: (item: CatalogItem, trigger: HTMLButtonElement) => void;
}) {
  return (
    <>
      {(catalogo.loading && !catalogo.data) || (mias?.loading && !catalogo.error)
        ? <Spinner label="Cargando catálogo…" /> : null}

      {mias?.error && !mias.loading ? (
        <div className="space-y-3">
          <ErrorNote message="No se pudieron cargar los enlaces y favoritos de tus plataformas." />
          <Button variant="secondary" onClick={mias.reload}>Reintentar enlaces</Button>
        </div>
      ) : null}

      {catalogo.error ? (
        <div className="space-y-3">
          <ErrorNote message={catalogo.error} />
          <Button variant="secondary" onClick={catalogo.reload}>Reintentar</Button>
        </div>
      ) : null}

      {/* Sin permiso para el catálogo pero con plataformas propias: se muestran solas. */}
      {!mias?.loading && (catalogo.data || (catalogo.error && mias?.data?.length)) ? (
        shown.length === 0 ? (
          <EmptyNote
            message={filtrando
              ? 'Ninguna plataforma coincide con el filtro.'
              : 'No hay plataformas en el catálogo de tus áreas.'}
          />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {shown.map((item) => (
              <RequestCatalogCard
                key={item.platform.id}
                item={item}
                mine={mine.get(item.platform.id)}
                reason={puedeSolicitar(item) ? '' : motivo(item)}
                onRequest={onRequest}
              />
            ))}
          </div>
        )
      ) : null}
    </>
  );
}
