'use client';

/**
 * KPI «Conectores» (DIS-146): dona de asociados y sin asociar (`GET /stats` → `desglose.connectors`),
 * con el mismo diseño que las demás KPI del Resumen de Solicitudes (`DonaKpi`).
 */

import type { DesgloseIndicador } from '@/lib/types';
import { DonaKpi } from '../dashboard/dona-kpi';

const PALETA_CONECTORES: Record<string, string> = {
  asociados: '--color-indicador-plataformas',
  sinAsociar: '--color-indicador-areas',
};

export function DonaConectores({ desglose }: { desglose: DesgloseIndicador }) {
  return (
    <DonaKpi
      titulo="Conectores"
      icono="marca"
      paleta={PALETA_CONECTORES}
      filas={[
        { clave: 'asociados', nombre: 'Asociados', cantidad: desglose.parte, color: 'asociados', punto: 'nx-dona__punto--serie-2' },
        { clave: 'sin-asociar', nombre: 'Sin asociar', cantidad: desglose.resto, color: 'sinAsociar', punto: 'nx-dona__punto--serie-1' },
      ]}
      vacioTitulo="Sin conectores"
      vacioMensaje="Aún no hay conectores registrados."
    />
  );
}
