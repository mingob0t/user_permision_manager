'use client';

import { useCallback, useEffect, useState } from 'react';

interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

/**
 * Carga datos de la API y expone estado de carga y error.
 *
 * `deps` controla cuándo se recarga; `reload` fuerza una recarga manual tras
 * una mutación.
 */
export function useAsync<T>(
  load: () => Promise<T>,
  deps: unknown[] = [],
): AsyncState<T> & { reload: () => void } {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    loading: true,
    error: null,
  });
  const [nonce, setNonce] = useState(0);

  // `load` se recrea en cada render; las dependencias declaradas por quien
  // llama son las que deciden la recarga. La regla no puede analizar `deps`
  // porque llega como parámetro; es intencional.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const runner = useCallback(load, deps);

  useEffect(() => {
    let active = true;
    setState((prev) => ({ ...prev, loading: true, error: null }));

    runner()
      .then((data) => {
        if (active) setState({ data, loading: false, error: null });
      })
      .catch((error: unknown) => {
        if (!active) return;
        setState({
          data: null,
          loading: false,
          error: error instanceof Error ? error.message : 'Error al cargar',
        });
      });

    return () => { active = false; };
  }, [runner, nonce]);

  return { ...state, reload: () => setNonce((n) => n + 1) };
}
