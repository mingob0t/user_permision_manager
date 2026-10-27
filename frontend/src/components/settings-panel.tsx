'use client';

/** Configuración del sistema: contenedor con las pestañas de Ajustes. */

import { useRef, useState } from 'react';
import { destinoPorTecla } from './access/my-requests-view';
import { useSession } from './session-provider';
import { BackupTab } from './settings/backup-tab';
import { DirectoryTab } from './settings/directory-tab';
import { PortalTab } from './settings/portal-tab';
import { PreferencesTab } from './settings/preferences-tab';
import { SmtpTab } from './settings/smtp-tab';
import { type Tab, panelId, tabId } from './settings/settings-tabs';
import { TemplatesTab } from './settings/templates-tab';

export function SettingsPanel() {
  const { session } = useSession();
  const isAdmin = session?.permissions.is_admin ?? false;
  const [tab, setTab] = useState<Tab>(isAdmin ? 'portal' : 'preferences');
  const botones = useRef<(HTMLButtonElement | null)[]>([]);

  // La configuración del sistema es solo del superadmin; las preferencias, de
  // cada usuario.
  const tabs: { id: Tab; label: string }[] = [
    ...(isAdmin
      ? ([
          { id: 'portal', label: 'Portal' },
          { id: 'smtp', label: 'Correo' },
          { id: 'templates', label: 'Plantillas' },
          { id: 'ldap', label: 'Directorio' },
          { id: 'backup', label: 'Respaldo' },
        ] as { id: Tab; label: string }[])
      : []),
    { id: 'preferences', label: 'Mis preferencias' },
  ];

  // Activación automática: la flecha mueve el foco y selecciona la pestaña.
  function alPulsar(event: React.KeyboardEvent<HTMLButtonElement>, indice: number) {
    const destino = destinoPorTecla(event.key, indice, tabs.length);
    if (destino === null) return;
    event.preventDefault();
    setTab(tabs[destino].id);
    botones.current[destino]?.focus();
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Ajustes</h1>
        <p className="mt-1 text-sm text-label">
          {isAdmin
            ? 'Configuración del sistema y preferencias personales.'
            : 'Tus preferencias personales.'}
        </p>
      </div>

      {/* Teclado WAI-ARIA y 48 px de alto, como las pestañas de DIS-014 (DIS-034). */}
      <div className="flex flex-wrap gap-1 border-b border-panel-border" role="tablist" aria-label="Ajustes">
        {tabs.map((item, indice) => (
          <button
            key={item.id}
            ref={(el) => { botones.current[indice] = el; }}
            id={tabId(item.id)}
            type="button"
            role="tab"
            aria-selected={tab === item.id}
            aria-controls={panelId(item.id)}
            tabIndex={tab === item.id ? 0 : -1}
            onClick={() => setTab(item.id)}
            onKeyDown={(event) => alPulsar(event, indice)}
            className={`-mb-px min-h-12 border-b-2 px-3 py-3 text-sm transition-colors ${
              tab === item.id
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
        id={panelId(tab)}
        aria-labelledby={tabId(tab)}
        tabIndex={0}
        className="rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-primary"
      >
        {tab === 'portal' ? <PortalTab /> : null}
        {tab === 'smtp' ? <SmtpTab /> : null}
        {tab === 'templates' ? <TemplatesTab /> : null}
        {tab === 'ldap' ? <DirectoryTab /> : null}
        {tab === 'backup' ? <BackupTab /> : null}
        {tab === 'preferences' ? <PreferencesTab /> : null}
      </div>
    </div>
  );
}
