'use client';

/**
 * Toast común (DIS-010, H-17): aviso breve y no bloqueante para confirmar o
 * fallar una acción, sin sustituir al error en línea de un formulario.
 *
 * - `ToastProvider` va una vez, en `layout.tsx`; `useToast()` devuelve
 *   `avisar(tono, texto)` y `cerrar(id)`. Fuera del proveedor no hace nada.
 * - Dos regiones vivas siempre montadas: `role="status"` (éxito e info,
 *   cortés) y `role="alert"` (error, asertiva).
 * - Éxito e info se cierran solos tras `TOAST_MS`; el error se queda hasta que
 *   se cierra (no se pierde un fallo por tardar en leerlo). Todos tienen botón
 *   "Cerrar aviso" de 48 px.
 * - DIS-049: el temporizador se pausa mientras el cursor (ratón, no toque) o el foco están sobre
 *   el aviso y vuelve a correr completo al salir (WCAG 2.2.1).
 * - DIS-049: con un diálogo abierto, la región de avisos entra en el ciclo de
 *   Tab de la trampa de foco (`data-fuera-de-trampa`), así "Cerrar aviso" se
 *   alcanza con el teclado.
 * - Se pinta en un portal en `document.body`, fuera de la raíz de la app, que
 *   queda `inert` bajo un diálogo (DIS-038), así que el aviso sigue legible.
 * - Solo tokens: `bg-panel-fill`, `border-<tono>` y texto `*-text` (pares ya
 *   medidos sobre el panel, AA en los dos temas).
 */

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';

/** Milisegundos que permanecen los avisos de éxito e info. */
export const TOAST_MS = 6000;

export type ToastTone = 'success' | 'error' | 'warning' | 'info';

type Aviso = { id: number; tono: ToastTone; texto: string };

type ToastApi = {
  avisar: (tono: ToastTone, texto: string) => number;
  cerrar: (id: number) => void;
};

const SIN_PROVEEDOR: ToastApi = { avisar: () => 0, cerrar: () => undefined };

const ToastContext = createContext<ToastApi>(SIN_PROVEEDOR);

export function useToast(): ToastApi {
  return useContext(ToastContext);
}

const CLASE_TONO: Record<ToastTone, string> = {
  success: 'border-success/40 text-success-text',
  error: 'border-error/40 text-error-text',
  warning: 'border-warning/40 text-warning-text',
  info: 'border-panel-border text-body-text',
};

type PropsTarjeta = {
  aviso: Aviso;
  onCerrar: (id: number) => void;
  onPausa: (id: number) => void;
  onReanudar: (id: number) => void;
};

function Tarjeta({ aviso, onCerrar, onPausa, onReanudar }: PropsTarjeta) {
  const encima = useRef({ cursor: false, foco: false });
  const actualizar = (parte: Partial<typeof encima.current>) => {
    encima.current = { ...encima.current, ...parte };
    if (aviso.tono === 'error') return; // persistente: no hay temporizador que pausar
    if (encima.current.cursor || encima.current.foco) onPausa(aviso.id);
    else onReanudar(aviso.id);
  };
  return (
    <div
      onPointerEnter={(evento) => {
        if (evento.pointerType === 'mouse') actualizar({ cursor: true });
      }}
      onPointerLeave={(evento) => {
        if (evento.pointerType === 'mouse') actualizar({ cursor: false });
      }}
      onFocus={() => actualizar({ foco: true })}
      onBlur={(evento) => {
        if (!evento.currentTarget.contains(evento.relatedTarget)) actualizar({ foco: false });
      }}
      className={`pointer-events-auto flex items-center gap-2 rounded-xl border bg-panel-fill py-1 pl-4 pr-1 shadow-lg ${CLASE_TONO[aviso.tono]}`}
    >
      <p className="flex-1 text-sm font-bold">{aviso.texto}</p>
      <button
        type="button"
        onClick={() => onCerrar(aviso.id)}
        aria-label="Cerrar aviso"
        className="inline-flex min-h-12 min-w-12 shrink-0 items-center justify-center rounded text-label outline-none hover:bg-surface-container focus-visible:ring-2 focus-visible:ring-primary"
      >
        ✕
      </button>
    </div>
  );
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [avisos, setAvisos] = useState<Aviso[]>([]);
  const [montado, setMontado] = useState(false);
  const siguiente = useRef(1);
  const temporizadores = useRef(new Map<number, ReturnType<typeof setTimeout>>());

  useEffect(() => {
    setMontado(true);
    const activos = temporizadores.current;
    return () => {
      activos.forEach(clearTimeout);
      activos.clear();
    };
  }, []);

  const cerrar = useCallback((id: number) => {
    const temporizador = temporizadores.current.get(id);
    if (temporizador) clearTimeout(temporizador);
    temporizadores.current.delete(id);
    setAvisos((actuales) => actuales.filter((aviso) => aviso.id !== id));
  }, []);

  const avisar = useCallback(
    (tono: ToastTone, texto: string) => {
      const id = siguiente.current++;
      setAvisos((actuales) => [...actuales, { id, tono, texto }]);
      if (tono !== 'error') temporizadores.current.set(id, setTimeout(() => cerrar(id), TOAST_MS));
      return id;
    },
    [cerrar],
  );

  const pausar = useCallback((id: number) => {
    const temporizador = temporizadores.current.get(id);
    if (temporizador) clearTimeout(temporizador);
    temporizadores.current.delete(id);
  }, []);

  const reanudar = useCallback(
    (id: number) => {
      if (temporizadores.current.has(id)) return;
      temporizadores.current.set(id, setTimeout(() => cerrar(id), TOAST_MS));
    },
    [cerrar],
  );

  const api = useMemo(() => ({ avisar, cerrar }), [avisar, cerrar]);

  return (
    <ToastContext.Provider value={api}>
      {children}
      {montado
        ? createPortal(
            <div data-fuera-de-trampa className="pointer-events-none fixed inset-x-4 bottom-4 z-60 flex flex-col items-end gap-2 sm:left-auto sm:w-96">
              <div role="status" className="flex w-full flex-col gap-2">
                {avisos
                  .filter((aviso) => aviso.tono !== 'error')
                  .map((aviso) => <Tarjeta key={aviso.id} aviso={aviso} onCerrar={cerrar} onPausa={pausar} onReanudar={reanudar} />)}
              </div>
              <div role="alert" className="flex w-full flex-col gap-2">
                {avisos
                  .filter((aviso) => aviso.tono === 'error')
                  .map((aviso) => <Tarjeta key={aviso.id} aviso={aviso} onCerrar={cerrar} onPausa={pausar} onReanudar={reanudar} />)}
              </div>
            </div>,
            document.body,
          )
        : null}
    </ToastContext.Provider>
  );
}
