'use client';

import { useEffect, useRef, useState } from 'react';

/** Un estado observable de un elemento: `clave` detecta el cambio, `texto` es lo que se anuncia. */
export interface EstadoObservado {
  clave: string;
  texto: string;
}

/** Salidas por filtro: sin `salida` (sin filtro activo) no se anuncian. */
export interface OpcionesDeSalida<T> {
  /** `total` de la respuesta: solo si baja respecto de la anterior hay una salida real. */
  total: number;
  /** Texto de un elemento que ya no cumple el filtro; `undefined` si no hay filtro de estado. */
  salida?: (item: T) => string;
}

/**
 * Anuncia (DIS-050) solo los estados que cambiaron entre una respuesta y la siguiente.
 *
 * - La primera respuesta de cada `contexto` (filtro, página) solo fija la línea base: no se anuncia.
 * - Un refresco sin cambios no produce texto; un elemento nuevo en la lista tampoco.
 * - Un `texto` vacío no se anuncia (estado que no aplica, por ejemplo sin acceso).
 * - Con `salida` y `total` anuncia los elementos que dejan la lista por el filtro, solo en el mismo
 *   contexto y si el total bajó (la paginación que solo desplaza elementos no cuenta).
 * - Devuelve el texto para una región `aria-live` (`RegionDeAnuncios`); `''` si no hay nada.
 */
export function useCambiosDeEstado<T extends { id: number }>(
  items: readonly T[] | undefined,
  contexto: string,
  estadosDe: (item: T) => EstadoObservado[],
  opciones?: OpcionesDeSalida<T>,
): string {
  const [mensaje, setMensaje] = useState('');
  const previo = useRef<{
    contexto: string;
    mapa: Map<string, string>;
    salidas: Map<number, string>;
    total: number | undefined;
  } | null>(null);
  const estadosRef = useRef(estadosDe);
  estadosRef.current = estadosDe;
  const opcionesRef = useRef(opciones);
  opcionesRef.current = opciones;

  useEffect(() => {
    if (!items) return;
    const mapa = new Map<string, string>();
    const cambios: string[] = [];
    const anterior = previo.current?.contexto === contexto ? previo.current : null;
    const base = anterior?.mapa ?? null;
    const salidas = new Map<number, string>();
    const { total, salida } = opcionesRef.current ?? {};
    for (const item of items) {
      if (salida) salidas.set(item.id, salida(item));
      estadosRef.current(item).forEach(({ clave, texto }, i) => {
        const llave = `${item.id}:${i}`;
        mapa.set(llave, clave);
        const antes = base?.get(llave);
        if (texto && antes !== undefined && antes !== clave) cambios.push(texto);
      });
    }
    if (anterior && salida && total !== undefined && anterior.total !== undefined && total < anterior.total) {
      const actuales = new Set(items.map((i) => i.id));
      anterior.salidas.forEach((texto, id) => {
        if (!actuales.has(id)) cambios.push(texto);
      });
    }
    previo.current = { contexto, mapa, salidas, total };
    setMensaje(cambios.join('. '));
  }, [items, contexto]);

  return mensaje;
}
