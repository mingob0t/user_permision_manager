'use client';

/** Tarjeta de plataforma: abre el enlace y permite marcar favorito. */

import { useState } from 'react';
import { api } from '@/lib/api';
import { atributoTexto, variablesChipPlataforma } from '@/lib/color-legible';
import { enlaceSeguro } from '@/lib/enlace-seguro';
import type { Platform } from '@/lib/types';
import { variablesCss } from '@/lib/variables-css';
import { useToast } from './toast';
import { Badge } from './ui';

export function PlatformCard({
  platform,
  onFavoriteChange,
}: {
  platform: Platform;
  onFavoriteChange?: (id: number, isFavorite: boolean) => void;
}) {
  const [favorite, setFavorite] = useState(platform.is_favorite);
  const [busy, setBusy] = useState(false);
  const { avisar } = useToast();

  async function toggleFavorite(event: React.MouseEvent) {
    // La tarjeta entera es un enlace: no navegar al pulsar la estrella.
    event.preventDefault();
    event.stopPropagation();
    if (busy) return;

    setBusy(true);
    const previous = favorite;
    setFavorite(!previous); // respuesta inmediata, se revierte si falla
    try {
      const result = await api.toggleFavorite(platform.id);
      setFavorite(result.is_favorite);
      onFavoriteChange?.(platform.id, result.is_favorite);
    } catch {
      setFavorite(previous);
      // DIS-010 (H-17): antes el fallo era silencioso.
      avisar('error', 'No se pudo actualizar el favorito. Inténtalo de nuevo.');
    } finally {
      setBusy(false);
    }
  }

  /** Cuenta la visita sin bloquear la apertura del enlace. */
  function registerVisit() {
    void api.registerVisit(platform.id).catch(() => undefined);
  }

  // SEG-24: solo se pinta en `href` un enlace https:// (DIS-017).
  const link = enlaceSeguro(platform.direct_link);
  const disabled = !link;

  const body = (
    <>
      <div className="flex items-start justify-between gap-3">
        <span
          className="nx-chip-solid grid h-10 w-10 shrink-0 place-items-center rounded-lg text-sm font-semibold"
          data-texto={atributoTexto(platform.bg_color)}
          style={variablesCss(variablesChipPlataforma(platform.bg_color))}
          aria-hidden
        >
          {platform.name.slice(0, 2).toUpperCase()}
        </span>

        {/* DIS-008: estrella de 48 px con foco visible. */}
        <button
          type="button"
          onClick={toggleFavorite}
          disabled={busy}
          aria-pressed={favorite}
          aria-label={favorite ? 'Quitar de favoritos' : 'Añadir a favoritos'}
          className="inline-flex min-h-12 min-w-12 shrink-0 items-center justify-center rounded text-lg leading-none outline-none transition-colors hover:bg-surface-container focus-visible:ring-2 focus-visible:ring-primary disabled:opacity-50"
        >
          <span className={favorite ? 'text-warning-text' : 'text-label'}>
            {favorite ? '★' : '☆'}
          </span>
        </button>
      </div>

      <div className="mt-3 min-w-0">
        <p className="truncate font-medium">{platform.name}</p>
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
    </>
  );

  const shell =
    'flex flex-col rounded-xl border border-panel-border bg-panel-fill p-4 transition-colors';

  // DIS-005: sin opacidad; la insignia "Sin enlace" ya indica el estado (con `opacity-70` el texto
  // bajaba a 3,6:1 y la insignia de advertencia a 2,8:1).
  if (disabled) {
    return <div className={shell}>{body}</div>;
  }

  return (
    <a
      href={link ?? undefined}
      target="_blank"
      rel="noopener noreferrer"
      onClick={registerVisit}
      className={`${shell} hover:border-primary/60`}
    >
      {body}
    </a>
  );
}
