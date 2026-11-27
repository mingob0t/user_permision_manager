'use client';

/**
 * KPI «Usuarios» (DIS-146): dona de rol usuario frente a administradores (`GET /stats` →
 * `desglose.users_by_role`), con el mismo diseño que las demás KPI del Resumen (`DonaKpi`).
 * DIS-152: colores del par `PAR_DOS_SERIES` (luminancia separada) y, si `GET /stats` no trae el
 * desglose, una sola fila «Total» con el valor en lugar de ocultar la tarjeta.
 */

import type { DesgloseIndicador } from '@/lib/types';
import { DonaKpi, PAR_DOS_SERIES, type FilaDona } from '../dashboard/dona-kpi';

const PALETA_USUARIOS: Record<string, string> = {
  primera: PAR_DOS_SERIES.primera.token,
  segunda: PAR_DOS_SERIES.segunda.token,
};

export function filasUsuarios(valor: number, desglose?: DesgloseIndicador): FilaDona[] {
  const primera = { color: 'primera', punto: PAR_DOS_SERIES.primera.punto };
  if (!desglose) return [{ clave: 'total', nombre: 'Total', cantidad: valor, ...primera }];
  return [
    { clave: 'usuarios', nombre: 'Usuarios', cantidad: desglose.parte, ...primera },
    { clave: 'administradores', nombre: 'Administradores', cantidad: desglose.resto, color: 'segunda', punto: PAR_DOS_SERIES.segunda.punto },
  ];
}

export function DonaUsuarios({ valor, desglose }: { valor: number; desglose?: DesgloseIndicador }) {
  return (
    <DonaKpi
      titulo="Usuarios"
      icono="usuarios"
      paleta={PALETA_USUARIOS}
      filas={filasUsuarios(valor, desglose)}
      vacioTitulo="Sin usuarios"
      vacioMensaje="Aún no hay usuarios registrados."
    />
  );
}
