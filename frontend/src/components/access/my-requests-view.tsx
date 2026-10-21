'use client';

/**
 * Pantalla `/requests` (DIS-014): pestañas "Mis solicitudes" y "Mis accesos".
 *
 * El superadmin no solicita ni tiene accesos propios (contratos: `mine` y
 * `/me/access` le responden vacío): ve un estado vacío explicado y no se
 * llama a la API.
 */

import { useState } from 'react';
import { useSession } from '../session-provider';
import { EmptyNote, ErrorNote, Spinner } from '../ui';
import { MyAccess } from './my-access';
import { MyRequests } from './my-requests';

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
  const [pestana, setPestana] = useState<Pestana>('solicitudes');

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
          {/* Mismas clases que las pestañas de Ajustes (`settings-panel.tsx`). */}
          <div
            className="flex flex-wrap gap-1 border-b border-panel-border"
            role="tablist"
            aria-label="Mis solicitudes y accesos"
          >
            {PESTANAS.map((item) => (
              <button
                key={item.id}
                id={tabId(item.id)}
                type="button"
                role="tab"
                aria-selected={pestana === item.id}
                aria-controls={panelId(item.id)}
                onClick={() => setPestana(item.id)}
                className={`-mb-px border-b-2 px-3 py-2 text-sm transition-colors ${
                  pestana === item.id
                    ? 'border-primary font-medium text-primary-text'
                    : 'border-transparent text-label hover:text-body-text'
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>

          <div role="tabpanel" id={panelId(pestana)} aria-labelledby={tabId(pestana)}>
            {pestana === 'solicitudes' ? <MyRequests /> : <MyAccess />}
          </div>
        </>
      )}
    </div>
  );
}
