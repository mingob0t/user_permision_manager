'use client';

/**
 * Detalle de un registro de auditoría (DIS-020, F-AUD-03): quién, qué, sobre
 * qué, dónde y, si vienen, antes y después como lista de campos.
 *
 * - Todo se pinta como texto (React lo escapa); nunca como HTML.
 * - `ip`, `before` y `after` llegan en null al usuario: esas secciones no se muestran.
 * - Cerrar devuelve el foco al botón que lo abrió (lo hace `AuditHistory`).
 */

import type { AuditEntryV1 } from '@/lib/access/types';
import { DataLabel, DataList, DataListItem } from '../data-table';
import { formatearFecha } from '../access/fecha';
import { Modal } from '../form';
import { Badge } from '../ui';
import { etiquetaAccion, resultado } from './audit-actions';
import { compararCampos } from './audit-diff';
import { quienActuo } from './audit-table';

export const TITULO_DETALLE = 'Detalle del registro';

/** Dato de un detalle (`dt`/`dd`); reutilizado en DIS-022. */
export function Dato({ etiqueta, valor }: { etiqueta: string; valor: React.ReactNode }) {
  return <DataLabel label={etiqueta}>{valor}</DataLabel>;
}

export function AuditDetailModal({ entry, onClose }: { entry: AuditEntryV1; onClose: () => void }) {
  const campos = compararCampos(entry.before, entry.after);
  const conAntes = entry.before !== null;
  const tono = resultado(entry.status);

  return (
    <Modal title={TITULO_DETALLE} onClose={onClose}>
      <dl className="grid gap-3 sm:grid-cols-2">
        <Dato etiqueta="Fecha" valor={formatearFecha(entry.time)} />
        <Dato etiqueta="Resultado" valor={<Badge tone={tono.tono}>{tono.texto}</Badge>} />
        <Dato etiqueta="Evento" valor={etiquetaAccion(entry.action)} />
        <Dato etiqueta="Quién" valor={quienActuo(entry)} />
        <Dato etiqueta="Sobre" valor={entry.target_user?.email ?? entry.target ?? '—'} />
        <Dato etiqueta="Módulo" valor={entry.module ?? '—'} />
        <Dato etiqueta="Área" valor={entry.area?.name ?? '—'} />
        <Dato etiqueta="Plataforma" valor={entry.platform?.name ?? '—'} />
        {entry.ip ? <Dato etiqueta="IP" valor={entry.ip} /> : null}
        {entry.detail ? (
          <div className="sm:col-span-2">
            <Dato etiqueta="Detalle" valor={entry.detail} />
          </div>
        ) : null}
      </dl>

      {campos.length > 0 ? (
        <section aria-labelledby="auditoria-detalle-cambios" className="space-y-3">
          <h3 id="auditoria-detalle-cambios" className="text-sm font-semibold text-body-text">
            {conAntes ? 'Antes y después' : 'Valores registrados'}
          </h3>
          <DataList>
            {campos.map((c) => (
              <DataListItem key={c.campo}>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="break-all text-sm font-semibold text-body-text">{c.campo}</span>
                  {conAntes && c.cambio ? <Badge tone="primary">Cambió</Badge> : null}
                </div>
                <dl className="grid gap-1 sm:grid-cols-2 sm:gap-3">
                  {conAntes ? (
                    <DataLabel label="Antes">{c.antes}</DataLabel>
                  ) : null}
                  <DataLabel label={conAntes ? 'Después' : 'Valor'}>{c.despues}</DataLabel>
                </dl>
              </DataListItem>
            ))}
          </DataList>
        </section>
      ) : null}
    </Modal>
  );
}
