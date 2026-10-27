'use client';

import { useEffect, useRef, useState } from 'react';

/** Un estado observable de un elemento: `clave` detecta el cambio, `texto` es lo que se anuncia. */
export interface EstadoObservado {
  clave: string;
  texto: string;
}

/**
 * Anuncia (DIS-050) solo los estados que cambiaron entre una respuesta y la siguiente.
 *
 * - La primera respuesta de cada `contexto` (filtro, página) solo fija la línea base: no se anuncia.
 * - Un refresco sin cambios no produce texto; un elemento nuevo en la lista tampoco.
 * - Devuelve el texto para una región `aria-live` (`RegionDeAnuncios`); `''` si no hay nada.
 */
export function useCambiosDeEstado<T extends { id: number }>(
  items: readonly T[] | undefined,
  contexto: string,
  estadosDe: (item: T) => EstadoObservado[],
): string {
  const [mensaje, setMensaje] = useState('');
  const previo = useRef<{ contexto: string; mapa: Map<string, string> } | null>(null);
  const estadosRef = useRef(estadosDe);
  estadosRef.current = estadosDe;

  useEffect(() => {
    if (!items) return;
    const mapa = new Map<string, string>();
    const cambios: string[] = [];
    const base = previo.current?.contexto === contexto ? previo.current.mapa : null;
    for (const item of items) {
      estadosRef.current(item).forEach(({ clave, texto }, i) => {
        const llave = `${item.id}:${i}`;
        mapa.set(llave, clave);
        const antes = base?.get(llave);
        if (antes !== undefined && antes !== clave) cambios.push(texto);
      });
    }
    previo.current = { contexto, mapa };
    setMensaje(cambios.join('. '));
  }, [items, contexto]);

  return mensaje;
}
