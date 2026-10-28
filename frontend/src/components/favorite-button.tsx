'use client';

/**
 * Estrella de favorito de una plataforma (extraída de `PlatformCard`, DIS-030):
 * respuesta inmediata, se revierte y avisa si falla. 48 px con foco visible (DIS-008).
 */

import { useState } from 'react';
import { api } from '@/lib/api';
import { useToast } from './toast';

import { ToggleChip } from './toggle-chip';

export function FavoriteButton({
  platformId,
  name,
  initial,
  onChange,
}: {
  platformId: number;
  /** Nombre de la plataforma: el nombre accesible es fijo y el estado va en `aria-pressed`. */
  name: string;
  initial: boolean;
  onChange?: (id: number, isFavorite: boolean) => void;
}) {
  const [favorite, setFavorite] = useState(initial);
  const [busy, setBusy] = useState(false);
  const { avisar } = useToast();

  async function toggle(event: React.MouseEvent) {
    // Dentro de una tarjeta-enlace no se debe navegar al pulsar la estrella.
    event.preventDefault();
    event.stopPropagation();
    if (busy) return;

    setBusy(true);
    const previous = favorite;
    setFavorite(!previous); // respuesta inmediata, se revierte si falla
    try {
      const result = await api.toggleFavorite(platformId);
      setFavorite(result.is_favorite);
      onChange?.(platformId, result.is_favorite);
    } catch {
      setFavorite(previous);
      // DIS-010 (H-17): antes el fallo era silencioso.
      avisar('error', 'No se pudo actualizar el favorito. Inténtalo de nuevo.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <ToggleChip
      variant="icon"
      onClick={toggle}
      aria-disabled={busy}
      pressed={favorite}
      aria-label={`Favorito: ${name}`}
    >
      <span className={favorite ? 'text-warning-text' : 'text-label'}>
        {favorite ? '★' : '☆'}
      </span>
    </ToggleChip>
  );
}
