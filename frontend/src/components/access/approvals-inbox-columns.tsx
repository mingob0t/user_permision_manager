'use client';

/**
 * Columnas de la tabla de la bandeja de aprobaciones (DIS-156), para `DataTable`.
 * La justificación y el motivo de rechazo son columnas aparte y condicionables
 * (`mostrarJustificacion`, `mostrarMotivo`) para poder ocultarlas por configuración (FNC-217).
 */

import type { AccessRequest } from '@/lib/access/types';
import { Button } from '../form';
import { Icono } from '../icono';
import type { DataColumn } from '../data-table';
import { AccessStatusBadge, NIVELES } from './access-status-badge';
import { formatearFechaCorta24h } from './fecha';
import { RequestStatusBadge } from './request-status-badge';

export const MENSAJE_PROPIA = 'Es tu solicitud: la decide otro administrador.';

export type TipoDecision = 'aprobar' | 'rechazar';

export interface OpcionesColumnasBandeja {
  /** Solicitud propia: no se decide (la decide otro administrador). */
  esPropia: (request: AccessRequest) => boolean;
  onDecidir: (tipo: TipoDecision, request: AccessRequest, trigger: HTMLButtonElement) => void;
  mostrarJustificacion?: boolean;
  mostrarMotivo?: boolean;
}

const ENCABEZADO = 'px-4 py-2 font-black tracking-wider text-primary-text select-none';
const CELDA = 'px-4 py-1.5';

/** Nombre accesible de cada botón: qué hace y sobre qué solicitud. */
export function nombreAccion(accion: 'Aprobar' | 'Rechazar', r: AccessRequest): string {
  return `${accion} la solicitud de ${r.requester.name} para ${r.platform.name}`;
}

function Dos({ principal, secundario }: { principal: string; secundario?: string | null }) {
  return (
    <div className="min-w-0">
      <span className="block truncate font-semibold text-body-text" title={principal}>{principal}</span>
      {secundario ? (
        <span className="block truncate text-xs text-label" title={secundario}>{secundario}</span>
      ) : null}
    </div>
  );
}

export function columnasBandeja({
  esPropia,
  onDecidir,
  mostrarJustificacion = true,
  mostrarMotivo = true,
}: OpcionesColumnasBandeja): DataColumn<AccessRequest>[] {
  const columnas: DataColumn<AccessRequest>[] = [
    {
      key: 'solicitante',
      header: 'Solicitante',
      headerClassName: ENCABEZADO,
      cellClassName: CELDA,
      cell: (r) => <Dos principal={r.requester.name} secundario={r.requester.email} />,
    },
    {
      key: 'plataforma',
      header: 'Plataforma',
      headerClassName: ENCABEZADO,
      cellClassName: CELDA,
      cell: (r) => <Dos principal={r.platform.name} secundario={r.area.name} />,
    },
    {
      key: 'nivel',
      header: 'Nivel',
      headerClassName: ENCABEZADO,
      cellClassName: CELDA,
      cell: (r) => (
        <Dos
          principal={NIVELES[r.level]}
          secundario={r.current_level ? `Tiene ${NIVELES[r.current_level]}` : null}
        />
      ),
    },
    {
      key: 'estado',
      header: 'Estado',
      headerClassName: ENCABEZADO,
      cellClassName: CELDA,
      cell: (r) => {
        const decidida = r.decided_at
          ? `Decidida: ${formatearFechaCorta24h(r.decided_at)}${r.decided_by ? ` por ${r.decided_by.name}` : ''}`
          : null;
        const fecha = `Enviada: ${formatearFechaCorta24h(r.created_at)}`;
        return (
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-1.5">
              <RequestStatusBadge status={r.status} />
              {r.access ? <AccessStatusBadge status={r.access.status} /> : null}
            </div>
            <span
              className="block truncate text-xs tabular-nums text-label"
              title={decidida ? `${fecha}. ${decidida}` : fecha}
            >
              {decidida ?? fecha}
            </span>
          </div>
        );
      },
    },
  ];

  if (mostrarJustificacion) {
    columnas.push({
      key: 'justificacion',
      header: 'Justificación',
      headerClassName: ENCABEZADO,
      cellClassName: CELDA,
      // Texto del solicitante: React lo escapa; nunca HTML.
      cell: (r) => (
        <span className="block truncate text-label" title={r.justification || undefined}>
          {r.justification || 'Sin justificación.'}
        </span>
      ),
    });
  }

  if (mostrarMotivo) {
    columnas.push({
      key: 'motivo',
      header: 'Motivo del rechazo',
      headerClassName: ENCABEZADO,
      cellClassName: CELDA,
      cell: (r) => {
        const motivo = r.status === 'rechazada' ? r.rejection_reason : null;
        return motivo ? (
          <span className="block truncate text-body-text" title={motivo}>{motivo}</span>
        ) : (
          <span className="text-label">
            <span aria-hidden="true">—</span>
            <span className="sr-only">Sin motivo de rechazo</span>
          </span>
        );
      },
    });
  }

  columnas.push({
    key: 'acciones',
    header: 'Acciones',
    headerClassName: 'w-36 px-4 py-2 text-right font-black tracking-wider text-primary-text select-none',
    cellClassName: 'w-36 px-4 py-1.5',
    cell: (r) => {
      if (r.status !== 'pendiente') {
        return <span className="block text-right text-xs text-label">Decidida</span>;
      }
      if (esPropia(r)) {
        return (
          <span className="block text-right text-xs text-label" title={MENSAJE_PROPIA}>
            Tu solicitud<span className="sr-only">. {MENSAJE_PROPIA}</span>
          </span>
        );
      }
      return (
        <div className="flex items-center justify-end gap-2">
          <Button
            variant="fila-peligro"
            aria-label={nombreAccion('Rechazar', r)}
            title="Rechazar"
            onClick={(event) => onDecidir('rechazar', r, event.currentTarget)}
          >
            <Icono nombre="rechazar" />
          </Button>
          <Button
            variant="fila-primario"
            aria-label={nombreAccion('Aprobar', r)}
            title="Aprobar"
            onClick={(event) => onDecidir('aprobar', r, event.currentTarget)}
          >
            <Icono nombre="aprobar" />
          </Button>
        </div>
      );
    },
  });

  return columnas;
}
