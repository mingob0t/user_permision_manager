/**
 * Tarjeta del catálogo solicitable (DIS-013): estado del usuario en la
 * plataforma (insignias con texto) y la acción "Solicitar acceso" solo si el
 * contrato la permite (`can_request` con niveles solicitables).
 *
 * Misma caja que `PlatformCard`: los datos del catálogo no son una `Platform`,
 * por eso es una tarjeta aparte (la de Favoritos solo cambió su estrella, DIS-030).
 *
 * DIS-030: si la plataforma ya se puede abrir (`mine`, de `GET /platforms`),
 * suma el favorito y el botón "Abrir" (solo `https://`, cuenta la visita).
 * La solicitud no cambia.
 */

import { api } from '@/lib/api';
import type { CatalogItem } from '@/lib/access/types';
import { enlaceSeguro } from '@/lib/enlace-seguro';
import type { Platform } from '@/lib/types';
import { FavoriteButton } from '../favorite-button';
import { Button, ButtonLink } from '../form';
import { Badge, Card } from '../ui';
import { AccessStatusBadge } from './access-status-badge';

export function puedeSolicitar(item: CatalogItem): boolean {
  return item.can_request && item.requestable_levels.length > 0;
}

export function RequestCatalogCard({
  item,
  reason,
  mine,
  onRequest,
}: {
  item: CatalogItem;
  /** Datos de `GET /platforms` si el usuario ya puede abrirla. */
  mine?: Platform;
  /** Por qué no se puede solicitar, si no hay acción. */
  reason: string;
  onRequest: (item: CatalogItem, trigger: HTMLButtonElement) => void;
}) {
  const { platform, area } = item;
  const tituloId = `catalogo-plataforma-${platform.id}`;
  const pendiente = item.pending_request_id !== null;
  // SEG-24: solo se pinta en `href` un enlace https:// (DIS-017).
  // Acceso automático (admin de área, superadmin): el catálogo no trae estado pero la abre.
  const estado = mine && (!item.my_access_status || item.my_access_status === 'revocado')
    ? 'activo' : item.my_access_status;
  // "Abrir" solo con el acceso efectivo `activo`; con otro estado va solo la insignia.
  const abrible = Boolean(mine) && estado === 'activo';
  const enlace = mine && abrible ? enlaceSeguro(mine.direct_link) : null;

  return (
    <Card
      as="article"
      aria-labelledby={tituloId}
      className="flex flex-col p-4"
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
        {mine ? (
          <span className="ml-auto">
            <FavoriteButton platformId={platform.id} name={platform.name} initial={mine.is_favorite} />
          </span>
        ) : null}
      </div>

      {platform.description ? (
        <p className="mt-3 line-clamp-2 text-sm text-label">{platform.description}</p>
      ) : null}

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <AccessStatusBadge status={estado} level={item.my_level} />
        {pendiente ? <Badge tone="warning">Solicitud pendiente</Badge> : null}
        {mine && mine.status !== 'Activo' ? <Badge tone="warning">{mine.status}</Badge> : null}
        {abrible && !enlace ? <Badge>Sin enlace</Badge> : null}
      </div>

      <div className="mt-auto space-y-2 pt-4">
        {enlace ? (
          <ButtonLink
            href={enlace}
            target="_blank"
            rel="noopener noreferrer"
            aria-label={`Abrir ${platform.name} (se abre en una pestaña nueva)`}
            onClick={() => { void api.registerVisit(platform.id).catch(() => undefined); }}
            variant="primary"
            className="w-full"
          >
            Abrir
          </ButtonLink>
        ) : null}
        {puedeSolicitar(item) ? (
          <Button
            variant="secondary"
            className="w-full"
            aria-label={`Solicitar acceso a ${platform.name}`}
            onClick={(event) => onRequest(item, event.currentTarget)}
          >
            Solicitar acceso
          </Button>
        ) : reason ? (
          <p className="text-xs text-label">{reason}</p>
        ) : null}
      </div>
    </Card>
  );
}
