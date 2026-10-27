/** Columnas de la tabla de Administrar plataformas (DIS-010, DIS-035). */

import Link from 'next/link';
import type { Platform } from '@/lib/types';
import { enlaceSeguro } from '@/lib/enlace-seguro';
import { variablesCss } from '@/lib/variables-css';
import { ACCION_FILA, ACCION_FILA_PELIGRO } from '../acciones-fila';
import { rutaHistorialPlataforma } from '../audit/audit-routes';
import type { DataColumn } from '../data-table';
import { Badge } from '../ui';

export function columnasPlataformas({
  canManage,
  onEdit,
  onRemove,
}: {
  canManage: boolean;
  onEdit: (event: React.MouseEvent<HTMLElement>, platform: Platform) => void;
  onRemove: (event: React.MouseEvent<HTMLElement>, platform: Platform) => void;
}): DataColumn<Platform>[] {
  return [
    {
      key: 'plataforma',
      header: 'Plataforma',
      cell: (platform) => (
        <div className="flex items-center gap-2">
          <span
            className="nx-chip-solid grid h-7 w-7 shrink-0 place-items-center rounded text-xs font-semibold"
            style={variablesCss({ '--chip-bg': platform.bg_color, '--chip-fg': platform.text_color })}
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
      cellClassName: 'px-4 py-2.5 text-label',
      cell: (platform) => platform.area_name ?? '—',
    },
    {
      key: 'enlace',
      header: 'Enlace',
      cellClassName: 'max-w-xs px-4 py-2.5',
      cell: (platform) =>
        enlaceSeguro(platform.direct_link) ? (
          <span className="block truncate text-label" title={platform.direct_link ?? undefined}>
            {platform.direct_link}
          </span>
        ) : (
          <Badge tone="warning">Sin enlace</Badge>
        ),
    },
    {
      key: 'estado',
      header: 'Estado',
      cell: (platform) => (
        <Badge tone={platform.status === 'Activo' ? 'success' : 'warning'}>{platform.status}</Badge>
      ),
    },
    {
      key: 'acciones',
      header: 'Acciones',
      headerSrOnly: true,
      cellClassName: 'whitespace-nowrap px-4 py-1 text-right',
      cell: (platform) => (
        // DIS-035: historial en Auditoría y acciones de 48 px (DIS-008), en una línea.
        <div className="flex justify-end gap-1">
          <Link
            href={rutaHistorialPlataforma(platform.id)}
            aria-label={`Historial de ${platform.name} en Auditoría`}
            className={ACCION_FILA}
          >
            Historial
          </Link>
          {canManage ? (
            <>
              <button
                type="button"
                onClick={(e) => onEdit(e, platform)}
                aria-label={`Editar ${platform.name}`}
                className={ACCION_FILA}
              >
                Editar
              </button>
              <button
                type="button"
                onClick={(e) => onRemove(e, platform)}
                aria-label={`Eliminar ${platform.name}`}
                className={ACCION_FILA_PELIGRO}
              >
                Eliminar
              </button>
            </>
          ) : null}
        </div>
      ),
    },
  ];
}
