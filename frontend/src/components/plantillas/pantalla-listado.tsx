'use client';

/**
 * Plantilla de pantalla de listado (DIS-070 / PLAN-FASE-7 §4.5).
 *
 * Estructura estándar:
 * Encabezado (PageHeader) → Barra de filtros (FilterBar) → Zona de avisos (RegionDeAviso)
 * → Estados (carga con Skeleton, vacío con EmptyNote, error) → Contenido (DataTable / List)
 * → Paginador (ListPager).
 */

import React from 'react';
import { PageHeader, type PageHeaderProps } from '../page-header';
import { EmptyNote, ErrorNote, RegionDeAviso, Skeleton } from '../ui';

export interface PantallaListadoProps {
  header?: React.ReactNode;
  headerProps?: PageHeaderProps;
  filters?: React.ReactNode;
  error?: string | null;
  loading?: boolean;
  empty?: boolean;
  emptyMessage?: string;
  emptyAction?: React.ReactNode;
  pager?: React.ReactNode;
  skeletonCount?: number;
  children: React.ReactNode;
  className?: string;
}

export function PantallaListado({
  header,
  headerProps,
  filters,
  error,
  loading = false,
  empty = false,
  emptyMessage = 'No se encontraron elementos.',
  emptyAction,
  pager,
  skeletonCount = 5,
  children,
  className = '',
}: PantallaListadoProps) {
  return (
    <div className={`mx-auto max-w-contenido space-y-6 ${className}`}>
      {header ?? (headerProps ? <PageHeader {...headerProps} /> : null)}

      {filters ? <div className="shrink-0">{filters}</div> : null}

      <RegionDeAviso minHeight="min-h-6">
        {error ? <ErrorNote message={error} /> : null}
      </RegionDeAviso>

      {loading ? (
        <Skeleton variant="fila" count={skeletonCount} ariaLabel="Cargando listado…" />
      ) : empty ? (
        <div className="py-8">
          <EmptyNote message={emptyMessage} action={emptyAction} />
        </div>
      ) : (
        <div className="space-y-4">
          {children}
          {pager ? <div className="pt-2">{pager}</div> : null}
        </div>
      )}
    </div>
  );
}
