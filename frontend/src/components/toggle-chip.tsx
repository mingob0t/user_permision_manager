'use client';

/**
 * Componente ToggleChip unificado (DIS-060 / PLAN-FASE-7 §4.4).
 * Botón conmutador con aria-pressed:
 * - Selección múltiple o individual (etiquetas, filtros, favorito)
 * - Foco visible con tokens (focus-visible:ring-2 focus-visible:ring-primary)
 * - Área táctil mínima (min-h-12 min-w-12 = 48 px)
 * - Distinción de estado seleccionado con contraste no solo cromático (borde destacado)
 */

import React from 'react';

export type ToggleChipVariant = 'chip' | 'icon';

export interface ToggleChipProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  pressed: boolean;
  onPressedChange?: (pressed: boolean) => void;
  variant?: ToggleChipVariant;
}

export const ToggleChip = React.forwardRef<HTMLButtonElement, ToggleChipProps>(
  function ToggleChip(
    {
      pressed,
      onPressedChange,
      variant = 'chip',
      className = '',
      children,
      onClick,
      disabled,
      ...props
    },
    ref,
  ) {
    const isIcon = variant === 'icon';

    const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
      if (disabled) {
        e.preventDefault();
        return;
      }
      onPressedChange?.(!pressed);
      onClick?.(e);
    };

    const isAriaDisabled = props['aria-disabled'] === true || props['aria-disabled'] === 'true';
    const disabledStateClass = disabled || isAriaDisabled ? 'estado-deshabilitado' : '';

    const variantClasses = isIcon
      ? `inline-flex min-h-12 min-w-12 shrink-0 items-center justify-center rounded text-lg leading-none outline-none transition-colors hover:bg-surface-container focus-visible:ring-2 focus-visible:ring-primary ${disabledStateClass}`
      : `inline-flex min-h-12 min-w-12 items-center justify-center rounded-full border px-3 text-xs outline-none transition-colors focus-visible:ring-2 focus-visible:ring-primary ${
          pressed
            ? 'border-primary bg-primary/15 text-primary-text font-medium'
            : 'border-panel-border text-label hover:text-body-text'
        } ${disabledStateClass}`;

    return (
      <button
        ref={ref}
        type="button"
        aria-pressed={pressed}
        disabled={disabled}
        onClick={handleClick}
        className={`${variantClasses} ${className}`}
        {...props}
      >
        {children}
      </button>
    );
  },
);
