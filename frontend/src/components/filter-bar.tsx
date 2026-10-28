/**
 * Barra de filtros común y unificada (DIS-010, DIS-069, ADR-007).
 *
 * Responsabilidad:
 * - Unificar todas las barras de filtros bajo una misma región semántica (`role="search"`).
 * - Alturas de control estandarizadas a `control-alto` (h-12 / min-h-12).
 * - Rejilla uniforme (`FilterBarGrid`) y formulario de búsqueda (`FilterBarSearch`).
 * - Acción de limpiar filtros (`FilterBarClear`).
 * - Zona reservada para errores de validación de rango (`FilterBarError`, `min-h-5`) que previene saltos CLS.
 *
 * Solo tokens de diseño; cumple con el sistema 8pt.
 */

import React from 'react';
import { Button } from './form';

/** Clases para que un `TextInput` de búsqueda ocupe el espacio libre de la barra. */
export const FILTRO_BUSQUEDA = 'min-w-56 flex-1';

/** Clases para que un `Select` de la barra no ocupe toda la fila desde `sm`. */
export const FILTRO_SELECTOR = 'sm:w-auto';

export interface FilterBarProps {
  /** Nombre accesible de la barra (p. ej. "Filtros de plataformas"). */
  label: string;
  children: React.ReactNode;
  className?: string;
  layout?: 'row' | 'stack';
  error?: string | null;
  errorId?: string;
}

export function FilterBar({
  label,
  children,
  className = '',
  layout = 'row',
  error,
  errorId,
}: FilterBarProps) {
  const baseLayout = layout === 'row' ? 'flex flex-wrap items-center gap-3' : 'space-y-3';

  return (
    <div role="search" aria-label={label} className={`${baseLayout} ${className}`}>
      {children}
      {error ? (
        <div className="w-full min-h-5">
          <p id={errorId} role="alert" className="text-sm font-bold text-error-text">
            {error}
          </p>
        </div>
      ) : null}
    </div>
  );
}

/** Rejilla estándar para selectores y campos de filtros (2 col en sm, 3 col en lg). */
export function FilterBarGrid({
  children,
  className = '',
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`grid gap-3 sm:grid-cols-2 lg:grid-cols-3 ${className}`}>
      {children}
    </div>
  );
}

/** Formulario de búsqueda con botón de envío a control-alto (min-h-12). */
export function FilterBarSearch({
  onSubmit,
  children,
  className = '',
  buttonLabel = 'Buscar',
}: {
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
  children: React.ReactNode;
  className?: string;
  buttonLabel?: string;
}) {
  return (
    <form onSubmit={onSubmit} className={`grid gap-3 sm:grid-cols-[1fr_auto] ${className}`}>
      {children}
      <Button type="submit" variant="secondary" className="min-h-12 min-w-12 px-5">
        {buttonLabel}
      </Button>
    </form>
  );
}

/** Botón accesible para reiniciar o limpiar filtros activos. */
export function FilterBarClear({
  onClear,
  disabled = false,
  label = 'Limpiar filtros',
  className = '',
}: {
  onClear: () => void;
  disabled?: boolean;
  label?: string;
  className?: string;
}) {
  return (
    <Button
      variant="secondary"
      onClick={onClear}
      disabled={disabled}
      className={`min-h-12 min-w-12 ${className}`}
    >
      {label}
    </Button>
  );
}

/**
 * Zona reservada para mensajes de error de filtros (p. ej. rango de fechas invertido),
 * manteniendo altura fija `min-h-5` para evitar Cumulative Layout Shift (CLS).
 */
export function FilterBarError({
  id,
  message,
}: {
  id?: string;
  message?: string | null;
}) {
  return (
    <div className="min-h-5">
      {message ? (
        <p id={id} role="alert" className="text-sm font-bold text-error-text">
          {message}
        </p>
      ) : null}
    </div>
  );
}
