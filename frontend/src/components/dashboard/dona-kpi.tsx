'use client';

/**
 * Tarjeta KPI con dona (DIS-131, generalizada en DIS-144): recharts `Pie` con `innerRadius`,
 * colores por token y leyenda con cifra y porcentaje en texto (la gráfica es decorativa para el
 * lector de pantalla). La usan las cuatro KPI del Resumen de Solicitudes (DIS-146, DIS-151).
 */

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';
import { useTokenColors } from '@/lib/use-token-colors';
import type { NombreIcono } from '../icono';
import { Card, PanelHeader, PremiumEmptyState } from '../ui';
import { porcentaje } from './indicadores';

const RADIO_INTERIOR = '58%';
const RADIO_EXTERIOR = '88%';
const SEPARACION_GRADOS = 2;

const TOKENS_BASE = {
  rejilla: '--color-panel-border',
  fondo: '--color-panel-fill',
  texto: '--color-body-text',
};

export interface FilaDona {
  clave: string;
  nombre: string;
  cantidad: number;
  /** Clave de `paleta` con el color del segmento. */
  color: string;
  /** Clase literal del punto de la leyenda con el mismo color (components.css). */
  punto: string;
}

export function DonaKpi({
  titulo,
  icono,
  paleta,
  filas,
  vacioTitulo,
  vacioMensaje,
  textoTotal = 'en total',
}: {
  titulo: string;
  icono: NombreIcono;
  /** Clave → token de color. Constante de módulo: `useTokenColors` la lee al montar. */
  paleta: Record<string, string>;
  filas: FilaDona[];
  vacioTitulo: string;
  vacioMensaje: string;
  /** Texto tras el total en el subtítulo (DIS-151), p. ej. «por aprobar». */
  textoTotal?: string;
}) {
  const total = filas.reduce((suma, fila) => suma + fila.cantidad, 0);
  const colores = useTokenColors({ ...TOKENS_BASE, ...paleta }) as Record<string, string>;
  const conPct = filas.map((fila) => ({ ...fila, pct: porcentaje({ parte: fila.cantidad, resto: total - fila.cantidad }) }));

  return (
    <Card className="!p-0 flex h-full flex-col overflow-hidden shadow-1 border border-panel-border/80">
      <PanelHeader title={titulo} subtitle={`${total} ${textoTotal}`} icon={icono} titleTag="h3" />
      {total === 0 ? (
        <PremiumEmptyState variant="seamless" icono={icono} title={vacioTitulo} message={vacioMensaje} />
      ) : (
        <div className="flex flex-1 items-center gap-4 p-4">
          <div className="size-28 shrink-0" aria-hidden="true">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={conPct}
                  dataKey="cantidad"
                  nameKey="nombre"
                  innerRadius={RADIO_INTERIOR}
                  outerRadius={RADIO_EXTERIOR}
                  paddingAngle={SEPARACION_GRADOS}
                  stroke={colores.fondo}
                >
                  {conPct.map((fila) => <Cell key={fila.clave} fill={colores[fila.color]} />)}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: colores.fondo,
                    border: `1px solid ${colores.rejilla}`,
                    borderRadius: '10px',
                    color: colores.texto,
                    boxShadow: 'var(--sombra-1)',
                    fontSize: '12px',
                    fontWeight: 600,
                    padding: '6px 10px',
                  }}
                  itemStyle={{ color: colores.texto }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <ul className="grid min-w-0 flex-1 gap-2" aria-label={titulo}>
            {conPct.map((fila) => (
              <li key={fila.clave} className="flex items-center gap-2 text-sm text-label">
                <span className={`${fila.punto} size-3 shrink-0 rounded-sm`} aria-hidden="true" />
                <span className="min-w-0 flex-1 truncate" title={fila.nombre}>{fila.nombre}</span>
                <b className="font-bold tabular-nums text-body-text">{fila.cantidad}</b>
                <span className="w-12 text-right font-semibold tabular-nums text-body-text">{fila.pct} %</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </Card>
  );
}
