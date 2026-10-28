'use client';

/**
 * Componente Tabs unificado (DIS-060 / PLAN-FASE-7 §4.4).
 * Cumple WAI-ARIA tablist:
 * - roving tabindex (solo la pestaña activa tiene tabIndex=0)
 * - navegación con teclado (ArrowRight, ArrowLeft, Home, End)
 * - activación automática al navegar por flechas
 * - área táctil mínima (min-h-12 = 48 px)
 * - foco visible con tokens de diseño
 * - indicador seleccionado no cromático (borde-b-2 >= 3:1)
 */

import React, { useRef } from 'react';

export function destinoPorTecla(tecla: string, actual: number, total: number): number | null {
  if (total <= 0) return null;
  switch (tecla) {
    case 'ArrowRight':
      return (actual + 1) % total;
    case 'ArrowLeft':
      return (actual - 1 + total) % total;
    case 'Home':
      return 0;
    case 'End':
      return total - 1;
    default:
      return null;
  }
}

export interface TabItem<T extends string = string> {
  id: T;
  label: React.ReactNode;
  disabled?: boolean;
}

export interface TabsProps<T extends string = string> {
  tabs: TabItem<T>[];
  value: T;
  onChange: (id: T) => void;
  ariaLabel?: string;
  ariaLabelledby?: string;
  getTabId?: (id: T) => string;
  getPanelId?: (id: T) => string;
  className?: string;
}

export function Tabs<T extends string = string>({
  tabs,
  value,
  onChange,
  ariaLabel,
  ariaLabelledby,
  getTabId,
  getPanelId,
  className = '',
}: TabsProps<T>) {
  const botones = useRef<(HTMLButtonElement | null)[]>([]);

  const alPulsar = (event: React.KeyboardEvent<HTMLButtonElement>, indice: number) => {
    const destino = destinoPorTecla(event.key, indice, tabs.length);
    if (destino === null) return;
    event.preventDefault();
    const itemDestino = tabs[destino];
    if (itemDestino.disabled) return;
    onChange(itemDestino.id);
    botones.current[destino]?.focus();
  };

  return (
    <div
      className={`flex flex-wrap gap-1 border-b border-panel-border ${className}`}
      role="tablist"
      aria-label={ariaLabel}
      aria-labelledby={ariaLabelledby}
    >
      {tabs.map((item, indice) => {
        const isSelected = value === item.id;
        const idProp = getTabId ? getTabId(item.id) : `${item.id}-tab`;
        const panelProp = getPanelId ? getPanelId(item.id) : `${item.id}-panel`;

        return (
          <button
            key={item.id}
            ref={(el) => {
              botones.current[indice] = el;
            }}
            id={idProp}
            type="button"
            role="tab"
            aria-selected={isSelected}
            aria-controls={panelProp}
            tabIndex={isSelected ? 0 : -1}
            disabled={item.disabled}
            onClick={() => !item.disabled && onChange(item.id)}
            onKeyDown={(event) => alPulsar(event, indice)}
            className={`-mb-px min-h-12 border-b-2 px-3 py-3 text-sm outline-none transition-colors focus-visible:ring-2 focus-visible:ring-primary ${
              isSelected
                ? 'border-primary font-medium text-primary-text'
                : 'border-transparent text-label hover:text-body-text'
            } ${item.disabled ? 'estado-deshabilitado pointer-events-none' : ''}`}
          >
            {item.label}
          </button>
        );
      })}
    </div>
  );
}

export interface TabPanelProps extends React.HTMLAttributes<HTMLDivElement> {
  id: string;
  tabId: string;
  children: React.ReactNode;
}

export function TabPanel({ id, tabId, children, className = '', ...props }: TabPanelProps) {
  return (
    <div
      role="tabpanel"
      id={id}
      aria-labelledby={tabId}
      tabIndex={0}
      className={`rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-primary ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}
