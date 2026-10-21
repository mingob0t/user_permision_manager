'use client';

/**
 * Pantalla `/requests` (DIS-014): pestañas "Mis solicitudes" y "Mis accesos".
 *
 * El superadmin no solicita ni tiene accesos propios (contratos: `mine` y
 * `/me/access` le responden vacío): ve un estado vacío explicado y no se
 * llama a la API.
 */

import { useRef, useState } from 'react';
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

/** Teclas del patrón WAI-ARIA de pestañas: índice destino o `null`. */
export function destinoPorTecla(tecla: string, actual: number, total: number): number | null {
  switch (tecla) {
    case 'ArrowRight': return (actual + 1) % total;
    case 'ArrowLeft': return (actual - 1 + total) % total;
    case 'Home': return 0;
    case 'End': return total - 1;
    default: return null;
  }
}
const panelId = (id: Pestana) => `mis-${id}-panel`;

export function MyRequestsView() {
  const { session, loading, error } = useSession();
  const [pestana, setPestana] = useState<Pestana>('solicitudes');
  const botones = useRef<(HTMLButtonElement | null)[]>([]);

  if (loading) return <Spinner label="Cargando sesión…" />;
  if (error) return <ErrorNote message={error} />;
  if (!session) return null;

  const esSuperadmin = session.permissions.is_admin;

  // Activación automática: la flecha mueve el foco y selecciona la pestaña.
  function alPulsar(event: React.KeyboardEvent<HTMLButtonElement>, indice: number) {
    const destino = destinoPorTecla(event.key, indice, PESTANAS.length);
    if (destino === null) return;
    event.preventDefault();
    setPestana(PESTANAS[destino].id);
    botones.current[destino]?.focus();
  }

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
          {/* Clases de las pestañas de Ajustes (`settings-panel.tsx`) más 48 px de alto y teclado WAI-ARIA. */}
          <div
            className="flex flex-wrap gap-1 border-b border-panel-border"
            role="tablist"
            aria-label="Mis solicitudes y accesos"
          >
            {PESTANAS.map((item, indice) => (
              <button
                key={item.id}
                ref={(el) => { botones.current[indice] = el; }}
                id={tabId(item.id)}
                type="button"
                role="tab"
                aria-selected={pestana === item.id}
                aria-controls={panelId(item.id)}
                tabIndex={pestana === item.id ? 0 : -1}
                onClick={() => setPestana(item.id)}
                onKeyDown={(event) => alPulsar(event, indice)}
                className={`-mb-px min-h-12 border-b-2 px-3 py-3 text-sm transition-colors ${
                  pestana === item.id
                    ? 'border-primary font-medium text-primary-text'
                    : 'border-transparent text-label hover:text-body-text'
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>

          <div
            role="tabpanel"
            id={panelId(pestana)}
            aria-labelledby={tabId(pestana)}
            tabIndex={0}
            className="rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            {pestana === 'solicitudes' ? <MyRequests /> : <MyAccess />}
          </div>
        </>
      )}
    </div>
  );
}
