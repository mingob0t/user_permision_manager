'use client';

/**
 * KPI «Conectores» (DIS-146): dona de asociados y sin asociar (`GET /stats` → `desglose.connectors`),
 * con el mismo diseño que las demás KPI del Resumen de Solicitudes (`DonaKpi`).
 * DIS-152: colores del par `PAR_DOS_SERIES` (luminancia separada) y, si `GET /stats` no trae el
 * desglose, una sola fila «Total» con el valor en lugar de ocultar la tarjeta.
 */

import type { DesgloseIndicador } from '@/lib/types';
import { DonaKpi, PAR_DOS_SERIES, type FilaDona } from '../dashboard/dona-kpi';

const PALETA_CONECTORES: Record<string, string> = {
  primera: PAR_DOS_SERIES.primera.token,
  segunda: PAR_DOS_SERIES.segunda.token,
};

export function filasConectores(valor: number, desglose?: DesgloseIndicador): FilaDona[] {
  const primera = { color: 'primera', punto: PAR_DOS_SERIES.primera.punto };
  if (!desglose) return [{ clave: 'total', nombre: 'Total', cantidad: valor, ...primera }];
  return [
    { clave: 'asociados', nombre: 'Asociados', cantidad: desglose.parte, ...primera },
    { clave: 'sin-asociar', nombre: 'Sin asociar', cantidad: desglose.resto, color: 'segunda', punto: PAR_DOS_SERIES.segunda.punto },
  ];
}

export function DonaConectores({ valor, desglose }: { valor: number; desglose?: DesgloseIndicador }) {
  return (
    <DonaKpi
      titulo="Conectores"
      icono="marca"
      paleta={PALETA_CONECTORES}
      filas={filasConectores(valor, desglose)}
      vacioTitulo="Sin conectores"
      vacioMensaje="Aún no hay conectores registrados."
    />
  );
}
