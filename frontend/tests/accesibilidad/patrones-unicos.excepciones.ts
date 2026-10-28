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
  // 0 excepciones: 100% de tablas, botones, h1, tablists y diálogos usan componentes unificados (DIS-067).
};

