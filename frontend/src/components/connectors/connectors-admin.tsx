'use client';

/**
 * Pantalla Conectores (DIS-022, F-CON-01; ruta `/admin/connectors`, guarda
 * `admin`): plataformas que usan conector con su configuración y, debajo, la
 * bitácora de ejecuciones.
 *
 * - Plataformas de `GET /platforms` con `integration_type` `conector`;
 *   `has_connector` dice si ya tienen configuración (sin una petición por fila).
 * - "Configurar" abre `ConnectorPanel` bajo la lista; al cerrarlo el foco
 *   vuelve al botón de la fila.
 */

import { useCallback, useState } from 'react';
import { api } from '@/lib/api';
import type { Platform } from '@/lib/types';
import { useAsync } from '@/lib/use-async';
import { listLoadError } from '../access/request-errors';
import { Button } from '../form';
import { EmptyNote, ErrorNote, Spinner } from '../ui';
import { ConnectorList, botonConfigurarId, plataformasConConector } from './connector-list';
import { ConnectorPanel } from './connector-panel';
import { JobsLog } from './jobs-log';

export const VACIO_CONECTORES =
  'Ninguna plataforma usa conector. Elige el tipo de integración "conector" en Administrar plataformas.';

export function ConnectorsAdmin() {
  const lista = useAsync(
    () => api.platforms().catch((err: unknown) => { throw listLoadError(err, 'las plataformas'); }),
    [],
  );
  const [seleccionadaId, setSeleccionadaId] = useState<number | null>(null);

  const plataformas = plataformasConConector(lista.data ?? []);
  const seleccionada = plataformas.find((p) => p.id === seleccionadaId) ?? null;

  const cerrar = useCallback(() => {
    const id = seleccionadaId;
    setSeleccionadaId(null);
    if (id !== null) requestAnimationFrame(() => document.getElementById(botonConfigurarId(id))?.focus());
  }, [seleccionadaId]);

  return (
    <div className="space-y-8">
      <section aria-labelledby="conectores-titulo" className="space-y-4">
        <div>
          <h2 id="conectores-titulo" className="text-lg font-semibold">Plataformas con conector</h2>
          <p className="text-sm text-label">
            La credencial se indica con la referencia del ítem en el gestor de secretos; el portal
            nunca pide ni muestra la contraseña.
          </p>
        </div>

        {lista.loading && !lista.data ? <Spinner label="Cargando las plataformas…" /> : null}

        {lista.error ? (
          <div className="space-y-3">
            <ErrorNote message={lista.error} />
            <Button variant="secondary" onClick={lista.reload}>Reintentar</Button>
          </div>
        ) : null}

        {lista.data ? (
          plataformas.length === 0 ? (
            <EmptyNote message={VACIO_CONECTORES} />
          ) : (
            <ConnectorList
              plataformas={plataformas}
              seleccionada={seleccionadaId}
              onSelect={(p: Platform) => setSeleccionadaId(p.id)}
            />
          )
        ) : null}

        {seleccionada ? (
          <ConnectorPanel platform={seleccionada} onClose={cerrar} onChanged={lista.reload} />
        ) : null}
      </section>

      <JobsLog />
    </div>
  );
}
