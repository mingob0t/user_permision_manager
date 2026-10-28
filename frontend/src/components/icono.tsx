import React from 'react';

export type NombreIcono =
  | 'cerrar'
  | 'marca'
  | 'favorito'
  | 'exito'
  | 'error'
  | 'aviso'
  | 'info'
  | 'pregunta';

export type TamanoIcono = 'sm' | 'md' | 'lg';

interface IconoProps {
  nombre: NombreIcono;
  tamano?: TamanoIcono;
  className?: string;
  ariaLabel?: string;
  ariaHidden?: boolean;
}

const DIMENSIONES: Record<TamanoIcono, { width: number; height: number; clase: string }> = {
  sm: { width: 16, height: 16, clase: 'w-4 h-4' },
  md: { width: 20, height: 20, clase: 'w-5 h-5' },
  lg: { width: 24, height: 24, clase: 'w-6 h-6' },
};

export const Icono: React.FC<IconoProps> = ({
  nombre,
  tamano = 'md',
  className = '',
  ariaLabel,
  ariaHidden,
}) => {
  const dim = DIMENSIONES[tamano] ?? DIMENSIONES.md;
  const oculto = ariaHidden ?? !ariaLabel;

  const renderPath = () => {
    switch (nombre) {
      case 'cerrar':
        return (
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M6 18L18 6M6 6l12 12"
          />
        );
      case 'marca':
        return (
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M13 10V3L4 14h7v7l9-11h-7z"
          />
        );
      case 'favorito':
        return (
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
          />
        );
      case 'exito':
        return (
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        );
      case 'error':
        return (
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        );
      case 'aviso':
        return (
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        );
      case 'info':
        return (
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        );
      case 'pregunta':
        return (
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        );
    }
  };

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      width={dim.width}
      height={dim.height}
      className={`inline-block shrink-0 ${dim.clase} ${className}`}
      aria-hidden={oculto}
      aria-label={ariaLabel}
      role={ariaLabel ? 'img' : undefined}
    >
      {renderPath()}
    </svg>
  );
};
