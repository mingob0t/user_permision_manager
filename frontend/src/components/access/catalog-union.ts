/**
 * Une el catálogo solicitable (`GET /access-requests/catalog`) con las
 * plataformas que el usuario ya puede abrir (`GET /platforms`) en una sola
 * lista (DIS-030). Función pura: el cruce es por id de plataforma.
 *
 * - Una plataforma del catálogo que el usuario ya puede abrir lleva sus datos
 *   (`mias`) para mostrar enlace y favorito.
 * - Una plataforma abrible que el catálogo no trae se agrega como entrada
 *   "con acceso" sin acción de solicitar, para no perder nada de "Mis plataformas".
 */

import type { CatalogItem } from '@/lib/access/types';
import type { Platform } from '@/lib/types';

export interface CatalogoUnido {
  items: CatalogItem[];
  /** Plataformas abribles por id de plataforma. */
  mias: Map<number, Platform>;
}

export function unirCatalogo(items: CatalogItem[], mias: Platform[]): CatalogoUnido {
  const porId = new Map(mias.map((p) => [p.id, p]));
  const enCatalogo = new Set(items.map((i) => i.platform.id));

  const extras: CatalogItem[] = mias
    .filter((p) => !enCatalogo.has(p.id))
    .map((p) => ({
      platform: { id: p.id, name: p.name, description: p.description, icon: p.icon },
      area: { id: p.area_id, name: p.area_name ?? 'Sin área' },
      my_level: null,
      my_access_status: 'activo' as const,
      pending_request_id: null,
      can_request: false,
      requestable_levels: [],
    }));

  return { items: [...items, ...extras], mias: porId };
}
