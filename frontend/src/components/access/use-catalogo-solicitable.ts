'use client';

/**
 * Carga y unión de datos del catálogo solicitable (DIS-052, extraído de `RequestCatalog`):
 * `GET /access-requests/catalog` cruzado con las plataformas propias (DIS-030) y los
 * cambios locales tras solicitar. No pinta nada.
 */

import { useCallback, useMemo, useState } from 'react';
import { requestsApi } from '@/lib/access/requests';
import type { CatalogItem } from '@/lib/access/types';
import type { Platform } from '@/lib/types';
import { useAsync } from '@/lib/use-async';
import { unirCatalogo } from './catalog-union';
import { describeCatalogError } from './request-errors';

/** Estado de la carga de `GET /platforms` (lo resuelve quien monta la vista). */
export interface MisPlataformas {
  data: Platform[] | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
}

/** Cambios locales tras solicitar, por plataforma. */
type Solicitadas = Record<number, number>;

function aplicarSolicitadas(items: CatalogItem[], solicitadas: Solicitadas): CatalogItem[] {
  return items.map((item) => {
    const id = solicitadas[item.platform.id];
    return id === undefined ? item : { ...item, pending_request_id: id, can_request: false };
  });
}

export function useCatalogoSolicitable(mias?: MisPlataformas) {
  const [solicitadas, setSolicitadas] = useState<Solicitadas>({});

  const catalogo = useAsync(
    () => requestsApi.catalog().catch((err: unknown) => {
      throw new Error(describeCatalogError(err));
    }),
    [],
  );

  const unido = useMemo(
    () => unirCatalogo(catalogo.data ?? [], mias?.data ?? []),
    [catalogo.data, mias?.data],
  );
  const items = useMemo(
    () => aplicarSolicitadas(unido.items, solicitadas),
    [unido.items, solicitadas],
  );
  const areas = useMemo(() => {
    const vistas = new Map<number, string>();
    for (const item of items) vistas.set(item.area.id, item.area.name);
    return [...vistas].map(([id, name]) => ({ id, name }));
  }, [items]);

  const marcarSolicitada = useCallback((platformId: number, requestId: number) => {
    setSolicitadas((prev) => ({ ...prev, [platformId]: requestId }));
  }, []);

  return {
    catalogo,
    items,
    areas,
    /** Plataformas abribles por id de plataforma. */
    mias: unido.mias,
    marcarSolicitada,
  };
}
