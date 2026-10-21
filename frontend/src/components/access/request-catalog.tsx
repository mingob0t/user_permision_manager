'use client';

/**
 * Catálogo solicitable (DIS-013, F-SOL-01/02, `GET /access-requests/catalog`):
 * plataformas de las áreas del usuario con su estado y la solicitud de nivel.
 *
 * - El catálogo no se pagina (acotado por áreas, contrato 1.1): el filtro por
 *   área y la búsqueda se resuelven en el cliente con una sola carga.
 * - Tras solicitar, la tarjeta pasa a "pendiente" sin recargar y el resultado
 *   se anuncia en una región `status` que recibe el foco.
 */

import { useCallback, useMemo, useRef, useState } from 'react';
import { requestsApi } from '@/lib/access/requests';
import type { AccessRequest, CatalogItem } from '@/lib/access/types';
import { useAsync } from '@/lib/use-async';
import { Button, Select, TextInput } from '../form';
import { useSession } from '../session-provider';
import { Card, EmptyNote, ErrorNote, Spinner } from '../ui';
import { NIVELES } from './access-status-badge';
import { RequestCatalogCard, puedeSolicitar } from './request-catalog-card';
import { describeCatalogError } from './request-errors';
import { RequestFormModal } from './request-form-modal';

const BUSCADOR_ID = 'catalogo-buscar';

/** Cambios locales tras solicitar, por plataforma. */
type Solicitadas = Record<number, number>;

function aplicarSolicitadas(items: CatalogItem[], solicitadas: Solicitadas): CatalogItem[] {
  return items.map((item) => {
    const id = solicitadas[item.platform.id];
    return id === undefined ? item : { ...item, pending_request_id: id, can_request: false };
  });
}

function coincide(item: CatalogItem, needle: string): boolean {
  return item.platform.name.toLowerCase().includes(needle)
    || (item.platform.description ?? '').toLowerCase().includes(needle);
}

export function RequestCatalog() {
  const { session } = useSession();
  const esSuperadmin = session?.permissions.is_admin ?? false;
  const administradas = useMemo(
    () => new Set((session?.managed_areas ?? []).map((a) => a.id)),
    [session],
  );

  const [areaId, setAreaId] = useState<number | null>(null);
  const [term, setTerm] = useState('');
  const [solicitadas, setSolicitadas] = useState<Solicitadas>({});
  const [abierta, setAbierta] = useState<CatalogItem | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const disparador = useRef<HTMLElement | null>(null);
  const avisoRef = useRef<HTMLDivElement>(null);

  const catalogo = useAsync(
    () => requestsApi.catalog().catch((err: unknown) => {
      throw new Error(describeCatalogError(err));
    }),
    [],
  );

  const items = useMemo(
    () => aplicarSolicitadas(catalogo.data ?? [], solicitadas),
    [catalogo.data, solicitadas],
  );

  const areas = useMemo(() => {
    const vistas = new Map<number, string>();
    for (const item of items) vistas.set(item.area.id, item.area.name);
    return [...vistas].map(([id, name]) => ({ id, name }));
  }, [items]);

  const shown = useMemo(() => {
    const needle = term.trim().toLowerCase();
    return items.filter((item) =>
      (areaId === null || item.area.id === areaId) && (!needle || coincide(item, needle)));
  }, [items, areaId, term]);

  function motivo(item: CatalogItem): string {
    if (item.pending_request_id !== null) return 'Espera la decisión del administrador del área.';
    if (esSuperadmin) return 'Como superadmin ya tienes acceso a todas las plataformas.';
    if (administradas.has(item.area.id)) return 'Administras esta área: tienes acceso automático.';
    if (item.my_level === 'admin') return 'Ya tienes el nivel más alto.';
    return 'No disponible para solicitar.';
  }

  function abrir(item: CatalogItem, trigger: HTMLButtonElement) {
    disparador.current = trigger;
    setAviso(null);
    setAbierta(item);
  }

  // Estable: `Modal` reinstala su efecto (y el foco) si cambia `onClose`.
  const cerrar = useCallback(() => {
    setAbierta(null);
    disparador.current?.focus();
  }, []);

  function creada(request: AccessRequest) {
    if (!abierta) return;
    setSolicitadas((prev) => ({ ...prev, [abierta.platform.id]: request.id }));
    setAviso(`Solicitud enviada: ${abierta.platform.name}, nivel ${NIVELES[request.level]}. Queda pendiente de aprobación.`);
    setAbierta(null);
    // El botón de la tarjeta desaparece: el foco va al aviso.
    requestAnimationFrame(() => avisoRef.current?.focus());
  }

  /** Al quitar el aviso, el foco va al buscador (no cae en `body`). */
  function cerrarAviso() {
    setAviso(null);
    document.getElementById(BUSCADOR_ID)?.focus();
  }

  const filtrando = Boolean(term.trim()) || areaId !== null;

  return (
    <section aria-labelledby="catalogo-titulo" className="space-y-6">
      <div>
        <h2 id="catalogo-titulo" className="text-xl font-semibold">Catálogo</h2>
        <p className="mt-1 text-sm text-label">
          {esSuperadmin
            ? 'Plataformas de todas las áreas. Como superadmin solo puedes consultarlas.'
            : 'Solicita acceso a las plataformas de tus áreas.'}
        </p>
      </div>

      <div role="status" ref={avisoRef} tabIndex={-1} className="rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-primary">
        {aviso ? (
          <Card>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm font-bold text-success-text">{aviso}</p>
              <Button variant="secondary" onClick={cerrarAviso}>Cerrar aviso</Button>
            </div>
          </Card>
        ) : null}
      </div>

      <div className="grid gap-3 sm:grid-cols-[1fr_auto]">
        <TextInput
          id={BUSCADOR_ID}
          type="search"
          value={term}
          onChange={(event) => setTerm(event.target.value)}
          placeholder="Buscar plataforma…"
          aria-label="Buscar en el catálogo"
        />
        <Select
          value={areaId ?? ''}
          onChange={(event) => setAreaId(event.target.value ? Number(event.target.value) : null)}
          aria-label="Filtrar el catálogo por área"
          className="sm:w-56"
        >
          <option value="">Todas las áreas</option>
          {areas.map((area) => (
            <option key={area.id} value={area.id}>{area.name}</option>
          ))}
        </Select>
      </div>

      {catalogo.loading && !catalogo.data ? <Spinner label="Cargando catálogo…" /> : null}

      {catalogo.error ? (
        <div className="space-y-3">
          <ErrorNote message={catalogo.error} />
          <Button variant="secondary" onClick={catalogo.reload}>Reintentar</Button>
        </div>
      ) : null}

      {catalogo.data && !catalogo.error ? (
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
                reason={puedeSolicitar(item) ? '' : motivo(item)}
                onRequest={abrir}
              />
            ))}
          </div>
        )
      ) : null}

      {abierta ? (
        <RequestFormModal item={abierta} onClose={cerrar} onCreated={creada} />
      ) : null}
    </section>
  );
}
