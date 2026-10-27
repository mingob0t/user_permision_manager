/**
 * DIS-010: componentes comunes nuevos o unificados: `DataTable`, `FilterBar`,
 * `SuccessNote`, variante `danger` de `Button` y `Toast`.
 */
import { useState } from 'react';
import { act, cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { DataTable, type DataColumn } from '@/components/data-table';
import { FILTRO_BUSQUEDA, FilterBar } from '@/components/filter-bar';
import { Button, Modal, Select, TextInput } from '@/components/form';
import { TOAST_MS, ToastProvider, useToast } from '@/components/toast';
import { SuccessNote } from '@/components/ui';
import { crearRaiz, simularCajas } from '../utils/dom-simulado';

afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

type Fila = { id: number; nombre: string };
const COLUMNAS: DataColumn<Fila>[] = [
  { key: 'nombre', header: 'Nombre', cell: (fila) => fila.nombre },
  { key: 'acciones', header: 'Acciones', headerSrOnly: true, cell: (fila) => <button type="button">Editar {fila.nombre}</button> },
];

function tabla(props: Partial<React.ComponentProps<typeof DataTable<Fila>>> = {}) {
  return render(
    <DataTable<Fila>
      label="Cosas"
      columns={COLUMNAS}
      rows={[{ id: 1, nombre: 'Uno' }, { id: 2, nombre: 'Dos' }]}
      rowKey={(fila) => fila.id}
      emptyMessage="Sin cosas."
      {...props}
    />,
  );
}

describe('DataTable', () => {
  it('pinta región con nombre y foco por teclado, encabezados y filas', () => {
    tabla();
    const region = screen.getByRole('region', { name: 'Cosas' });
    expect(region).toHaveProperty('tabIndex', 0);
    expect(screen.getAllByRole('columnheader').map((th) => th.textContent)).toEqual(['Nombre', 'Acciones']);
    expect(screen.getAllByRole('columnheader')[0].getAttribute('scope')).toBe('col');
    expect(within(screen.getAllByRole('columnheader')[1]).getByText('Acciones').className).toContain('sr-only');
    expect(screen.getAllByRole('row')).toHaveLength(3);
    expect(screen.getByRole('button', { name: 'Editar Dos' })).toBeTruthy();
  });

  it('carga, error y vacío reemplazan la tabla', () => {
    tabla({ loading: true });
    expect(screen.getByRole('status').textContent).toContain('Cargando');
    expect(screen.queryByRole('table')).toBeNull();
    cleanup();
    tabla({ error: 'Falló la carga.' });
    expect(screen.getByRole('alert').textContent).toBe('Falló la carga.');
    expect(screen.queryByRole('table')).toBeNull();
    cleanup();
    tabla({ rows: [] });
    expect(screen.getByText('Sin cosas.')).toBeTruthy();
    expect(screen.queryByRole('table')).toBeNull();
  });

  it('sin estilos inline ni colores literales en su marcado', () => {
    const { container } = tabla();
    expect(container.innerHTML).not.toMatch(/style=|#[0-9a-f]{3,6}\b|rgb\(/i);
  });
});

describe('FilterBar', () => {
  it('es una búsqueda con nombre que agrupa los controles de form.tsx', () => {
    render(
      <FilterBar label="Filtros de cosas">
        <TextInput type="search" aria-label="Buscar" className={FILTRO_BUSQUEDA} />
        <Select aria-label="Área"><option value="">Todas</option></Select>
      </FilterBar>,
    );
    const barra = screen.getByRole('search', { name: 'Filtros de cosas' });
    expect(within(barra).getByRole('searchbox', { name: 'Buscar' }).className).toContain('h-12');
    expect(within(barra).getByRole('combobox', { name: 'Área' }).className).toContain('h-12');
  });
});

describe('SuccessNote y Button danger', () => {
  it('SuccessNote usa el texto de éxito por token', () => {
    render(<SuccessNote>Listo.</SuccessNote>);
    expect(screen.getByText('Listo.').className).toContain('text-success-text');
  });

  it('Button danger usa .nexus-btn-danger, sin overrides de Tailwind', () => {
    render(<Button variant="danger">Eliminar</Button>);
    const clases = screen.getByRole('button', { name: 'Eliminar' }).className;
    expect(clases).toContain('nexus-btn-danger');
    expect(clases).not.toContain('nexus-btn-primary');
    expect(clases).not.toMatch(/!bg-|!text-/);
  });
});

function Disparador() {
  const { avisar } = useToast();
  return (
    <>
      <button type="button" onClick={() => avisar('success', 'Guardado.')}>ok</button>
      <button type="button" onClick={() => avisar('error', 'Falló.')}>mal</button>
    </>
  );
}

describe('Toast', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  it('éxito en región de estado, se cierra solo tras TOAST_MS', () => {
    render(<ToastProvider><Disparador /></ToastProvider>);
    fireEvent.click(screen.getByRole('button', { name: 'ok' }));
    const aviso = screen.getByText('Guardado.');
    expect(aviso.closest('[role="status"]')).toBeTruthy();
    act(() => { vi.advanceTimersByTime(TOAST_MS + 10); });
    expect(screen.queryByText('Guardado.')).toBeNull();
  });

  it('error en región de alerta, no se cierra solo y se cierra con el botón', () => {
    render(<ToastProvider><Disparador /></ToastProvider>);
    fireEvent.click(screen.getByRole('button', { name: 'mal' }));
    expect(screen.getByText('Falló.').closest('[role="alert"]')).toBeTruthy();
    act(() => { vi.advanceTimersByTime(TOAST_MS * 5); });
    expect(screen.getByText('Falló.')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Cerrar aviso' }));
    expect(screen.queryByText('Falló.')).toBeNull();
  });

  it('fuera del proveedor useToast no falla ni pinta nada', () => {
    render(<Disparador />);
    fireEvent.click(screen.getByRole('button', { name: 'mal' }));
    expect(screen.queryByText('Falló.')).toBeNull();
  });

  it('sin estilos inline en el aviso', () => {
    render(<ToastProvider><Disparador /></ToastProvider>);
    fireEvent.click(screen.getByRole('button', { name: 'ok' }));
    expect(document.body.innerHTML).not.toMatch(/style=/);
  });

  it('DIS-049: el éxito se pausa con el cursor y reanuda completo al salir', () => {
    render(<ToastProvider><Disparador /></ToastProvider>);
    fireEvent.click(screen.getByRole('button', { name: 'ok' }));
    const tarjeta = screen.getByText('Guardado.').parentElement as HTMLElement;
    fireEvent.pointerEnter(tarjeta, { pointerType: 'mouse' });
    act(() => { vi.advanceTimersByTime(TOAST_MS * 5); });
    expect(screen.getByText('Guardado.')).toBeTruthy();
    fireEvent.pointerLeave(tarjeta, { pointerType: 'mouse' });
    act(() => { vi.advanceTimersByTime(TOAST_MS - 100); });
    expect(screen.getByText('Guardado.')).toBeTruthy();
    act(() => { vi.advanceTimersByTime(200); });
    expect(screen.queryByText('Guardado.')).toBeNull();
  });

  it('DIS-049: el éxito se pausa con el foco y reanuda al salir; con cursor y foco espera a ambos', () => {
    render(<ToastProvider><Disparador /></ToastProvider>);
    fireEvent.click(screen.getByRole('button', { name: 'ok' }));
    const boton = screen.getByRole('button', { name: 'Cerrar aviso' });
    const tarjeta = boton.parentElement as HTMLElement;
    fireEvent.focus(boton);
    fireEvent.pointerEnter(tarjeta, { pointerType: 'mouse' });
    fireEvent.pointerLeave(tarjeta, { pointerType: 'mouse' });
    act(() => { vi.advanceTimersByTime(TOAST_MS * 3); });
    expect(screen.getByText('Guardado.')).toBeTruthy();
    fireEvent.blur(boton);
    act(() => { vi.advanceTimersByTime(TOAST_MS + 10); });
    expect(screen.queryByText('Guardado.')).toBeNull();
  });

  it('DIS-049: el error sigue sin temporizador tras pasar el cursor', () => {
    render(<ToastProvider><Disparador /></ToastProvider>);
    fireEvent.click(screen.getByRole('button', { name: 'mal' }));
    const tarjeta = screen.getByText('Falló.').parentElement as HTMLElement;
    fireEvent.pointerEnter(tarjeta, { pointerType: 'mouse' });
    fireEvent.pointerLeave(tarjeta, { pointerType: 'mouse' });
    act(() => { vi.advanceTimersByTime(TOAST_MS * 5); });
    expect(screen.getByText('Falló.')).toBeTruthy();
  });

  it('DIS-049: con un diálogo abierto (raíz inert, trampa de foco) Tab llega a "Cerrar aviso" y vuelve al diálogo', () => {
    function Caso() {
      const { avisar } = useToast();
      return (
        <>
          <button type="button" onClick={() => avisar('error', 'Falló.')}>mal</button>
          <Modal title="Diálogo" onClose={() => undefined}><input aria-label="Campo" /></Modal>
        </>
      );
    }
    const cajas = simularCajas();
    const raiz = crearRaiz();
    render(<ToastProvider><Caso /></ToastProvider>, { container: raiz });
    expect(raiz.hasAttribute('inert')).toBe(true); // el aviso vive fuera de la raíz bloqueada
    fireEvent.click(screen.getByRole('button', { name: 'mal' }));
    const campo = screen.getByLabelText('Campo');
    const cerrarAviso = screen.getByRole('button', { name: 'Cerrar aviso' });
    campo.focus();
    fireEvent.keyDown(campo, { key: 'Tab' }); // último del diálogo: salta al aviso
    expect(document.activeElement).toBe(cerrarAviso);
    fireEvent.keyDown(cerrarAviso, { key: 'Tab' }); // último del ciclo: vuelve al primero
    expect(document.activeElement).toBe(screen.getByRole('button', { name: 'Cerrar' }));
    fireEvent.keyDown(document.activeElement as Element, { key: 'Tab', shiftKey: true });
    expect(document.activeElement).toBe(cerrarAviso);
    fireEvent.click(cerrarAviso);
    expect(screen.queryByText('Falló.')).toBeNull();
    cajas.mockRestore();
  });

  it('DIS-049: al cerrar el aviso con el diálogo abierto el foco vuelve al diálogo (clic y cierre programático)', async () => {
    let cerrarAviso: (id: number) => void = () => undefined;
    function Caso() {
      const { avisar, cerrar } = useToast();
      cerrarAviso = cerrar;
      return (
        <>
          <button type="button" onClick={() => { avisar('error', 'Falló.'); avisar('success', 'Listo.'); }}>mal</button>
          <Modal title="Diálogo" onClose={() => undefined}><input aria-label="Campo" /></Modal>
        </>
      );
    }
    const cajas = simularCajas();
    render(<ToastProvider><Caso /></ToastProvider>, { container: crearRaiz() });
    fireEvent.click(screen.getByRole('button', { name: 'mal' }));
    const dialogo = screen.getByRole('dialog');
    const [botonExito, botonError] = screen.getAllByRole('button', { name: 'Cerrar aviso' });
    botonError.focus();
    fireEvent.click(botonError);
    await act(async () => { await Promise.resolve(); });
    expect(dialogo.contains(document.activeElement)).toBe(true);
    botonExito.focus();
    act(() => { cerrarAviso(1 + 1); });
    await act(async () => { await Promise.resolve(); });
    expect(screen.queryByText('Listo.')).toBeNull();
    expect(dialogo.contains(document.activeElement)).toBe(true);
    cajas.mockRestore();
  });

  it('DIS-049: Escape con el foco en el aviso cierra el diálogo y el foco vuelve al disparador', () => {
    function Caso() {
      const { avisar } = useToast();
      const [abierto, setAbierto] = useState(false);
      return (
        <>
          <button type="button" onClick={() => { avisar('error', 'Falló.'); setAbierto(true); }}>abrir</button>
          {abierto ? <Modal title="Diálogo" onClose={() => setAbierto(false)}><input aria-label="Campo" /></Modal> : null}
        </>
      );
    }
    const cajas = simularCajas();
    render(<ToastProvider><Caso /></ToastProvider>, { container: crearRaiz() });
    const disparador = screen.getByRole('button', { name: 'abrir' });
    disparador.focus();
    fireEvent.click(disparador);
    const aviso = screen.getByRole('button', { name: 'Cerrar aviso' });
    aviso.focus();
    fireEvent.keyDown(aviso, { key: 'Escape' });
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(document.activeElement).toBe(disparador);
    cajas.mockRestore();
  });

  it('DIS-049: un toque (pointerType touch) no pausa el aviso de éxito', () => {
    render(<ToastProvider><Disparador /></ToastProvider>);
    fireEvent.click(screen.getByRole('button', { name: 'ok' }));
    const tarjeta = screen.getByText('Guardado.').parentElement as HTMLElement;
    fireEvent.pointerEnter(tarjeta, { pointerType: 'touch' });
    act(() => { vi.advanceTimersByTime(TOAST_MS + 10); });
    expect(screen.queryByText('Guardado.')).toBeNull();
  });
});
