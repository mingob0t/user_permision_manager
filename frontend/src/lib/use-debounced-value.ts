import { useEffect, useState } from 'react';

/** `valor` con retraso: solo cambia cuando deja de modificarse `ms` milisegundos (DIS-156, buscadores). */
export function useDebouncedValue<T>(valor: T, ms: number): T {
  const [retrasado, setRetrasado] = useState(valor);
  useEffect(() => {
    const id = setTimeout(() => setRetrasado(valor), ms);
    return () => clearTimeout(id);
  }, [valor, ms]);
  return retrasado;
}
