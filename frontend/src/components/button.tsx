import React from 'react';

export type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'fila' | 'fila-peligro';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  busy?: boolean;
}

export const CLASES_VARIANTE_BOTON: Record<ButtonVariant, string> = {
  primary: 'nexus-btn-primary',
  secondary: 'nexus-btn-secondary',
  danger: 'nexus-btn-danger',
  fila: 'nexus-btn-fila min-h-12 min-w-12 text-primary-text focus-visible:ring-primary',
  'fila-peligro': 'nexus-btn-fila-peligro min-h-12 min-w-12 text-error-text focus-visible:ring-primary',
};

/**
 * Componente Button unificado (DIS-058 / PLAN-FASE-7 §4.3).
 * Soporta variantes estándar (primary, secondary, danger, fila, fila-peligro),
 * tamaños de control, estado busy (aria-busy, aria-disabled y spinner accesible),
 * retención de foco accesible (aria-disabled no despoja el foco a document.body)
 * y foco visible con tokens de diseño.
 */
export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  {
    variant = 'primary',
    size = 'md',
    busy = false,
    className = '',
    children,
    disabled,
    onClick,
    ...props
  },
  ref,
) {
  const ariaDisabled = Boolean(props['aria-disabled']) || busy;
  const isDisabled = Boolean(disabled);
  const sizeClasses = size === 'sm' ? 'text-xs' : size === 'lg' ? 'text-sm' : '';

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (ariaDisabled || isDisabled) {
      e.preventDefault();
      return;
    }
    onClick?.(e);
  };

  return (
    <button
      ref={ref}
      type="button"
      {...props}
      disabled={isDisabled}
      aria-disabled={ariaDisabled ? 'true' : undefined}
      aria-busy={busy ? 'true' : props['aria-busy']}
      onClick={handleClick}
      className={`nexus-btn ${CLASES_VARIANTE_BOTON[variant]} ${sizeClasses} ${isDisabled || ariaDisabled ? 'estado-deshabilitado' : ''} ${className}`.trim()}
    >
      {busy ? (
        <span
          className="inline-block h-4 w-4 shrink-0 animate-spin rounded-full border-2 border-current border-t-transparent"
          aria-hidden="true"
        />
      ) : null}
      {children}
    </button>
  );
});

Button.displayName = 'Button';
