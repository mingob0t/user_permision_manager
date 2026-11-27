'use client';

/**
 * KPI «Usuarios» (DIS-146): dona de usuarios y administradores (`GET /stats` →
 * `desglose.users_by_role`), con el mismo diseño que las demás KPI del Resumen de Solicitudes.
 */

import type { DesgloseIndicador } from '@/lib/types';
import { DonaKpi } from '../dashboard/dona-kpi';

const PALETA_USUARIOS: Record<string, string> = {
  usuarios: '--color-indicador-usuarios',
  administradores: '--color-indicador-areas',
};

export function DonaUsuarios({ desglose }: { desglose: DesgloseIndicador }) {
  return (
    <DonaKpi
      titulo="Usuarios"
      icono="usuarios"
      paleta={PALETA_USUARIOS}
      filas={[
        { clave: 'usuarios', nombre: 'Usuarios', cantidad: desglose.parte, color: 'usuarios', punto: 'nx-dona__punto--serie-4' },
        { clave: 'administradores', nombre: 'Administradores', cantidad: desglose.resto, color: 'administradores', punto: 'nx-dona__punto--serie-1' },
      ]}
      vacioTitulo="Sin usuarios"
      vacioMensaje="Aún no hay usuarios registrados."
    />
  );
}
