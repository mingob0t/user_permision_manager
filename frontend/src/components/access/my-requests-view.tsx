'use client';

/**
 * Pantalla `/requests` (DIS-014): pestañas "Mis solicitudes" y "Mis accesos".
 *
 * El superadmin no solicita ni tiene accesos propios (contratos: `mine` y
 * `/me/access` le responden vacío): ve un estado vacío explicado y no se
 * llama a la API.
 */

import { useSearchParams } from 'next/navigation';
import { useState } from 'react';
import { useSession } from '../session-provider';
import { Tabs, TabPanel, destinoPorTecla } from '../tabs';
import { EmptyNote, ErrorNote, Spinner } from '../ui';
import { valorPermitido } from './filtro-url';
import { FILTROS, MyAccess } from './my-access';
import { ESTADOS, MyRequests } from './my-requests';

export { destinoPorTecla };

type Pestana = 'solicitudes' | 'accesos';

const PESTANAS: { id: Pestana; label: string }[] = [
  { id: 'solicitudes', label: 'Mis solicitudes' },
  { id: 'accesos', label: 'Mis accesos' },
];

export const MENSAJE_SUPERADMIN =
  'Como superadmin tienes acceso a todas las plataformas: no solicitas accesos ni tienes accesos propios que revisar aquí.';

const tabId = (id: Pestana) => `mis-${id}-pestana`;
const panelId = (id: Pestana) => `mis-${id}-panel`;

export function MyRequestsView() {
  const { session, loading, error } = useSession();
  // Pestaña y estado que llegan por la URL (DIS-036); lo inválido se ignora.
  const params = useSearchParams();
  const [inicial] = useState(() => ({
    pestana: valorPermitido(params?.get('tab'), PESTANAS.map((p) => p.id)) ?? 'solicitudes',
    solicitud: valorPermitido(params?.get('status'), ESTADOS),
    acceso: valorPermitido(params?.get('status'), FILTROS.map((f) => f.valor)),
  }));
  const [pestana, setPestana] = useState<Pestana>(inicial.pestana);

  if (loading) return <Spinner label="Cargando sesión…" />;
  if (error) return <ErrorNote message={error} />;
  if (!session) return null;

  const esSuperadmin = session.permissions.is_admin;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Mis solicitudes y accesos</h1>
        <p className="mt-1 text-sm text-label">
          El estado de tus solicitudes y de los accesos que ya tienes.
        </p>
      </div>

      {esSuperadmin ? (
        <EmptyNote message={MENSAJE_SUPERADMIN} />
      ) : (
        <>
          <Tabs
            tabs={PESTANAS}
            value={pestana}
            onChange={setPestana}
            ariaLabel="Mis solicitudes y accesos"
            getTabId={tabId}
            getPanelId={panelId}
          />

          <TabPanel id={panelId(pestana)} tabId={tabId(pestana)}>
            {pestana === 'solicitudes'
              ? <MyRequests estadoInicial={inicial.pestana === 'solicitudes' ? inicial.solicitud : undefined} />
              : <MyAccess estadoInicial={inicial.pestana === 'accesos' ? inicial.acceso : undefined} />}
          </TabPanel>
        </>
      )}
    </div>
  );
}
