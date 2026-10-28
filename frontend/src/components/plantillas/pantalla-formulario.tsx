'use client';

/**
 * Plantilla de pantalla de formulario (DIS-070 / PLAN-FASE-7 §4.5).
 *
 * Estructura estándar:
 * PageHeader (+ volver opcional) → Zona de avisos → Formulario dentro de ancho formulario-max
 * → Secciones de campos → Barra de acciones (primaria a la derecha).
 */

import React from 'react';
import { PageHeader, type PageHeaderProps } from '../page-header';
import { ErrorNote, RegionDeAviso, Skeleton } from '../ui';

export interface PantallaFormularioProps {
  header?: React.ReactNode;
  headerProps?: PageHeaderProps;
  error?: string | null;
  loading?: boolean;
  onSubmit?: (e: React.FormEvent) => void;
  actions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export function PantallaFormulario({
  header,
  headerProps,
  error,
  loading = false,
  onSubmit,
  actions,
  children,
  className = '',
}: PantallaFormularioProps) {
  return (
    <div className={`mx-auto max-w-formulario space-y-6 ${className}`}>
      {header ?? (headerProps ? <PageHeader {...headerProps} /> : null)}

      <RegionDeAviso minHeight="min-h-6">
        {error ? <ErrorNote message={error} /> : null}
      </RegionDeAviso>

      {loading ? (
        <div className="space-y-4">
          <Skeleton variant="tarjeta" ariaLabel="Cargando formulario…" />
        </div>
      ) : (
        <form onSubmit={onSubmit} className="space-y-6">
          <div className="space-y-4">{children}</div>
          {actions ? (
            <div className="flex flex-wrap items-center justify-end gap-3 pt-4 border-t border-panel-border">
              {actions}
            </div>
          ) : null}
        </form>
      )}
    </div>
  );
}
