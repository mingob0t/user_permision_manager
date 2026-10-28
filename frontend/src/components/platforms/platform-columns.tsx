/** Columnas de la tabla de Administrar plataformas (DIS-010, DIS-035). */

import type { Platform } from '@/lib/types';
import { enlaceSeguro } from '@/lib/enlace-seguro';
import { atributoTexto, variablesChipPlataforma } from '@/lib/color-legible';
import { variablesCss } from '@/lib/variables-css';
import { Button, ButtonLink } from '../form';
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
          <ButtonLink
            href={rutaHistorialPlataforma(platform.id)}
            variant="fila"
            aria-label={`Historial de ${platform.name} en Auditoría`}
          >
            Historial
          </ButtonLink>
          {canManage ? (
            <>
              <Button
                variant="fila"
                onClick={(e) => onEdit(e, platform)}
                aria-label={`Editar ${platform.name}`}
              >
                Editar
              </Button>
              <Button
                variant="fila-peligro"
                onClick={(e) => onRemove(e, platform)}
                aria-label={`Eliminar ${platform.name}`}
              >
                Eliminar
              </Button>
            </>
          ) : null}
        </div>
      ),
    },
  ];
}
