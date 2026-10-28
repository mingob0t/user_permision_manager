/**
 * Excepciones de la prueba «Un patrón, un componente» (DIS-068).
 *
 * Registra los archivos con marcado ad hoc heredado que deben ser
 * migrados a los componentes unificados durante los bloques C y D.
 *
 * Reglas auditadas:
 * - `table`: solo en DataTable (components/data-table.tsx)
 * - `nexus-btn`: solo en Button/ButtonLink (components/form.tsx o components/button.tsx)
 * - `h1`: solo en PageHeader (components/page-header.tsx)
 * - `role="tablist"`: solo en Tabs (components/tabs.tsx)
 * - `role="dialog"`: solo en Modal/Drawer (components/form.tsx o components/modal.tsx)
 */

export interface ExcepcionPatron {
  patron: 'table' | 'nexus-btn' | 'h1' | 'tablist' | 'dialog';
  cantidad: number;
  tarea: string;
  motivo: string;
}

export const EXCEPCIONES_PATRONES: Record<string, ExcepcionPatron[]> = {
  // Tablas fuera de data-table.tsx
  'components/dashboard.tsx': [
    {
      patron: 'table',
      cantidad: 1,
      tarea: 'DIS-071',
      motivo: 'Tabla accesible oculta (sr-only) para datos de gráfica; será migrada a DataTable en DIS-071',
    },
    {
      patron: 'h1',
      cantidad: 1,
      tarea: 'DIS-070',
      motivo: 'Encabezado h1 de vista; migrar a PageHeader en DIS-070',
    },
  ],
  'components/audit/platform-audit-history.tsx': [
    {
      patron: 'h1',
      cantidad: 1,
      tarea: 'DIS-070',
      motivo: 'Encabezado h1 de vista; migrar a PageHeader en DIS-070',
    },
  ],
  'components/audit/user-audit-history.tsx': [
    {
      patron: 'h1',
      cantidad: 1,
      tarea: 'DIS-070',
      motivo: 'Encabezado h1 de vista; migrar a PageHeader en DIS-070',
    },
  ],
  'components/access/my-requests-view.tsx': [
    {
      patron: 'h1',
      cantidad: 1,
      tarea: 'DIS-070',
      motivo: 'Encabezado h1 de vista; migrar a PageHeader en DIS-070',
    },
  ],
  'components/settings-panel.tsx': [
    {
      patron: 'h1',
      cantidad: 1,
      tarea: 'DIS-070',
      motivo: 'Encabezado h1 de vista; migrar a PageHeader en DIS-070',
    },
  ],
  // Diálogos manuales fuera de Modal / Drawer / AlertDialog
  'components/mobile-menu.tsx': [
    {
      patron: 'dialog',
      cantidad: 1,
      tarea: 'DIS-063',
      motivo: 'Menú móvil con role="dialog"; migrar a Drawer en DIS-061/DIS-063',
    },
  ],
  // h1 restantes en componentes y pantallas
  'components/login-form.tsx': [
    { patron: 'h1', cantidad: 1, tarea: 'DIS-063', motivo: 'Título en login; migrar a PageHeader en DIS-063/DIS-070' },
  ],
  'components/notifications-list.tsx': [
    { patron: 'h1', cantidad: 1, tarea: 'DIS-070', motivo: 'Encabezado h1; migrar a PageHeader en DIS-070' },
  ],
  'components/platform-admin.tsx': [
    { patron: 'h1', cantidad: 1, tarea: 'DIS-070', motivo: 'Encabezado h1; migrar a PageHeader en DIS-070' },
  ],
  'components/audit-log.tsx': [
    { patron: 'h1', cantidad: 1, tarea: 'DIS-070', motivo: 'Encabezado h1; migrar a PageHeader en DIS-070' },
  ],
  'components/areas-list.tsx': [
    { patron: 'h1', cantidad: 1, tarea: 'DIS-070', motivo: 'Encabezado h1; migrar a PageHeader en DIS-070' },
  ],
  'components/users-list.tsx': [
    { patron: 'h1', cantidad: 1, tarea: 'DIS-070', motivo: 'Encabezado h1; migrar a PageHeader en DIS-070' },
  ],
  'components/favorites-list.tsx': [
    { patron: 'h1', cantidad: 1, tarea: 'DIS-070', motivo: 'Encabezado h1; migrar a PageHeader en DIS-070' },
  ],
  'app/not-found.tsx': [
    { patron: 'h1', cantidad: 1, tarea: 'DIS-070', motivo: 'Encabezado h1; migrar a PageHeader en DIS-070' },
  ],
  'app/error.tsx': [
    { patron: 'h1', cantidad: 1, tarea: 'DIS-070', motivo: 'Encabezado h1; migrar a PageHeader en DIS-070' },
  ],
  'app/inventory/page.tsx': [
    { patron: 'h1', cantidad: 1, tarea: 'DIS-070', motivo: 'Encabezado h1; migrar a PageHeader en DIS-070' },
  ],
  'app/platforms/page.tsx': [
    { patron: 'h1', cantidad: 1, tarea: 'DIS-070', motivo: 'Encabezado h1; migrar a PageHeader en DIS-070' },
  ],
  'app/admin/jobs/page.tsx': [
    { patron: 'h1', cantidad: 1, tarea: 'DIS-070', motivo: 'Encabezado h1; migrar a PageHeader en DIS-070' },
  ],
  'app/admin/connectors/page.tsx': [
    { patron: 'h1', cantidad: 1, tarea: 'DIS-070', motivo: 'Encabezado h1; migrar a PageHeader en DIS-070' },
  ],
  'app/approvals/page.tsx': [
    { patron: 'h1', cantidad: 1, tarea: 'DIS-070', motivo: 'Encabezado h1; migrar a PageHeader en DIS-070' },
  ],
};
