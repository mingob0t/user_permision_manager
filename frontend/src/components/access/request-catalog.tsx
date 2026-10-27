'use client';

/**
 * Catálogo solicitable (DIS-013, F-SOL-01/02, `GET /access-requests/catalog`):
 * plataformas de las áreas del usuario con su estado y la solicitud de nivel.
 *
 * - El catálogo no se pagina (acotado por áreas, contrato 1.1): el filtro por
 *   área y la búsqueda se resuelven en el cliente con una sola carga.
 * - DIS-030: con `mias` (las plataformas que ya puede abrir, `GET /platforms`) es
 *   la vista única del catálogo: cada tarjeta suma enlace y favorito, y las
 *   abribles que el catálogo no trae se agregan. Sin `mias` se comporta como antes.
 * - Tras solicitar, la tarjeta pasa a "pendiente" sin recargar y el resultado
 *   se anuncia en una región `status` que recibe el foco.
 */

import { useCallback, useMemo, useRef, useState } from 'react';
import type { AccessRequest, CatalogItem } from '@/lib/access/types';
import { useSession } from '../session-provider';
import { NIVELES } from './access-status-badge';
import { BUSCADOR_ID, CatalogFilters, filtrarCatalogo } from './catalog-filters';
import { CatalogGrid } from './catalog-grid';
import { CatalogNotice } from './catalog-notice';
import { RequestFormModal } from './request-form-modal';
import { useCatalogoSolicitable, type MisPlataformas } from './use-catalogo-solicitable';

export type { MisPlataformas };

export function RequestCatalog({ mias }: { mias?: MisPlataformas } = {}) {
  const { session } = useSession();
  const esSuperadmin = session?.permissions.is_admin ?? false;
  const administradas = useMemo(
    () => new Set((session?.managed_areas ?? []).map((a) => a.id)),
    [session],
  );

  const [areaId, setAreaId] = useState<number | null>(null);
  const [term, setTerm] = useState('');
  const [abierta, setAbierta] = useState<CatalogItem | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const disparador = useRef<HTMLElement | null>(null);
  const avisoRef = useRef<HTMLDivElement>(null);

  const { catalogo, items, areas, mias: abribles, marcarSolicitada } = useCatalogoSolicitable(mias);
  const shown = useMemo(() => filtrarCatalogo(items, areaId, term), [items, areaId, term]);

  function motivo(item: CatalogItem): string {
    if (item.pending_request_id !== null) return 'Espera la decisión del administrador del área.';
    if (esSuperadmin) return 'Como superadmin ya tienes acceso a todas las plataformas.';
    if (administradas.has(item.area.id)) return 'Administras esta área: tienes acceso automático.';
    if (item.my_level === 'admin') return 'Ya tienes el nivel más alto.';
    if (abribles.has(item.platform.id)) return '';
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
    marcarSolicitada(abierta.platform.id, request.id);
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
            : mias
              ? 'Abre tus plataformas y solicita acceso a las de tus áreas.'
              : 'Solicita acceso a las plataformas de tus áreas.'}
        </p>
      </div>

      <CatalogNotice aviso={aviso} onClose={cerrarAviso} regionRef={avisoRef} />

      <CatalogFilters
        term={term}
        onTermChange={setTerm}
        areaId={areaId}
        onAreaChange={setAreaId}
        areas={areas}
      />

      <CatalogGrid
        catalogo={catalogo}
        mias={mias}
        shown={shown}
        filtrando={filtrando}
        mine={abribles}
        motivo={motivo}
        onRequest={abrir}
      />

      {abierta ? (
        <RequestFormModal item={abierta} onClose={cerrar} onCreated={creada} />
      ) : null}
    </section>
  );
}
