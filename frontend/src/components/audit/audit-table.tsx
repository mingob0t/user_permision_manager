/**
 * Filas de la auditoría (DIS-020): fecha, quién, evento, sobre qué (con área
 * y plataforma), resultado y el botón del detalle.
 *
 * Tabla en escritorio y tarjeta en móvil con `ResponsiveList` (DIS-014).
 */

import type { AuditEntryV1 } from '@/lib/access/types';
import { formatearFecha } from '../access/fecha';
import { ETIQUETA_CELDA, ResponsiveList, ResponsiveRow } from '../access/responsive-list';
import { Button } from '../form';
import { Badge } from '../ui';
import { ACTOR_SISTEMA, etiquetaAccion, resultado } from './audit-actions';

/** Columnas en escritorio: fecha, quién, evento, sobre, resultado, acción. */
const COLUMNAS =
  'md:grid-cols-[minmax(0,1.5fr)_minmax(0,2fr)_minmax(0,2fr)_minmax(0,2fr)_minmax(0,1fr)_auto]';

export const ENCABEZADOS = ['Fecha', 'Quién', 'Evento', 'Sobre', 'Resultado', 'Detalle'];

/** `user` = "sistema" cuando actúa el sistema (contrato `auditoria.md`). */
const USUARIO_SISTEMA = 'sistema';

/** Quién actuó: el correo del actor, el `user` heredado o "Sistema". */
export function quienActuo(entry: AuditEntryV1): string {
  if (entry.actor) return entry.actor.email;
  return entry.user && entry.user !== USUARIO_SISTEMA ? entry.user : ACTOR_SISTEMA;
}

/** Área y plataforma del registro, si las tiene. */
function dondeOcurrio(entry: AuditEntryV1): string | null {
  const partes = [entry.platform?.name, entry.area?.name].filter(Boolean);
  return partes.length ? partes.join(' · ') : null;
}

function Fila({
  entry,
  onDetalle,
}: {
  entry: AuditEntryV1;
  onDetalle: (entry: AuditEntryV1, boton: HTMLButtonElement) => void;
}) {
  const fecha = formatearFecha(entry.time);
  const evento = etiquetaAccion(entry.action);
  const estado = resultado(entry.status);
  const donde = dondeOcurrio(entry);

  return (
    <ResponsiveRow columns={COLUMNAS} label={`${evento}, ${fecha}`}>
      <div>
        <dt className={ETIQUETA_CELDA}>Fecha</dt>
        <dd className="text-sm tabular-nums text-body-text">{fecha}</dd>
      </div>
      <div className="min-w-0">
        <dt className={ETIQUETA_CELDA}>Quién</dt>
        <dd className="break-words text-sm text-body-text">{quienActuo(entry)}</dd>
      </div>
      <div className="min-w-0">
        <dt className={ETIQUETA_CELDA}>Evento</dt>
        <dd className="text-sm font-semibold text-body-text">{evento}</dd>
        {entry.detail ? (
          <dd className="break-words text-sm text-label">{entry.detail}</dd>
        ) : null}
      </div>
      <div className="min-w-0">
        <dt className={ETIQUETA_CELDA}>Sobre</dt>
        <dd className="break-words text-sm text-body-text">
          {entry.target_user?.email ?? entry.target ?? '—'}
        </dd>
        {donde ? (
          <>
            <dt className="sr-only">Plataforma y área</dt>
            <dd className="break-words text-sm text-label">{donde}</dd>
          </>
        ) : null}
      </div>
      <div>
        <dt className={ETIQUETA_CELDA}>Resultado</dt>
        <dd><Badge tone={estado.tono}>{estado.texto}</Badge></dd>
      </div>
      <div>
        <dt className="sr-only">Detalle</dt>
        <dd>
          <Button
            variant="secondary"
            onClick={(event) => onDetalle(entry, event.currentTarget)}
            aria-label={`Ver detalle: ${evento}, ${fecha}`}
          >
            Ver detalle
          </Button>
        </dd>
      </div>
    </ResponsiveRow>
  );
}

export function AuditTable({
  items,
  onDetalle,
}: {
  items: AuditEntryV1[];
  onDetalle: (entry: AuditEntryV1, boton: HTMLButtonElement) => void;
}) {
  return (
    <ResponsiveList columns={COLUMNAS} headers={ENCABEZADOS} label="Registros de auditoría">
      {items.map((entry) => <Fila key={entry.id} entry={entry} onDetalle={onDetalle} />)}
    </ResponsiveList>
  );
}
