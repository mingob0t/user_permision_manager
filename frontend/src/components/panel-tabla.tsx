'use client';

/**
 * Piezas de la «tabla de panel» de 8 filas a todo lo alto (estilo de «Actividad reciente»,
 * DIS-079): encabezado de columnas con degradado, filas de relleno vacías (zebra) para mantener la simetría y
 * pie con «N de total registros» y paginador `‹ N/TOTAL ›` (DIS-141).
 *
 * La rejilla de columnas la define quien la usa (`claseGrid`, p. ej.
 * `sm:grid-cols-[minmax(0,2fr)_minmax(0,1fr)_auto]`) para que encabezado, filas y fantasmas
 * queden alineados.
 */

import { Icono } from './icono';

/** Clases de una fila (real o fantasma) según su posición: zebra striping. */
export function claseFilaPanel(indice: number): string {
  return indice % 2 === 1 ? 'bg-fondo/75' : 'bg-panel-fill';
}

export function PanelTablaEncabezado({ columnas, claseGrid }: { columnas: string[]; claseGrid: string }) {
  return (
    <div
      className={`hidden shrink-0 border-b-2 border-primary/35 bg-gradient-to-r from-primary/15 via-brand/10 to-accent/10 px-4 py-2 text-xs font-black uppercase tracking-wider text-primary-text sm:grid sm:gap-3 ${claseGrid}`}
      aria-hidden="true"
    >
      {columnas.map((columna, i) => (
        <span key={columna} className={i === columnas.length - 1 ? 'text-right' : undefined}>
          {columna}
        </span>
      ))}
    </div>
  );
}

/**
 * Filas de relleno (solo escritorio) que completan la página; `desde` = filas reales ya pintadas.
 * DIS-148: vacías, sin barras ni círculos de esqueleto, para no aparentar registros que no
 * existen; solo continúan la alternancia de color (zebra) y el borde de las filas reales.
 */
export function FilasFantasma({
  cantidad,
  desde,
  claseGrid,
}: {
  cantidad: number;
  desde: number;
  claseGrid: string;
}) {
  return (
    <>
      {Array.from({ length: cantidad }).map((_, idx) => (
        <li
          key={`fantasma-${idx}`}
          aria-hidden="true"
          data-fila-relleno=""
          className={`hidden sm:grid flex-1 min-h-0 border-b border-panel-border/20 select-none pointer-events-none ${claseGrid} ${claseFilaPanel(desde + idx)}`}
        />
      ))}
    </>
  );
}

const CLASE_BOTON_PAGINA =
  'flex min-h-12 min-w-12 items-center justify-center rounded-lg text-primary-text transition-all hover:bg-surface-container active:scale-95 disabled:opacity-deshabilitada disabled:pointer-events-none outline-none focus-visible:ring-2 focus-visible:ring-primary';

/** Pie con el contador y, si hay más de una página, el paginador. `etiqueta`: «de solicitudes». */
export function PanelTablaPie({
  mostrados,
  total,
  pagina,
  paginas,
  onPagina,
  etiqueta,
}: {
  mostrados: number;
  total: number;
  pagina: number;
  paginas: number;
  onPagina: (pagina: number) => void;
  etiqueta: string;
}) {
  return (
    <div className="flex shrink-0 items-center justify-between border-t border-panel-border/80 bg-superficie-hundida/50 px-4 py-2.5 text-xs">
      <span className="flex items-center gap-2 font-semibold tabular-nums text-label">
        <span className="inline-block size-2 rounded-full bg-primary/70 animate-pulse" aria-hidden="true" />
        <span>{mostrados} de {total} registros</span>
      </span>

      {paginas > 1 ? (
        <nav
          aria-label={`Paginación ${etiqueta}`}
          className="flex items-center gap-1 rounded-xl border border-panel-border/80 bg-superficie/90 p-0.5 shadow-xs"
        >
          <button
            type="button"
            disabled={pagina <= 1}
            onClick={() => onPagina(Math.max(1, pagina - 1))}
            className={CLASE_BOTON_PAGINA}
            aria-label={`Página anterior ${etiqueta}`}
            title="Página anterior"
          >
            <Icono nombre="chevron-izq" tamano="sm" ariaHidden={true} />
          </button>
          <span className="px-2.5 py-0.5 text-xs font-black tabular-nums tracking-wide text-body-text select-none" aria-current="page">
            {pagina}/{paginas}
          </span>
          <button
            type="button"
            disabled={pagina >= paginas}
            onClick={() => onPagina(Math.min(paginas, pagina + 1))}
            className={CLASE_BOTON_PAGINA}
            aria-label={`Página siguiente ${etiqueta}`}
            title="Página siguiente"
          >
            <Icono nombre="chevron-der" tamano="sm" ariaHidden={true} />
          </button>
        </nav>
      ) : null}
    </div>
  );
}
