'use client';

/**
 * Panel con una gráfica de barras (recharts) y su alternativa textual (DIS-131, horizontales en DIS-147): Card +
 * PanelHeader + barras con los tokens de tema + tabla `srOnly` con los mismos datos + estado
 * vacío. Barras horizontales: etiqueta en el eje Y y cantidad en el eje X. Mismo aspecto que las gráficas del dashboard; ese archivo conserva su copia (ver
 * propuesta de unificación en la ficha DIS-131).
 */

import { useId } from 'react';
import {
  Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import { useTokenColors } from '@/lib/use-token-colors';
import { DataTable } from '../data-table';
import type { NombreIcono } from '../icono';
import { Card, PanelHeader, PremiumEmptyState } from '../ui';

/** Alto por fila (px), alto mínimo y ancho (px) reservado a las etiquetas del eje Y. */
const ALTO_FILA = 32;
const ALTO_MIN = 120;
const ANCHO_ETIQUETA = 110;
const LARGO_ETIQUETA = 16;

interface PropsEtiqueta {
  x?: number;
  y?: number;
  payload?: { value: string };
  fill: string;
}

/** Etiqueta del eje Y: recorta con elipsis y deja el nombre completo en `<title>` (y en la tabla). */
function EtiquetaFila({ x = 0, y = 0, payload, fill }: PropsEtiqueta) {
  const texto = String(payload?.value ?? '');
  const corta = texto.length > LARGO_ETIQUETA ? `${texto.slice(0, LARGO_ETIQUETA - 1)}…` : texto;
  return (
    <text x={x - 4} y={y} dy={4} textAnchor="end" fontSize={12} fill={fill}>
      <title>{texto}</title>
      {corta}
    </text>
  );
}

const TOKENS_BARRAS = {
  serie: '--color-primary',
  serieAlterna: '--color-primary-text',
  eje: '--color-label-text',
  rejilla: '--color-panel-border',
  fondo: '--color-panel-fill',
  texto: '--color-body-text',
};

export interface FilaBarra {
  /** Clave estable de la fila. */
  id: string | number;
  etiqueta: string;
  cantidad: number;
}

interface Props {
  titulo: string;
  subtitulo: string;
  icono: NombreIcono;
  /** Nombre de la serie en el tooltip y de la columna de cantidad en la tabla. */
  serie: string;
  /** Encabezado de la columna de etiqueta en la tabla. */
  columna: string;
  filas: FilaBarra[];
  vacioTitulo: string;
  vacioMensaje: string;
  /** Usa el segundo color de serie para distinguir la gráfica. */
  alterna?: boolean;
}

export function GraficaBarras({
  titulo, subtitulo, icono, serie, columna, filas, vacioTitulo, vacioMensaje, alterna = false,
}: Props) {
  const colores = useTokenColors(TOKENS_BARRAS);
  const gradiente = `nx-barras-${useId().replace(/:/g, '')}`;
  const altoGrafica = Math.max(ALTO_MIN, filas.length * ALTO_FILA + 28);
  const color = alterna ? colores.serieAlterna || colores.serie : colores.serie;

  return (
    <Card className="!p-0 flex min-h-64 flex-1 flex-col overflow-hidden shadow-1 border border-panel-border/80">
      <PanelHeader title={titulo} subtitle={subtitulo} icon={icono} titleTag="h3" />
      {filas.length === 0 ? (
        <PremiumEmptyState variant="seamless" icono={icono} title={vacioTitulo} message={vacioMensaje} />
      ) : (
        <div className="flex flex-1 min-h-0 flex-col p-3">
          <div className="w-full min-h-0 flex-1" aria-hidden="true">
            <ResponsiveContainer width="100%" height="100%" minHeight={altoGrafica}>
              <BarChart data={filas} layout="vertical" margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id={gradiente} x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor={color} stopOpacity={1} />
                    <stop offset="100%" stopColor={color} stopOpacity={0.65} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={colores.rejilla} horizontal={false} />
                <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12, fill: colores.eje }} stroke={colores.rejilla} />
                <YAxis
                  type="category"
                  dataKey="etiqueta"
                  width={ANCHO_ETIQUETA}
                  interval={0}
                  tick={<EtiquetaFila fill={colores.eje} />}
                  stroke={colores.rejilla}
                />
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
                  labelStyle={{ color: colores.texto }}
                />
                <Bar dataKey="cantidad" name={serie} fill={`url(#${gradiente})`} radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          {/* Alternativa textual de la gráfica: los mismos datos. */}
          <DataTable
            srOnly
            label={titulo}
            columns={[
              { key: 'etiqueta', header: columna, cell: (fila) => fila.etiqueta },
              { key: 'cantidad', header: serie, cell: (fila) => fila.cantidad },
            ]}
            rows={filas}
            rowKey={(fila) => fila.id}
            emptyMessage={vacioMensaje}
          />
        </div>
      )}
    </Card>
  );
}
