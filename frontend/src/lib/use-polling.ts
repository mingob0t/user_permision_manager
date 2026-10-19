'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { ApiError } from '@/lib/api';
import { useAsync } from '@/lib/use-async';

/**
 * Refresco periódico de datos según ADR-006 y `docs/contratos/README.md`
 * (sección "Refresco"): polling HTTP a la misma ruta de lectura, sin SSE.
 */

/** Límites de `preferences.refresh_interval` (igual que el backend, `crud.py`). */
export const INTERVALO_POLLING_MIN_S = 15;
export const INTERVALO_POLLING_MAX_S = 3600;
/** Valor por defecto de `pref_refresh_interval` en el backend (`auth/models.py`). */
export const INTERVALO_POLLING_POR_DEFECTO_S = 60;
/** Fracción máxima que el *jitter* resta a la espera tras un error. */
export const JITTER_POLLING = 0.1;

const MS_POR_SEGUNDO = 1000;

/** Intervalo válido en segundos: sin valor o inválido usa el por defecto. */
export function normalizarIntervalo(segundos: number | null | undefined): number {
  if (typeof segundos !== 'number' || !Number.isFinite(segundos)) {
    return INTERVALO_POLLING_POR_DEFECTO_S;
  }
  return Math.min(Math.max(segundos, INTERVALO_POLLING_MIN_S), INTERVALO_POLLING_MAX_S);
}

/**
 * Espera en milisegundos hasta la siguiente consulta.
 * Sin fallos: el intervalo. Con fallos: el intervalo duplicado por fallo hasta
 * el máximo, menos un *jitter* aleatorio (nunca supera el máximo).
 */
export function esperaPolling(
  intervaloS: number,
  fallos: number,
  aleatorio: () => number = Math.random,
): number {
  if (fallos <= 0) return intervaloS * MS_POR_SEGUNDO;
  const conBackoff = Math.min(intervaloS * 2 ** fallos, INTERVALO_POLLING_MAX_S);
  return Math.round(conBackoff * (1 - JITTER_POLLING * aleatorio()) * MS_POR_SEGUNDO);
}

function pestanaVisible(): boolean {
  return typeof document === 'undefined' || document.visibilityState !== 'hidden';
}

export interface PollingOptions {
  /** `session.preferences.refresh_interval` (segundos). */
  intervalSeconds?: number | null;
  /** Igual que en `useAsync`: cuándo se recarga por cambio de parámetros. */
  deps?: unknown[];
}

/**
 * `useAsync` con refresco periódico.
 *
 * - Una consulta a la vez: la siguiente se programa al terminar la anterior.
 * - Pestaña oculta: sin consultas; al volver, una consulta inmediata.
 * - Error: *backoff* exponencial con *jitter*; al primer éxito vuelve al intervalo.
 * - `401`: se detiene (la sesión terminó); `refresh()` lo reintenta.
 * - Al desmontar no queda ningún temporizador.
 * - `refresh()`: consulta inmediata; si hay una en curso, se hace al terminar.
 * - `loading` vale `true` en cada consulta y `data` conserva el valor anterior:
 *   la pantalla muestra el indicador de carga solo si aún no hay datos.
 */
export function usePolling<T>(load: () => Promise<T>, options: PollingOptions = {}) {
  const intervalo = normalizarIntervalo(options.intervalSeconds);
  const ultimoError = useRef<unknown>(null);
  const turno = useRef(0);

  // Se guarda el error original (useAsync solo conserva el mensaje) para
  // distinguir el 401. Solo cuenta la consulta más reciente.
  const { data, loading, error, reload } = useAsync<T>(async () => {
    const mio = ++turno.current;
    try {
      const resultado = await load();
      if (mio === turno.current) ultimoError.current = null;
      return resultado;
    } catch (e) {
      if (mio === turno.current) ultimoError.current = e;
      throw e;
    }
  }, options.deps ?? []);

  const [fallos, setFallos] = useState(0);
  const [detenido, setDetenido] = useState(false);
  const [visible, setVisible] = useState(pestanaVisible);

  const recargar = useRef(reload);
  const cargando = useRef(loading);
  const pendiente = useRef(false);
  useEffect(() => {
    recargar.current = reload;
  });

  // Marca la consulta en curso antes del siguiente render para no solaparla.
  const consultar = useCallback(() => {
    cargando.current = true;
    recargar.current();
  }, []);

  // Al terminar cada consulta: cuenta fallos, detiene con 401 o atiende un
  // refresco manual pedido mientras estaba en curso.
  useEffect(() => {
    cargando.current = loading;
    if (loading) return;
    if (error) {
      const e = ultimoError.current;
      if (e instanceof ApiError && e.isUnauthenticated) setDetenido(true);
      else setFallos((n) => n + 1);
    } else {
      setFallos(0);
      setDetenido(false);
    }
    if (pendiente.current) {
      pendiente.current = false;
      consultar();
    }
  }, [loading, error, consultar]);

  useEffect(() => {
    const alCambiar = () => setVisible(pestanaVisible());
    document.addEventListener('visibilitychange', alCambiar);
    return () => document.removeEventListener('visibilitychange', alCambiar);
  }, []);

  // Al volver a la pestaña: consulta inmediata (si no hay una en curso).
  const visibleAntes = useRef(visible);
  useEffect(() => {
    const volvio = visible && !visibleAntes.current;
    visibleAntes.current = visible;
    if (volvio && !detenido && !cargando.current) consultar();
  }, [visible, detenido, consultar]);

  // Siguiente consulta programada solo sin consulta en curso y con la pestaña visible.
  useEffect(() => {
    if (loading || !visible || detenido) return;
    const id = setTimeout(consultar, esperaPolling(intervalo, fallos));
    return () => clearTimeout(id);
  }, [loading, visible, detenido, intervalo, fallos, consultar]);

  const refresh = useCallback(() => {
    if (cargando.current) pendiente.current = true;
    else consultar();
  }, [consultar]);

  return { data, loading, error, refresh };
}
