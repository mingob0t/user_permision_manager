'use client';

/** Plataformas marcadas como favoritas. */

import { useEffect, useRef, useState } from 'react';
import { api } from '@/lib/api';
import { useAsync } from '@/lib/use-async';
import { PlatformCard } from './platform-card';
import { RegionDeAnuncios } from './region-de-anuncios';
import { EmptyNote, ErrorNote, Spinner } from './ui';

export function FavoritesList() {
  const { data, loading, error, reload } = useAsync(() => api.favorites(), []);
  const [anuncio, setAnuncio] = useState('');
  const encabezado = useRef<HTMLHeadingElement>(null);
  const contenedor = useRef<HTMLDivElement>(null);
  /** DIS-051: destino del foco tras quitar un favorito (`null` = encabezado). */
  const destino = useRef<{ id: number | null } | null>(null);

  function alQuitar(id: number) {
    const lista = data ?? [];
    const i = lista.findIndex((p) => p.id === id);
    // La siguiente tarjeta; si era la última, la anterior; si no queda ninguna, el encabezado.
    const vecino = lista[i + 1] ?? lista[i - 1];
    destino.current = { id: vecino ? vecino.id : null };
    setAnuncio(`«${lista[i]?.name ?? 'Plataforma'}» quitada de favoritos.`);
    reload();
  }

  // Al terminar la recarga la tarjeta ya salió: el foco no puede quedar en `body`.
  useEffect(() => {
    if (loading || !destino.current) return;
    const { id } = destino.current;
    destino.current = null;
    const boton = id === null || error
      ? null
      : contenedor.current?.querySelector<HTMLElement>(`[data-favorito-id="${id}"] button`);
    (boton ?? encabezado.current)?.focus();
  }, [loading, data, error]);

  return (
    <div className="space-y-6">
      <RegionDeAnuncios mensaje={anuncio} />
      <div>
        <h1 ref={encabezado} tabIndex={-1} className="text-2xl font-semibold outline-none">Favoritos</h1>
        <p className="mt-1 text-sm text-label">
          Tus accesos marcados para consulta rápida.
        </p>
      </div>

      {loading ? <Spinner /> : null}
      {error ? <ErrorNote message={error} /> : null}

      {!loading && !error ? (
        (data ?? []).length === 0 ? (
          <EmptyNote message="Todavía no has marcado ninguna plataforma como favorita." />
        ) : (
          <div ref={contenedor} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {(data ?? []).map((platform) => (
              <div key={platform.id} data-favorito-id={platform.id} className="contents">
                <PlatformCard
                  platform={{ ...platform, is_favorite: true }}
                  // Al desmarcar, recargar para que salga de la lista y mover el foco.
                  onFavoriteChange={(id, isFavorite) => {
                    if (!isFavorite) alQuitar(id);
                  }}
                />
              </div>
            ))}
          </div>
        )
      ) : null}
    </div>
  );
}
