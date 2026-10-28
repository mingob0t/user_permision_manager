import React from 'react';
import Link, { type LinkProps } from 'next/link';
import { CLASES_VARIANTE_BOTON, type ButtonVariant, type ButtonSize } from './button';

export interface ButtonLinkProps extends Omit<React.AnchorHTMLAttributes<HTMLAnchorElement>, keyof LinkProps>, LinkProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
  className?: string;
  children?: React.ReactNode;
}

/**
 * Componente ButtonLink unificado (DIS-058 / PLAN-FASE-7 §4.3).
 * Renderiza un enlace de navegación con la misma apariencia y tokens
 * de interacción que Button.
 */
export const ButtonLink = React.forwardRef<HTMLAnchorElement, ButtonLinkProps>(function ButtonLink(
  {
    variant = 'primary',
    size = 'md',
    className = '',
    children,
    ...props
  },
  ref,
) {
  const sizeClasses = size === 'sm' ? 'text-xs' : size === 'lg' ? 'text-sm' : '';

  return (
    <Link
      ref={ref}
      {...props}
      className={`nexus-btn ${CLASES_VARIANTE_BOTON[variant]} ${sizeClasses} ${className}`.trim()}
    >
      {children}
    </Link>
  );
});

ButtonLink.displayName = 'ButtonLink';
