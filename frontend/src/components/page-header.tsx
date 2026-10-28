'use client';

/**
 * Encabezado canónico de pantalla (DIS-070 / PLAN-FASE-7 §4.5).
 *
 * Único componente autorizado para renderizar `<h1>` en el portal (DIS-068).
 * Admite título, descripción opcional, acciones a la derecha, botón volver
 * y ref para foco accesible tras navegación o cambios de vista.
 */

import React from 'react';
import { ButtonLink } from './form';

export interface PageHeaderProps {
  title: React.ReactNode;
  description?: React.ReactNode;
  actions?: React.ReactNode;
  backHref?: string;
  backLabel?: string;
  h1Ref?: React.Ref<HTMLHeadingElement>;
  className?: string;
}

export function PageHeader({
  title,
  description,
  actions,
  backHref,
  backLabel = 'Volver',
  h1Ref,
  className = '',
}: PageHeaderProps) {
  return (
    <header className={`flex flex-col gap-4 pb-6 sm:flex-row sm:items-center sm:justify-between ${className}`}>
      <div className="min-w-0 flex-1">
        {backHref ? (
          <div className="mb-2">
            <ButtonLink href={backHref} variant="secondary" className="min-h-9 px-3 text-xs">
              ← {backLabel}
            </ButtonLink>
          </div>
        ) : null}
        <h1
          ref={h1Ref}
          tabIndex={-1}
          className="text-2xl font-bold tracking-tight text-body-text outline-none"
        >
          {title}
        </h1>
        {description ? (
          <p className="mt-1 text-sm text-label">{description}</p>
        ) : null}
      </div>
      {actions ? (
        <div className="flex shrink-0 flex-wrap items-center gap-3">
          {actions}
        </div>
      ) : null}
    </header>
  );
}
