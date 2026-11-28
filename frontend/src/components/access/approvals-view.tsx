'use client';

/**
 * Pantalla Solicitudes (DIS-131): sin `?status=` muestra el resumen (tarjetas, gráficas y dona);
 * con `?status=todas|pendiente|aprobada|rechazada` abre el historial (`ApprovalsInbox`, DIS-156) con
 * sus filtros en la URL y un botón Volver al resumen en su barra. La URL permite Volver y F5.
 */

import { useSearchParams } from 'next/navigation';
import { PageHeader } from '../page-header';
import { ApprovalsInbox, ESTADOS_BANDEJA } from './approvals-inbox';
import { ApprovalsResumen, RUTA_SOLICITUDES } from './approvals-resumen';
import { valorPermitido } from './filtro-url';

export function ApprovalsView() {
  const params = useSearchParams();
  const estado = valorPermitido(params?.get('status'), ESTADOS_BANDEJA);

  if (!estado) {
    return (
      // DIS-144: como el Dashboard (flex + gap): el h1 oculto no suma espacio y el resumen
      // llena el alto del contenedor.
      <div className="flex h-full w-full min-h-0 flex-col gap-4">
        <PageHeader title="Solicitudes" />
        <ApprovalsResumen />
      </div>
    );
  }

  return (
    // DIS-156: como el detalle de Plataformas: Volver va en la barra de herramientas de la bandeja.
    <div className="flex h-full w-full min-h-0 flex-col gap-4">
      {/* DIS-157: sin descripción (pedido del dueño). */}
      <PageHeader title="Historial de solicitudes" />
      <ApprovalsInbox volverHref={RUTA_SOLICITUDES} />
    </div>
  );
}
