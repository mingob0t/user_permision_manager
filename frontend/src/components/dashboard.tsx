'use client';

/**
 * Panel: resumen por rol (DIS-024) encima de la actividad del portal (`/stats`):
 * visitas, gráfica de plataformas por área con tabla alternativa (DIS-003) y
 * más visitadas. Áreas y Plataformas solo se repiten a quien no tiene resumen
 * de totales (DIS-037).
 */

import {
  Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import { useState } from 'react';
import { api } from '@/lib/api';
import type { Stats } from '@/lib/types';
import { useAsync } from '@/lib/use-async';
import { useTokenColors } from '@/lib/use-token-colors';
import { RoleSummary } from './home/role-summary';
import { useSession } from './session-provider';
import { Card, ErrorNote, Spinner, StatTile } from './ui';

export function Dashboard() {
  const { session } = useSession();
  const { data: stats, loading, error } = useAsync(() => api.stats(), []);
  const [resumenFallo, setResumenFallo] = useState(false);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Panel</h1>
        <p className="mt-1 text-sm text-label">
          {session?.permissions.is_admin
            ? 'Vista global del sistema.'
            : 'Datos de las áreas a las que tienes acceso.'}
        </p>
      </div>

      <RoleSummary onFallo={setResumenFallo} />

      {loading ? <Spinner /> : null}
      {error ? <ErrorNote message={error} /> : null}
      {stats ? <Estadisticas stats={stats} resumenFallo={resumenFallo} /> : null}
    </div>
  );
}

/** Tokens de la gráfica (DIS-003): todos de tema, medidos en `pares-contraste.ts`. */
const TOKENS_GRAFICA = {
  serie: '--color-primary',
  eje: '--color-label-text',
  rejilla: '--color-panel-border',
  fondo: '--color-panel-fill',
  texto: '--color-body-text',
};

/** Contadores, gráfica y más visitadas de `/stats`. */
function Estadisticas({ stats, resumenFallo }: { stats: Stats; resumenFallo: boolean }) {
  const { session, loading: cargandoSesion } = useSession();
  const colores = useTokenColors(TOKENS_GRAFICA);
  const byArea = stats.platforms_by_area.filter((row) => row.count > 0);
  // DIS-037: el resumen por rol ya muestra Áreas y Plataformas a quien administra. No se muestran
  // hasta conocer el rol (sin saltos) y reaparecen si el resumen falla (respaldo).
  const administra = Boolean(session?.permissions.is_admin || session?.permissions.is_area_admin);
  const verAreasYPlataformas = !cargandoSesion && (!administra || resumenFallo);

  return (
    <>
      <h2 className="text-lg font-semibold">Actividad del portal</h2>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {verAreasYPlataformas ? <StatTile label="Áreas" value={stats.areas} /> : null}
        {verAreasYPlataformas ? <StatTile label="Plataformas" value={stats.platforms} /> : null}
        <StatTile label="Visitas" value={stats.visits} />
        {stats.users !== undefined ? (
          <StatTile label="Usuarios" value={stats.users} />
        ) : null}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <h3 className="text-sm font-medium">Plataformas por área</h3>
          {byArea.length === 0 ? (
            <p className="pt-4 text-sm text-label">Sin datos todavía.</p>
          ) : (
            <>
              <div className="h-64 pt-4" aria-hidden="true">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={byArea} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={colores.rejilla} vertical={false} />
                    <XAxis
                      dataKey="area"
                      tick={{ fontSize: 12, fill: colores.eje }}
                      stroke={colores.rejilla}
                      interval={0}
                      angle={-20}
                      textAnchor="end"
                      height={72}
                    />
                    <YAxis
                      allowDecimals={false}
                      width={40}
                      tick={{ fontSize: 12, fill: colores.eje }}
                      stroke={colores.rejilla}
                    />
                    <Tooltip
                      contentStyle={{
                        background: colores.fondo,
                        border: `1px solid ${colores.rejilla}`,
                        borderRadius: 'var(--radius-panel)',
                        color: colores.texto,
                      }}
                      itemStyle={{ color: colores.texto }}
                      labelStyle={{ color: colores.texto }}
                    />
                    <Bar
                      dataKey="count"
                      name="Plataformas"
                      fill={colores.serie}
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              {/* Alternativa textual de la gráfica: los mismos datos (DIS-003). */}
              <table className="sr-only">
                <caption>Plataformas por área</caption>
                <thead>
                  <tr>
                    <th scope="col">Área</th>
                    <th scope="col">Plataformas</th>
                  </tr>
                </thead>
                <tbody>
                  {byArea.map((row) => (
                    <tr key={row.area}>
                      <th scope="row">{row.area}</th>
                      <td>{row.count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </Card>

        <Card>
          <h3 className="text-sm font-medium">Más visitadas</h3>
          {stats.most_visited.length === 0 ? (
            <p className="pt-4 text-sm text-label">Sin visitas registradas.</p>
          ) : (
            <ul className="divide-y divide-panel-border pt-2">
              {stats.most_visited.map((row) => (
                <li
                  key={row.id}
                  className="flex items-center justify-between py-2.5 text-sm"
                >
                  <span className="truncate pr-4">{row.name}</span>
                  <span className="tabular-nums text-label">{row.visits}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </>
  );
}
