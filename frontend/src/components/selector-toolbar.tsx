'use client';

/**
 * Selector de barra de herramientas (DIS-158): el patrón de los filtros del detalle de Plataformas
 * (`platform-admin.tsx`, «Estado: Todos»): botón de 48 px con ícono, «Etiqueta: valor» y chevron,
 * y menú `listbox` con la opción elegida marcada. Se cierra con clic fuera o Escape (el foco vuelve
 * al botón); flechas, Inicio y Fin recorren las opciones.
 *
 * - Destacado (borde primario) cuando el valor no es el primero (el «todos» del filtro).
 * - Solo tokens; mismas clases que el original para que se vean idénticos.
 */

import { useEffect, useRef, useState, type KeyboardEvent } from 'react';
import { Icono } from './icono';
import type { NombreIcono } from './icono-trazos';

export interface OpcionSelectorToolbar<T extends string | number> {
  valor: T;
  texto: string;
}

export interface SelectorToolbarProps<T extends string | number> {
  id: string;
  etiqueta: string;
  icono: NombreIcono;
  valor: T;
  opciones: OpcionSelectorToolbar<T>[];
  onChange: (valor: T) => void;
  /** Nombre accesible del botón; el valor actual se anuncia como descripción. */
  ariaLabel: string;
}

const BOTON =
  'inline-flex h-12 min-h-12 w-48 min-w-48 items-center justify-between gap-2 rounded-xl border px-3.5 text-xs font-semibold shadow-xs transition-all duration-rapida cursor-pointer select-none focus:outline-none focus-visible:ring-2 focus-visible:ring-primary';
const BOTON_ABIERTO = 'border-primary bg-primary/10 text-primary-text ring-2 ring-primary/20 shadow-1';
const BOTON_DESTACADO =
  'border-primary/60 bg-superficie text-primary-text hover:border-primary hover:bg-superficie/80 hover:shadow-1';
const BOTON_NORMAL =
  'border-panel-border bg-fondo text-body-text hover:border-primary/50 hover:bg-superficie hover:shadow-1';
const OPCION =
  'flex w-full min-h-12 items-center justify-between gap-2 rounded-lg px-3 py-2 text-left text-xs font-semibold transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary';

export function SelectorToolbar<T extends string | number>({
  id,
  etiqueta,
  icono,
  valor,
  opciones,
  onChange,
  ariaLabel,
}: SelectorToolbarProps<T>) {
  const [abierto, setAbierto] = useState(false);
  const contenedor = useRef<HTMLDivElement>(null);
  const boton = useRef<HTMLButtonElement>(null);
  const lista = useRef<HTMLDivElement>(null);
  const actual = opciones.find((o) => o.valor === valor) ?? opciones[0];
  const destacado = opciones.length > 0 && valor !== opciones[0].valor;
  const listaId = `${id}-opciones`;

  useEffect(() => {
    if (!abierto) return;
    function fuera(e: MouseEvent) {
      if (contenedor.current && !contenedor.current.contains(e.target as Node)) setAbierto(false);
    }
    document.addEventListener('mousedown', fuera);
    // Al abrir, el foco va a la opción elegida.
    const elegida = lista.current?.querySelector<HTMLElement>('[aria-selected="true"]')
      ?? lista.current?.querySelector<HTMLElement>('[role="option"]');
    elegida?.focus();
    return () => document.removeEventListener('mousedown', fuera);
  }, [abierto]);

  function cerrar() {
    setAbierto(false);
    boton.current?.focus();
  }

  function elegir(v: T) {
    if (v !== valor) onChange(v);
    cerrar();
  }

  function teclado(e: KeyboardEvent<HTMLDivElement>) {
    const items = Array.from(lista.current?.querySelectorAll<HTMLElement>('[role="option"]') ?? []);
    const i = items.indexOf(document.activeElement as HTMLElement);
    const mover: Record<string, number> = {
      ArrowDown: Math.min(i + 1, items.length - 1),
      ArrowUp: Math.max(i - 1, 0),
      Home: 0,
      End: items.length - 1,
    };
    if (e.key === 'Escape') {
      e.preventDefault();
      cerrar();
    } else if (e.key === 'Tab') {
      setAbierto(false);
    } else if (e.key in mover) {
      e.preventDefault();
      items[mover[e.key]]?.focus();
    }
  }

  return (
    <div ref={contenedor} className="relative">
      <button
        ref={boton}
        id={id}
        type="button"
        onClick={() => setAbierto((v) => !v)}
        aria-haspopup="listbox"
        aria-expanded={abierto}
        aria-controls={abierto ? listaId : undefined}
        aria-label={ariaLabel}
        aria-describedby={`${id}-valor`}
        title={actual?.texto}
        className={`${BOTON} ${abierto ? BOTON_ABIERTO : destacado ? BOTON_DESTACADO : BOTON_NORMAL}`}
      >
        <span className="flex min-w-0 items-center gap-2">
          <Icono nombre={icono} tamano="sm" ariaHidden={true} className="shrink-0 text-primary-text" />
          <span className="flex min-w-0 items-center gap-1.5 whitespace-nowrap">
            <span className="font-medium text-label">{etiqueta}:</span>
            <span id={`${id}-valor`} className="truncate font-bold text-body-text">{actual?.texto}</span>
          </span>
        </span>
        <Icono
          nombre="chevron-abajo"
          tamano="xs"
          ariaHidden={true}
          className={`shrink-0 transition-transform duration-rapida ${abierto ? 'rotate-180 text-primary-text' : 'text-label'}`}
        />
      </button>

      {abierto ? (
        <div
          ref={lista}
          id={listaId}
          role="listbox"
          aria-label={`Opciones: ${etiqueta}`}
          onKeyDown={teclado}
          className="absolute right-0 top-full z-50 mt-1.5 max-h-80 w-60 overflow-y-auto rounded-xl border border-panel-border bg-panel-fill p-1.5 shadow-2 backdrop-blur-md"
        >
          {opciones.map((opcion) => {
            const elegida = opcion.valor === valor;
            return (
              <button
                key={String(opcion.valor)}
                type="button"
                role="option"
                aria-selected={elegida}
                onClick={() => elegir(opcion.valor)}
                className={`${OPCION} ${elegida ? 'bg-primary/15 font-bold text-primary-text' : 'text-body-text hover:bg-surface-container'}`}
              >
                <span className="truncate" title={opcion.texto}>{opcion.texto}</span>
                {elegida ? <Icono nombre="aprobar" tamano="sm" ariaHidden={true} className="shrink-0" /> : null}
              </button>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
