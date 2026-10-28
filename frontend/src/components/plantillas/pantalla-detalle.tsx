'use client';

/**
 * Plantilla de pantalla de detalle (DIS-070 / PLAN-FASE-7 §4.5).
 *
 * Estructura estándar:
 * PageHeader (+ volver) → Zona de avisos → Resumen (Card / DataList) → Secciones → Estados.
 */

import React from 'react';
import { PageHeader, type PageHeaderProps } from '../page-header';
import { ErrorNote, RegionDeAviso, Skeleton } from '../ui';

export interface PantallaDetalleProps {
  header?: React.ReactNode;
  headerProps?: PageHeaderProps;
  summary?: React.ReactNode;
  error?: string | null;
  loading?: boolean;
  children?: React.ReactNode;
  className?: string;
}

export function PantallaDetalle({
  header,
  headerProps,
  summary,
  error,
  loading = false,
  children,
  className = '',
}: PantallaDetalleProps) {
  return (
    <div className={`mx-auto max-w-contenido space-y-6 ${className}`}>
      {header ?? (headerProps ? <PageHeader {...headerProps} /> : null)}

      <RegionDeAviso minHeight="min-h-6">
        {error ? <ErrorNote message={error} /> : null}
      </RegionDeAviso>

      {loading ? (
        <div className="space-y-6">
          <Skeleton variant="tarjeta" ariaLabel="Cargando resumen…" />
          <Skeleton variant="fila" count={4} ariaLabel="Cargando secciones…" />
        </div>
      ) : (
        <div className="space-y-6">
          {summary ? <div className="shrink-0">{summary}</div> : null}
          {children}
        </div>
      )}
    </div>
  );
}
