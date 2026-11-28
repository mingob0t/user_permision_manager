'use client';

/**
 * Barra de herramientas de la bandeja de aprobaciones (DIS-156): misma tarjeta, botón Volver y
 * buscador que el detalle de un área en Plataformas (`platform-admin.tsx`, clases
 * `nx-btn-toolbar` y `nx-buscador-toolbar`), con el selector de área y de estado y plataforma.
 * DIS-158: los selectores usan `SelectorToolbar` (antes `Select` nativo, fuera del estándar).
 */

import type { InboxStatus } from '@/lib/access/types';
import type { AreaRef } from '@/lib/types';
import { Icono } from '../icono';
import { ButtonLink } from '../form';
import { SelectorToolbar } from '../selector-toolbar';

export const FILTRO_ESTADO_ID = 'bandeja-filtro-estado';
export const FILTRO_AREA_ID = 'bandeja-filtro-area';
export const FILTRO_PLATAFORMA_ID = 'bandeja-filtro-plataforma';
export const BUSCADOR_ID = 'bandeja-buscador';

export interface OpcionEstado {
  valor: InboxStatus;
  texto: string;
}

export interface ApprovalsInboxToolbarProps {
  /** Con él se muestra el botón Volver (la pantalla decide el destino). */
  volverHref?: string;
  busqueda: string;
  onBusqueda: (valor: string) => void;
  estado: { valor: InboxStatus; opciones: OpcionEstado[]; onChange: (valor: InboxStatus) => void };
  areaId: number | null;
  areas: AreaRef[];
  etiquetaTodasAreas: string;
  onArea: (id: number | null) => void;
  /** Plataformas del área elegida (o de todo el alcance si no hay área). */
  plataformaId: number | null;
  plataformas: { id: number; name: string }[];
  onPlataforma: (id: number | null) => void;
}

export function ApprovalsInboxToolbar({
  volverHref,
  busqueda,
  onBusqueda,
  estado,
  areaId,
  areas,
  etiquetaTodasAreas,
  onArea,
  plataformaId,
  plataformas,
  onPlataforma,
}: ApprovalsInboxToolbarProps) {
  return (
    <div className="flex shrink-0 flex-wrap items-center justify-between gap-3 rounded-xl border border-panel-border/80 bg-gradient-to-r from-superficie via-superficie to-superficie-hundida p-3.5 shadow-1">
      <div className="flex min-w-0 max-w-5xl flex-1 flex-wrap items-center gap-3">
        {volverHref ? (
          <ButtonLink
            href={volverHref}
            variant="fila"
            aria-label="Volver al resumen de Solicitudes"
            title="Volver al resumen de Solicitudes"
            className="nx-btn-toolbar !px-3 inline-flex items-center gap-1.5 whitespace-nowrap text-xs font-bold shadow-xs"
          >
            <Icono nombre="chevron-izq" tamano="sm" ariaHidden={true} />
            <span>Resumen</span>
          </ButtonLink>
        ) : null}

        <div className="relative w-full min-w-48 max-w-md flex-1">
          <label htmlFor={BUSCADOR_ID} className="sr-only">
            Buscar por solicitante, correo o plataforma
          </label>
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-label">
            <Icono nombre="buscar" tamano="md" ariaHidden={true} />
          </div>
          <input
            id={BUSCADOR_ID}
            type="search"
            placeholder="Buscar solicitante, correo o plataforma…"
            value={busqueda}
            onChange={(event) => onBusqueda(event.target.value)}
            className="nx-buscador-toolbar h-12 w-full rounded-xl border border-panel-border bg-fondo py-3 pl-11 pr-10 text-sm text-body-text transition-all placeholder:text-placeholder focus:border-primary focus:bg-superficie focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
          {busqueda ? (
            <button
              type="button"
              onClick={() => {
                onBusqueda('');
                document.getElementById(BUSCADOR_ID)?.focus();
              }}
              className="absolute inset-y-0 right-0 flex min-h-12 min-w-12 items-center justify-center pr-3 text-label transition-colors hover:text-body-text"
              aria-label="Limpiar búsqueda"
            >
              <Icono nombre="cerrar" tamano="sm" ariaHidden={true} />
            </button>
          ) : null}
        </div>

        {/* DIS-158: selectores con el estándar de la barra de Plataformas (ícono, «Etiqueta: valor»). */}
        <SelectorToolbar
          id={FILTRO_ESTADO_ID}
          etiqueta="Estado"
          icono="inventario"
          valor={estado.valor}
          opciones={estado.opciones}
          onChange={estado.onChange}
          ariaLabel="Filtrar la bandeja por estado"
        />

        <SelectorToolbar<number | ''>
          id={FILTRO_AREA_ID}
          etiqueta="Área"
          icono="areas"
          valor={areaId ?? ''}
          opciones={[
            { valor: '', texto: etiquetaTodasAreas },
            ...areas.map((area) => ({ valor: area.id, texto: area.name })),
          ]}
          onChange={(v) => onArea(v === '' ? null : v)}
          ariaLabel="Filtrar la bandeja por área"
        />

        <SelectorToolbar<number | ''>
          id={FILTRO_PLATAFORMA_ID}
          etiqueta="Plataforma"
          icono="plataformas"
          valor={plataformaId ?? ''}
          opciones={[
            { valor: '', texto: 'Todas' },
            ...plataformas.map((plataforma) => ({ valor: plataforma.id, texto: plataforma.name })),
          ]}
          onChange={(v) => onPlataforma(v === '' ? null : v)}
          ariaLabel="Filtrar la bandeja por plataforma"
        />
      </div>
    </div>
  );
}
