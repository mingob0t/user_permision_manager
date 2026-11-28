/** Columnas de la tabla de Administrar plataformas (DIS-010, DIS-035). */

import Link from 'next/link';
import type { Platform } from '@/lib/types';
import { enlaceSeguro } from '@/lib/enlace-seguro';
import { atributoTexto, variablesChipPlataforma } from '@/lib/color-legible';
import { variablesCss } from '@/lib/variables-css';
import type { DataColumn } from '../data-table';
import { EstadoBadgeBoton } from '../estado-badge-boton';
import { Badge } from '../ui';
import { rutaConFiltro } from '../access/filtro-url';

/** Ruta del Historial de solicitudes (`RUTA_SOLICITUDES`); aquí sin importar el Resumen y sus gráficas. */
const RUTA_SOLICITUDES = '/approvals';

/** DIS-161: Historial con las pendientes de la plataforma (filtro de área y plataforma). */
export function rutaPendientesPlataforma(platform: Pick<Platform, 'id' | 'area_id'>): string {
  return rutaConFiltro(RUTA_SOLICITUDES, {
    status: 'pendiente',
    area_id: String(platform.area_id),
    platform_id: String(platform.id),
  });
}

/** DIS-138: etiqueta de la columna Enlace para las plataformas sin enlace a propósito. */
export const ETIQUETA_SIN_ENLACE_WEB = 'No requiere enlace web';

/**
 * Sin enlace a propósito («Omitir enlace», DIS-133): `direct_link` vacío. Un enlace escrito
 * pero no válido (no https) sí es un problema y se sigue avisando.
 */
export function sinEnlaceWeb(platform: Pick<Platform, 'direct_link'>): boolean {
  return !platform.direct_link?.trim();
}

export function columnasPlataformas({
  selectedPlatformIds,
  allSelected,
  someSelected,
  toggleSelectAll,
  togglePlatform,
  puedeEditarEstado = false,
  actualizarEstado,
  onEstadoCambiado,
  pendientes,
}: {
  selectedPlatformIds: Set<number>;
  allSelected: boolean;
  someSelected: boolean;
  toggleSelectAll: () => void;
  togglePlatform: (id: number) => void;
  /** Mismo permiso que «Editar»: el badge de estado conmuta (DIS-114). */
  puedeEditarEstado?: boolean;
  actualizarEstado?: (platform: Platform, status: 'Activo' | 'Inactivo') => Promise<unknown>;
  onEstadoCambiado?: () => void;
  /**
   * DIS-161: solicitudes pendientes por plataforma (`inbox/stats.pending_by_platform`, FNC-219).
   * Sin dato (consulta fallida o sin permiso) no se muestra la columna.
   */
  pendientes?: Record<number, number>;
}): DataColumn<Platform>[] {
  const columnas: DataColumn<Platform>[] = [
    {
      key: 'seleccion',
      header: (
        <div className="flex items-center justify-center">
          <input
            type="checkbox"
            checked={allSelected}
            ref={(el) => {
              if (el) el.indeterminate = someSelected;
            }}
            onChange={toggleSelectAll}
            aria-label="Seleccionar todas las plataformas"
            className="nexus-checkbox cursor-pointer"
          />
        </div>
      ),
      headerClassName: 'w-12 px-4 py-2 select-none text-center',
      cellClassName: 'w-12 px-4 py-1.5 text-center',
      cell: (platform) => {
        const isSelected = selectedPlatformIds.has(platform.id);
        return (
          <div className="flex items-center justify-center">
            <input
              type="checkbox"
              checked={isSelected}
              onClick={(e) => e.stopPropagation()}
              onChange={() => togglePlatform(platform.id)}
              aria-label={`Seleccionar ${platform.name}`}
              className="nexus-checkbox cursor-pointer"
            />
          </div>
        );
      },
    },
    {
      key: 'plataforma',
      header: 'Plataforma',
      headerClassName: 'px-6 py-2 font-black tracking-wider text-primary-text select-none',
      cellClassName: 'px-6 py-1.5',
      cell: (platform) => (
        <div className="flex items-center gap-2">
          <span
            className="nx-chip-solid grid size-8 shrink-0 place-items-center rounded-lg text-xs font-semibold shadow-xs"
            data-texto={atributoTexto(platform.bg_color)}
            style={variablesCss(variablesChipPlataforma(platform.bg_color))}
            aria-hidden
          >
            {platform.name.slice(0, 2).toUpperCase()}
          </span>
          <span className="truncate font-medium">{platform.name}</span>
        </div>
      ),
    },
    {
      key: 'area',
      header: 'Área',
      headerClassName: 'px-6 py-2 font-black tracking-wider text-primary-text select-none',
      cellClassName: 'px-6 py-1.5 text-label',
      cell: (platform) => platform.area_name ?? '—',
    },
    {
      key: 'enlace',
      header: 'Enlace',
      headerClassName: 'px-6 py-2 font-black tracking-wider text-primary-text select-none',
      cellClassName: 'max-w-xs px-6 py-1.5',
      cell: (platform) =>
        enlaceSeguro(platform.direct_link) ? (
          <span className="block truncate text-label" title={platform.direct_link ?? undefined}>
            {platform.direct_link}
          </span>
        ) : sinEnlaceWeb(platform) ? (
          // DIS-138: se guardó con «Omitir enlace»; no es un pendiente.
          <Badge tone="slate">{ETIQUETA_SIN_ENLACE_WEB}</Badge>
        ) : (
          <Badge tone="warning">Sin enlace</Badge>
        ),
    },
    {
      key: 'estado',
      header: 'Estado',
      headerClassName: 'px-6 py-2 font-black tracking-wider text-primary-text select-none',
      cellClassName: 'px-6 py-1.5',
      cell: (platform) => (
        <EstadoBadgeBoton
          tipo="plataforma"
          nombre={platform.name}
          activo={platform.status === 'Activo'}
          editable={puedeEditarEstado && Boolean(actualizarEstado)}
          actualizar={(status) => actualizarEstado!(platform, status)}
          onCambiado={onEstadoCambiado}
        />
      ),
    },
  ];

  if (pendientes) {
    columnas.push({
      key: 'pendientes',
      header: 'Solicitudes pendientes',
      headerClassName: 'px-6 py-2 font-black tracking-wider text-primary-text select-none',
      cellClassName: 'px-6 py-1.5',
      cell: (platform) => {
        const n = pendientes[platform.id] ?? 0;
        return (
          <Link
            href={rutaPendientesPlataforma(platform)}
            // La fila alterna la selección al hacer clic: el enlace no debe seleccionarla.
            onClick={(evento) => evento.stopPropagation()}
            aria-label={`Solicitudes pendientes: ${n}, en ${platform.name}. Abrir Historial.`}
            title="Ver solicitudes pendientes"
            className="inline-flex min-h-12 min-w-12 items-center gap-1.5 whitespace-nowrap rounded-lg px-3 text-xs font-bold tabular-nums text-primary-text transition-colors hover:bg-surface-container outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            {n}
          </Link>
        );
      },
    });
  }
  return columnas;
}
