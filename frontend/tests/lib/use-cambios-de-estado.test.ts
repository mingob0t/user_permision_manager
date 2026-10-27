/** DIS-050: salidas de la lista por el filtro (misma página, `total` a la baja). */
import { renderHook } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { useCambiosDeEstado } from '@/lib/use-cambios-de-estado';

interface Fila { id: number }
const estados = (f: Fila) => [{ clave: 'a', texto: `Fila ${f.id}` }];
const salida = (f: Fila) => `Fila ${f.id} ya no está en “X”`;

function montar(items: Fila[], contexto: string, total: number, conFiltro = true) {
  return renderHook(
    (p: { items: Fila[]; contexto: string; total: number }) =>
      useCambiosDeEstado(p.items, p.contexto, estados, { total: p.total, salida: conFiltro ? salida : undefined }),
    { initialProps: { items, contexto, total } },
  );
}

describe('useCambiosDeEstado: salidas', () => {
  it('con filtro, el elemento que sale y baja el total se anuncia', () => {
    const h = montar([{ id: 1 }, { id: 2 }], 'f:1', 2);
    h.rerender({ items: [{ id: 2 }], contexto: 'f:1', total: 1 });
    expect(h.result.current).toBe('Fila 1 ya no está en “X”');
  });

  it('sin filtro no se anuncia la salida', () => {
    const h = montar([{ id: 1 }, { id: 2 }], 'f:1', 2, false);
    h.rerender({ items: [{ id: 2 }], contexto: 'f:1', total: 1 });
    expect(h.result.current).toBe('');
  });

  it('un cambio de página no anuncia salidas', () => {
    const h = montar([{ id: 1 }, { id: 2 }], 'f:1', 40);
    h.rerender({ items: [{ id: 3 }], contexto: 'f:2', total: 40 });
    expect(h.result.current).toBe('');
  });

  it('si el total no baja (la paginación solo desplaza) no se anuncia', () => {
    const h = montar([{ id: 1 }, { id: 2 }], 'f:1', 40);
    h.rerender({ items: [{ id: 2 }, { id: 3 }], contexto: 'f:1', total: 40 });
    expect(h.result.current).toBe('');
  });
});
