/**
 * Pruebas de `usePolling` (FNC-071, ADR-006) con temporizadores simulados.
 */
import { act, cleanup, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '@/lib/api';
import {
  INTERVALO_POLLING_MAX_S,
  INTERVALO_POLLING_MIN_S,
  INTERVALO_POLLING_POR_DEFECTO_S,
  JITTER_POLLING,
  esperaPolling,
  normalizarIntervalo,
  usePolling,
} from '@/lib/use-polling';

const S = 1000;

let visibilidad: DocumentVisibilityState = 'visible';

function cambiarVisibilidad(estado: DocumentVisibilityState) {
  visibilidad = estado;
  document.dispatchEvent(new Event('visibilitychange'));
}

/** Avanza el reloj y deja resolver las promesas pendientes. */
async function avanzar(ms: number) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
}

beforeEach(() => {
  vi.useFakeTimers();
  visibilidad = 'visible';
  vi.spyOn(document, 'visibilityState', 'get').mockImplementation(() => visibilidad);
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

describe('normalizarIntervalo y esperaPolling', () => {
  it('acota el intervalo a 15–3600 s y usa el por defecto si no hay valor', () => {
    expect(normalizarIntervalo(5)).toBe(INTERVALO_POLLING_MIN_S);
    expect(normalizarIntervalo(99999)).toBe(INTERVALO_POLLING_MAX_S);
    expect(normalizarIntervalo(undefined)).toBe(INTERVALO_POLLING_POR_DEFECTO_S);
    expect(normalizarIntervalo(Number.NaN)).toBe(INTERVALO_POLLING_POR_DEFECTO_S);
    expect(normalizarIntervalo(45)).toBe(45);
  });

  it('duplica la espera por fallo hasta el máximo y el jitter solo la reduce', () => {
    const sinJitter = () => 0;
    expect(esperaPolling(30, 0, sinJitter)).toBe(30 * S);
    expect(esperaPolling(30, 1, sinJitter)).toBe(60 * S);
    expect(esperaPolling(30, 3, sinJitter)).toBe(240 * S);
    expect(esperaPolling(30, 20, sinJitter)).toBe(INTERVALO_POLLING_MAX_S * S);
    expect(esperaPolling(30, 20, () => 1)).toBe(
      Math.round(INTERVALO_POLLING_MAX_S * (1 - JITTER_POLLING) * S),
    );
  });
});

describe('usePolling', () => {
  it('respeta el intervalo de la preferencia del usuario', async () => {
    const load = vi.fn().mockResolvedValue('ok');
    const { result } = renderHook(() => usePolling(load, { intervalSeconds: 30 }));
    await avanzar(0);
    expect(load).toHaveBeenCalledTimes(1);
    expect(result.current.data).toBe('ok');

    await avanzar(30 * S - 1);
    expect(load).toHaveBeenCalledTimes(1);
    await avanzar(1);
    expect(load).toHaveBeenCalledTimes(2);
    await avanzar(30 * S);
    expect(load).toHaveBeenCalledTimes(3);
  });

  it('usa el mínimo de 15 s aunque la preferencia sea menor', async () => {
    const load = vi.fn().mockResolvedValue('ok');
    renderHook(() => usePolling(load, { intervalSeconds: 1 }));
    await avanzar(0);
    await avanzar(14 * S);
    expect(load).toHaveBeenCalledTimes(1);
    await avanzar(1 * S);
    expect(load).toHaveBeenCalledTimes(2);
  });

  it('con la pestaña oculta no consulta y al volver consulta de inmediato', async () => {
    const load = vi.fn().mockResolvedValue('ok');
    renderHook(() => usePolling(load, { intervalSeconds: 15 }));
    await avanzar(0);
    expect(load).toHaveBeenCalledTimes(1);

    act(() => cambiarVisibilidad('hidden'));
    await avanzar(INTERVALO_POLLING_MAX_S * S);
    expect(load).toHaveBeenCalledTimes(1);

    act(() => cambiarVisibilidad('visible'));
    await avanzar(0);
    expect(load).toHaveBeenCalledTimes(2);
    await avanzar(15 * S);
    expect(load).toHaveBeenCalledTimes(3);
  });

  it('tras errores la espera crece hasta el máximo y se restablece al primer éxito', async () => {
    vi.spyOn(Math, 'random').mockReturnValue(0);
    const load = vi.fn().mockRejectedValue(new ApiError(500, 'falla'));
    const { result } = renderHook(() => usePolling(load, { intervalSeconds: 600 }));
    await avanzar(0);
    expect(load).toHaveBeenCalledTimes(1);
    expect(result.current.error).toBe('falla');

    // 1.er fallo: 1200 s; 2.º: 2400 s; 3.º en adelante: tope de 3600 s.
    await avanzar(1200 * S - 1);
    expect(load).toHaveBeenCalledTimes(1);
    await avanzar(1);
    expect(load).toHaveBeenCalledTimes(2);
    await avanzar(2400 * S);
    expect(load).toHaveBeenCalledTimes(3);
    await avanzar(3600 * S - 1);
    expect(load).toHaveBeenCalledTimes(3);
    await avanzar(1);
    expect(load).toHaveBeenCalledTimes(4);

    load.mockResolvedValue('ok');
    await avanzar(3600 * S);
    expect(load).toHaveBeenCalledTimes(5);
    expect(result.current.data).toBe('ok');
    expect(result.current.error).toBeNull();

    // Primer éxito: vuelve al intervalo de 600 s.
    await avanzar(600 * S);
    expect(load).toHaveBeenCalledTimes(6);
  });

  it('no solapa consultas: la siguiente espera a que termine la anterior', async () => {
    let resolver: (v: string) => void = () => {};
    const load = vi.fn(() => new Promise<string>((r) => { resolver = r; }));
    const { result } = renderHook(() => usePolling(load, { intervalSeconds: 15 }));
    await avanzar(0);
    await avanzar(10 * 15 * S);
    expect(load).toHaveBeenCalledTimes(1);

    // Refresco manual en curso: se atiende al terminar, sin solapar.
    act(() => result.current.refresh());
    act(() => result.current.refresh());
    expect(load).toHaveBeenCalledTimes(1);
    await act(async () => { resolver('a'); });
    await avanzar(0);
    expect(load).toHaveBeenCalledTimes(2);
  });

  it('refresh() consulta de inmediato sin esperar el intervalo', async () => {
    const load = vi.fn().mockResolvedValue('ok');
    const { result } = renderHook(() => usePolling(load, { intervalSeconds: 60 }));
    await avanzar(0);
    act(() => result.current.refresh());
    await avanzar(0);
    expect(load).toHaveBeenCalledTimes(2);
  });

  it('un 401 detiene el polling', async () => {
    const load = vi.fn().mockRejectedValue(new ApiError(401, 'sin sesión'));
    renderHook(() => usePolling(load, { intervalSeconds: 15 }));
    await avanzar(0);
    await avanzar(INTERVALO_POLLING_MAX_S * 2 * S);
    expect(load).toHaveBeenCalledTimes(1);
  });

  it('tras un fallo conserva el último dato válido y expone el error (revisión)', async () => {
    const load = vi.fn().mockResolvedValue('ok');
    const { result } = renderHook(() => usePolling(load, { intervalSeconds: 15 }));
    await avanzar(0);
    expect(result.current.data).toBe('ok');

    load.mockRejectedValue(new ApiError(500, 'falla'));
    await avanzar(15 * S);
    expect(load).toHaveBeenCalledTimes(2);
    expect(result.current.error).toBe('falla');
    expect(result.current.data).toBe('ok');
  });

  it('DIS-024: durante el reintento tras un fallo conserva el último dato válido', async () => {
    const load = vi.fn().mockResolvedValue('ok');
    const { result } = renderHook(() => usePolling(load, { intervalSeconds: 15 }));
    await avanzar(0);
    load.mockRejectedValueOnce(new ApiError(500, 'falla'));
    await avanzar(15 * S);
    expect(result.current.error).toBe('falla');

    // Reintento en curso: `useAsync` deja `error` en null y `data` en null.
    load.mockReturnValueOnce(new Promise(() => {}));
    await avanzar(esperaPolling(15, 1, () => 0));
    expect(result.current.loading).toBe(true);
    expect(result.current.error).toBeNull();
    expect(result.current.data).toBe('ok');
  });

  it('un error con mensaje vacío cuenta como fallo (revisión)', async () => {
    vi.spyOn(Math, 'random').mockReturnValue(0);
    const load = vi.fn().mockRejectedValue(new Error(''));
    renderHook(() => usePolling(load, { intervalSeconds: 15 }));
    await avanzar(0);
    // Con backoff la siguiente es a los 30 s, no a los 15 s.
    await avanzar(30 * S - 1);
    expect(load).toHaveBeenCalledTimes(1);
    await avanzar(1);
    expect(load).toHaveBeenCalledTimes(2);
  });

  it('refresh() reanuda el polling tras un 401 (revisión)', async () => {
    const load = vi.fn().mockRejectedValue(new ApiError(401, 'sin sesión'));
    const { result } = renderHook(() => usePolling(load, { intervalSeconds: 15 }));
    await avanzar(0);
    await avanzar(60 * S);
    expect(load).toHaveBeenCalledTimes(1);

    load.mockResolvedValue('ok');
    act(() => result.current.refresh());
    await avanzar(0);
    expect(load).toHaveBeenCalledTimes(2);
    expect(result.current.data).toBe('ok');
    await avanzar(15 * S);
    expect(load).toHaveBeenCalledTimes(3);
  });

  it('un 403 no detiene: sigue con backoff (revisión)', async () => {
    vi.spyOn(Math, 'random').mockReturnValue(0);
    const load = vi.fn().mockRejectedValue(new ApiError(403, 'prohibido'));
    renderHook(() => usePolling(load, { intervalSeconds: 15 }));
    await avanzar(0);
    await avanzar(30 * S - 1);
    expect(load).toHaveBeenCalledTimes(1);
    await avanzar(1);
    expect(load).toHaveBeenCalledTimes(2);
    await avanzar(60 * S);
    expect(load).toHaveBeenCalledTimes(3);
  });

  it('al desmontar no hay más consultas ni temporizadores', async () => {
    const load = vi.fn().mockResolvedValue('ok');
    const { unmount } = renderHook(() => usePolling(load, { intervalSeconds: 15 }));
    await avanzar(0);
    unmount();
    expect(vi.getTimerCount()).toBe(0);
    await avanzar(INTERVALO_POLLING_MAX_S * S);
    expect(load).toHaveBeenCalledTimes(1);
  });
});
