'use client';

/**
 * Vista única de `/platforms` (DIS-030): el catálogo solicitable con enlace y
 * favorito de las plataformas que ya se pueden abrir. Carga `GET /platforms`
 * y la pasa a `RequestCatalog`, que hace el cruce, el filtro por área y la búsqueda.
 */

import { api } from '@/lib/api';
import { useAsync } from '@/lib/use-async';
import { RequestCatalog } from './access/request-catalog';

export function PlatformsView() {
  const mias = useAsync(() => api.platforms(), []);
  return <RequestCatalog mias={mias} />;
}
