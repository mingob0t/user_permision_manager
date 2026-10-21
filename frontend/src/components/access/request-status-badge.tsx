/**
 * Estado de una solicitud de acceso como insignia con texto (DIS-014): nunca
 * solo color. Reutilizable en Aprobaciones (DIS-015).
 */

import type { RequestStatus } from '@/lib/access/types';
import { Badge } from '../ui';

type Tono = React.ComponentProps<typeof Badge>['tone'];

export const ESTADOS_SOLICITUD: Record<RequestStatus, { texto: string; tono: Tono }> = {
  pendiente: { texto: 'Pendiente', tono: 'warning' },
  aprobada: { texto: 'Aprobada', tono: 'success' },
  rechazada: { texto: 'Rechazada', tono: 'error' },
};

export function RequestStatusBadge({ status }: { status: RequestStatus }) {
  const { texto, tono } = ESTADOS_SOLICITUD[status];
  return <Badge tone={tono}>{texto}</Badge>;
}
