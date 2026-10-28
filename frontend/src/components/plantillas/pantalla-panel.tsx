'use client';

/**
 * Plantilla de pantalla de panel de control o inicio (DIS-070 / PLAN-FASE-7 §4.5).
 *
 * Estructura estándar:
 * PageHeader → Zona de avisos → Rejilla de métricas / tarjetas (StatTile / Card)
 * → Bloques de contenido y estados por bloque.
 */

import React from 'react';
import { PageHeader, type PageHeaderProps } from '../page-header';
import { ErrorNote, RegionDeAviso, Skeleton } from '../ui';

export interface PantallaPanelProps {
  header?: React.ReactNode;
  headerProps?: PageHeaderProps;
  stats?: React.ReactNode;
  error?: string | null;
  loading?: boolean;
  children?: React.ReactNode;
  className?: string;
}

export function PantallaPanel({
  header,
  headerProps,
  stats,
  error,
  loading = false,
  children,
  className = '',
}: PantallaPanelProps) {
  return (
    <div className={`mx-auto max-w-contenido space-y-6 ${className}`}>
      {header ?? (headerProps ? <PageHeader {...headerProps} /> : null)}

      <RegionDeAviso minHeight="min-h-6">
        {error ? <ErrorNote message={error} /> : null}
      </RegionDeAviso>

      {loading ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Skeleton variant="contador" count={4} ariaLabel="Cargando métricas…" />
          </div>
          <Skeleton variant="tarjeta" count={2} ariaLabel="Cargando paneles…" />
        </div>
      ) : (
        <div className="space-y-6">
          {stats ? <div className="shrink-0">{stats}</div> : null}
          {children}
        </div>
      )}
    </div>
  );
}
