/**
 * Tarjeta del catálogo solicitable (DIS-013): estado del usuario en la
 * plataforma (insignias con texto) y la acción "Solicitar acceso" solo si el
 * contrato la permite (`can_request` con niveles solicitables).
 *
 * Misma caja que `PlatformCard`, sin tocarla: los datos del catálogo no son
 * una `Platform` y la tarjeta de Favoritos no cambia.
 */

import type { CatalogItem } from '@/lib/access/types';
import { Button } from '../form';
import { Badge } from '../ui';
import { AccessStatusBadge } from './access-status-badge';

export function puedeSolicitar(item: CatalogItem): boolean {
  return item.can_request && item.requestable_levels.length > 0;
}

export function RequestCatalogCard({
  item,
  reason,
  onRequest,
}: {
  item: CatalogItem;
  /** Por qué no se puede solicitar, si no hay acción. */
  reason: string;
  onRequest: (item: CatalogItem, trigger: HTMLButtonElement) => void;
}) {
  const { platform, area } = item;
  const tituloId = `catalogo-plataforma-${platform.id}`;
  const pendiente = item.pending_request_id !== null;

  return (
    <article
      aria-labelledby={tituloId}
      className="flex flex-col rounded-xl border border-panel-border bg-panel-fill p-4"
    >
      <div className="flex items-start gap-3">
        <span
          className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-primary/15 text-sm font-semibold text-primary-text"
          aria-hidden
        >
          {platform.name.slice(0, 2).toUpperCase()}
        </span>
        <div className="min-w-0">
          <h3 id={tituloId} className="line-clamp-2 break-words font-medium">{platform.name}</h3>
          <p className="line-clamp-2 break-words text-xs text-label">{area.name}</p>
        </div>
      </div>

      {platform.description ? (
        <p className="mt-3 line-clamp-2 text-sm text-label">{platform.description}</p>
      ) : null}

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <AccessStatusBadge status={item.my_access_status} level={item.my_level} />
        {pendiente ? <Badge tone="warning">Solicitud pendiente</Badge> : null}
      </div>

      <div className="mt-auto pt-4">
        {puedeSolicitar(item) ? (
          <Button
            variant="secondary"
            className="w-full"
            aria-label={`Solicitar acceso a ${platform.name}`}
            onClick={(event) => onRequest(item, event.currentTarget)}
          >
            Solicitar acceso
          </Button>
        ) : (
          <p className="text-xs text-label">{reason}</p>
        )}
      </div>
    </article>
  );
}
