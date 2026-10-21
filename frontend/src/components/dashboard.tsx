'use client';

/**
 * Panel: resumen por rol (DIS-024) encima de los contadores y la distribución
 * de plataformas dentro del alcance (`/stats`, heredado).
 */

import {
  Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import { api } from '@/lib/api';
import type { Stats } from '@/lib/types';
import { useAsync } from '@/lib/use-async';
import { RoleSummary } from './home/role-summary';
import { useSession } from './session-provider';
import { Card, ErrorNote, Spinner, StatTile } from './ui';

export function Dashboard() {
  const { session } = useSession();
  const { data: stats, loading, error } = useAsync(() => api.stats(), []);

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

      <RoleSummary />

      {loading ? <Spinner /> : null}
      {error ? <ErrorNote message={error} /> : null}
      {stats ? <Estadisticas stats={stats} /> : null}
    </div>
  );
}

/** Contadores, gráfica y más visitadas de `/stats` (sin cambios, DIS-024). */
function Estadisticas({ stats }: { stats: Stats }) {
  const byArea = stats.platforms_by_area.filter((row) => row.count > 0);

  return (
    <>
      <h2 className="text-lg font-semibold">Actividad del portal</h2>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile label="Áreas" value={stats.areas} />
        <StatTile label="Plataformas" value={stats.platforms} />
        <StatTile label="Visitas" value={stats.visits} />
        {stats.users !== undefined ? (
          <StatTile label="Usuarios" value={stats.users} />
        ) : null}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <h2 className="text-sm font-medium">Plataformas por área</h2>
          {byArea.length === 0 ? (
            <p className="pt-4 text-sm text-label">Sin datos todavía.</p>
          ) : (
            <div className="h-64 pt-4">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={byArea}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="rgb(var(--nx-border))"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="area"
                    tick={{ fontSize: 11, fill: 'rgb(var(--nx-muted))' }}
                    interval={0}
                    angle={-20}
                    textAnchor="end"
                    height={60}
                  />
                  <YAxis
                    allowDecimals={false}
                    tick={{ fontSize: 11, fill: 'rgb(var(--nx-muted))' }}
                  />
                  <Tooltip
                    contentStyle={{
                      background: 'rgb(var(--nx-panel))',
                      border: '1px solid rgb(var(--nx-border))',
                      borderRadius: 8,
                      color: 'rgb(var(--nx-content))',
                    }}
                  />
                  <Bar dataKey="count" name="Plataformas" radius={[4, 4, 0, 0]}>
                    {byArea.map((row) => (
                      <Cell key={row.area} fill={row.color || '#6366f1'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </Card>

        <Card>
          <h2 className="text-sm font-medium">Más visitadas</h2>
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
