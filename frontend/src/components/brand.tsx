import React from 'react';

/**
 * Identidad visual del portal (DIS-063).
 *
 * Muestra el nombre y descripción del portal sin inventar marcas ni cargar
 * imágenes externas, con dimensiones estables para evitar saltos de diseño (CLS = 0).
 */
export function Brand({
  subtitle = false,
  size = 'md',
  className = '',
}: {
  subtitle?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}) {
  const sizeClasses = {
    sm: 'text-base font-semibold',
    md: 'text-lg font-semibold',
    lg: 'text-2xl font-semibold',
  };

  return (
    <div className={`flex flex-col select-none ${className}`}>
      <span className={`tracking-tight text-body-text ${sizeClasses[size]}`}>Nexus</span>
      {subtitle ? (
        <span className="text-xs text-label">
          Catálogo centralizado de plataformas
        </span>
      ) : null}
    </div>
  );
}
