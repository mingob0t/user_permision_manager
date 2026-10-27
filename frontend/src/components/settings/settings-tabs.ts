/** Identificadores de las pestañas de Ajustes y de los ids ARIA que las enlazan con su panel. */

export type Tab = 'portal' | 'smtp' | 'templates' | 'ldap' | 'backup' | 'preferences';

export const tabId = (id: Tab) => `ajustes-${id}-pestana`;
export const panelId = (id: Tab) => `ajustes-${id}-panel`;
