/**
 * Filas del inventario de permisos (DIS-021, F-AUD-02): quién, plataforma,
 * área, nivel, origen, desde cuándo, quién aprobó y estado.
 *
 * Tabla en escritorio y tarjeta en móvil con `ResponsiveList` (DIS-014). Las
 * ocho columnas del contrato van en cinco grupos, como en Mis accesos
 * (plataforma con área, nivel con origen); cada dato tiene su propia etiqueta.
 */

import type { Access } from '@/lib/access/types';
import { AccessStatusBadge, NIVELES } from './access-status-badge';
import { formatearFecha } from './fecha';
import { ORIGENES_INVENTARIO } from './inventory-filters';
import { ETIQUETA_CELDA, ResponsiveList, ResponsiveRow } from './responsive-list';

/** Columnas en escritorio: usuario, plataforma y área, nivel y origen, desde y aprobó, estado. */
const COLUMNAS =
  'md:grid-cols-[minmax(0,2fr)_minmax(0,1.5fr)_minmax(0,1.5fr)_minmax(0,1.5fr)_minmax(0,1.5fr)]';

export const ENCABEZADOS = ['Usuario', 'Plataforma y área', 'Nivel y origen', 'Desde y aprobó', 'Estado'];

/** `granted_by` null = sistema (origen `admin_de_area`, contrato `accesos.md`). */
export const APROBO_SISTEMA = 'Sistema';

/** Quién aprobó u otorgó el acceso. */
export function quienAprobo(access: Access): string {
  return access.granted_by?.name ?? APROBO_SISTEMA;
}

function Fila({ access }: { access: Access }) {
  return (
    <ResponsiveRow
      columns={COLUMNAS}
      label={`Acceso de ${access.user.name} a ${access.platform.name}`}
    >
      <div className="min-w-0">
        <dt className={ETIQUETA_CELDA}>Usuario</dt>
        <dd className="font-semibold text-body-text">{access.user.name}</dd>
        <dd className="break-words text-sm text-label">{access.user.email}</dd>
      </div>
      <div className="min-w-0">
        <dt className={ETIQUETA_CELDA}>Plataforma</dt>
        <dd className="text-sm font-semibold text-body-text">{access.platform.name}</dd>
        <dt className="sr-only">Área</dt>
        <dd className="text-sm text-label">{access.area.name}</dd>
      </div>
      <div>
        <dt className={ETIQUETA_CELDA}>Nivel</dt>
        <dd className="text-sm text-body-text">{NIVELES[access.level]}</dd>
        <dt className="sr-only">Origen</dt>
        <dd className="text-sm text-label">{ORIGENES_INVENTARIO[access.origin]}</dd>
      </div>
      <div>
        <dt className={ETIQUETA_CELDA}>Desde</dt>
        <dd className="text-sm text-body-text">{formatearFecha(access.granted_at)}</dd>
        <dt className="sr-only">Aprobó</dt>
        <dd className="text-sm text-label">
          <span aria-hidden>Aprobó: </span>{quienAprobo(access)}
        </dd>
      </div>
      <div>
        <dt className={ETIQUETA_CELDA}>Estado</dt>
        <dd><AccessStatusBadge status={access.status} /></dd>
        {access.revoked_at ? (
          <dd className="mt-1 text-sm text-label">
            Retirado: {formatearFecha(access.revoked_at)}
            {access.revoked_by ? ` por ${access.revoked_by.name}` : ''}
          </dd>
        ) : null}
      </div>
    </ResponsiveRow>
  );
}

export function InventoryTable({ items }: { items: Access[] }) {
  return (
    <ResponsiveList columns={COLUMNAS} headers={ENCABEZADOS} label="Inventario de permisos">
      {items.map((access) => <Fila key={access.id} access={access} />)}
    </ResponsiveList>
  );
}
