'use client';

/**
 * Tarjeta de plataforma: abre el enlace y permite marcar favorito.
 *
 * DIS-051: sin interactivos anidados. La tarjeta es un contenedor; el enlace principal es el
 * nombre y su pseudo-elemento cubre toda la tarjeta (sigue siendo clicable entera); la
 * estrella es hermana del enlace y queda por encima (`z-10`).
 */

import { api } from '@/lib/api';
import { atributoTexto, variablesChipPlataforma } from '@/lib/color-legible';
import { enlaceSeguro } from '@/lib/enlace-seguro';
import type { Platform } from '@/lib/types';
import { variablesCss } from '@/lib/variables-css';
import { FavoriteButton } from './favorite-button';
import { Badge, Card } from './ui';

export function PlatformCard({
  platform,
  onFavoriteChange,
}: {
  platform: Platform;
  onFavoriteChange?: (id: number, isFavorite: boolean) => void;
}) {
  /** Cuenta la visita sin bloquear la apertura del enlace. */
  function registerVisit() {
    void api.registerVisit(platform.id).catch(() => undefined);
  }

  // SEG-24: solo se pinta en `href` un enlace https:// (DIS-017).
  const link = enlaceSeguro(platform.direct_link);
  const disabled = !link;

  // Pseudo-elemento que extiende el área clicable del enlace a toda la tarjeta.
  const nombreEnlace =
    'outline-none after:absolute after:inset-0 after:rounded-xl focus-visible:after:ring-2 focus-visible:after:ring-primary';

  // DIS-005: sin opacidad; la insignia "Sin enlace" ya indica el estado (con `opacity-70` el texto
  // bajaba a 3,6:1 y la insignia de advertencia a 2,8:1).
  return (
    <Card variant={disabled ? 'default' : 'link'} className="relative flex flex-col p-4">
      <div className="flex items-start justify-between gap-3">
        <span
          className="nx-chip-solid grid h-10 w-10 shrink-0 place-items-center rounded-lg text-sm font-semibold"
          data-texto={atributoTexto(platform.bg_color)}
          style={variablesCss(variablesChipPlataforma(platform.bg_color))}
          aria-hidden
        >
          {platform.name.slice(0, 2).toUpperCase()}
        </span>

        <span className="relative z-10">
          <FavoriteButton
            platformId={platform.id}
            name={platform.name}
            initial={platform.is_favorite}
            onChange={onFavoriteChange}
          />
        </span>
      </div>

      <div className="mt-3 min-w-0">
        <p className="truncate font-medium">
          {link ? (
            <a
              href={link}
              target="_blank"
              rel="noopener noreferrer"
              onClick={registerVisit}
              className={nombreEnlace}
            >
              {platform.name}
            </a>
          ) : (
            platform.name
          )}
        </p>
        <p className="mt-0.5 line-clamp-2 text-sm text-label">
          {platform.description}
        </p>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        {platform.area_name ? (
          <span
            className="nx-chip-tint inline-flex items-center rounded-full px-2 py-0.5 text-xs"
            style={variablesCss({ '--chip-color': platform.area_color })}
          >
            {platform.area_name}
          </span>
        ) : null}
        {platform.status !== 'Activo' ? (
          <Badge tone="warning">{platform.status}</Badge>
        ) : null}
        {disabled ? <Badge>Sin enlace</Badge> : null}
      </div>
    </Card>
  );
}
