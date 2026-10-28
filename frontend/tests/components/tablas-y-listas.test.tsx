import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import React from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ListPager } from '@/components/access/list-pager';
import {
  DataColumn,
  DataLabel,
  DataList,
  DataListItem,
  DataTable,
  ResponsiveList,
  ResponsiveRow,
} from '@/components/data-table';

afterEach(() => {
  cleanup();
});

interface ItemPrueba {
  id: string;
  nombre: string;
  categoria: string;
  activo: boolean;
}

const ITEMS: ItemPrueba[] = [
  { id: '1', nombre: 'Elemento Alfa', categoria: 'Cat A', activo: true },
  { id: '2', nombre: 'Elemento Beta', categoria: 'Cat B', activo: false },
];

const COLUMNAS: DataColumn<ItemPrueba>[] = [
  { key: 'nombre', header: 'Nombre', cell: (r) => r.nombre },
  { key: 'categoria', header: 'Categoría', cell: (r) => r.categoria },
];

describe('DIS-071: Tablas y listas unificadas', () => {
  describe('DataTable', () => {
    it('renderiza tabla con encabezados y filas accesibles', () => {
      render(
        <DataTable
          label="Tabla de prueba"
          columns={COLUMNAS}
          rows={ITEMS}
          rowKey={(r) => r.id}
          emptyMessage="Sin elementos"
        />,
      );

      expect(screen.getByRole('region', { name: 'Tabla de prueba' })).toBeDefined();
      expect(screen.getByRole('columnheader', { name: 'Nombre' })).toBeDefined();
      expect(screen.getByRole('columnheader', { name: 'Categoría' })).toBeDefined();
      expect(screen.getByText('Elemento Alfa')).toBeDefined();
      expect(screen.getByText('Elemento Beta')).toBeDefined();
    });

    it('renderiza tabla alternativa sr-only para gráficos accesibles', () => {
      render(
        <DataTable
          srOnly
          label="Datos alternativos de gráfica"
          columns={COLUMNAS}
          rows={ITEMS}
          rowKey={(r) => r.id}
          emptyMessage="Sin datos"
        />,
      );

      const tabla = screen.getByRole('table');
      expect(tabla.className).toContain('sr-only');
      expect(screen.getByText('Datos alternativos de gráfica')).toBeDefined();
      expect(screen.getByRole('rowheader', { name: 'Elemento Alfa' })).toBeDefined();
    });

    it('soporta filas seleccionables e interactivas con aria-selected', () => {
      const onRowClick = vi.fn();
      render(
        <DataTable
          label="Tabla interactiva"
          columns={COLUMNAS}
          rows={ITEMS}
          rowKey={(r) => r.id}
          emptyMessage="Sin elementos"
          selectedKey="1"
          onRowClick={onRowClick}
        />,
      );

      const filas = screen.getAllByRole('row');
      // filas[0] es thead; filas[1] es Alfa (seleccionada)
      expect(filas[1].getAttribute('aria-selected')).toBe('true');
      expect(filas[1].className).toContain('bg-primary/10');

      fireEvent.click(filas[2]);
      expect(onRowClick).toHaveBeenCalledWith(ITEMS[1]);
    });
  });

  describe('ResponsiveList & ResponsiveRow', () => {
    it('renderiza lista adaptable con encabezados de escritorio y filas semánticas', () => {
      render(
        <ResponsiveList
          columns="md:grid-cols-[1fr_10rem]"
          headers={['Elemento', 'Categoría']}
          label="Lista responsiva"
        >
          {ITEMS.map((item) => (
            <ResponsiveRow
              key={item.id}
              columns="md:grid-cols-[1fr_10rem]"
              label={`Fila ${item.id}`}
            >
              <div>
                <dt className="text-xs text-label md:sr-only">Elemento</dt>
                <dd>{item.nombre}</dd>
              </div>
              <div>
                <dt className="text-xs text-label md:sr-only">Categoría</dt>
                <dd>{item.categoria}</dd>
              </div>
            </ResponsiveRow>
          ))}
        </ResponsiveList>,
      );

      expect(screen.getByRole('list', { name: 'Lista responsiva' })).toBeDefined();
      expect(screen.getAllByRole('listitem')).toHaveLength(2);
      expect(screen.getByText('Elemento Alfa')).toBeDefined();
    });

    it('aplica clases de estado seleccionado y error a ResponsiveRow', () => {
      render(
        <ResponsiveList
          columns="md:grid-cols-2"
          headers={['A', 'B']}
          label="Estados de lista"
        >
          <ResponsiveRow
            columns="md:grid-cols-2"
            label="Fila seleccionada"
            selected={true}
          >
            <div>
              <dt>A</dt>
              <dd>Sel</dd>
            </div>
          </ResponsiveRow>
          <ResponsiveRow
            columns="md:grid-cols-2"
            label="Fila error"
            error={true}
          >
            <div>
              <dt>A</dt>
              <dd>Err</dd>
            </div>
          </ResponsiveRow>
        </ResponsiveList>,
      );

      const items = screen.getAllByRole('listitem');
      expect(items[0].getAttribute('data-selected')).toBe('true');
      expect(items[0].className).toContain('border-l-primary');
      expect(items[1].className).toContain('border-l-error');
    });
  });

  describe('DataLabel', () => {
    it('renderiza término y descripción semántica con diseño de tokens', () => {
      render(<DataLabel label="Estado operativo">Activo</DataLabel>);
      expect(screen.getByText('Estado operativo')).toBeDefined();
      expect(screen.getByText('Activo')).toBeDefined();
    });
  });

  describe('DataList & DataListItem', () => {
    it('renderiza lista estructurada de detalles', () => {
      render(
        <DataList aria-label="Historial de cambios">
          <DataListItem selected>Cambio 1</DataListItem>
          <DataListItem error>Cambio 2 con error</DataListItem>
        </DataList>,
      );

      expect(screen.getByRole('list', { name: 'Historial de cambios' })).toBeDefined();
      const items = screen.getAllByRole('listitem');
      expect(items[0].className).toContain('border-l-primary');
      expect(items[1].className).toContain('border-l-error');
    });
  });

  describe('ListPager', () => {
    it('renderiza paginador con botones de control alto accesible (min-h-12)', () => {
      const onChange = vi.fn();
      render(
        <ListPager
          page={2}
          perPage={10}
          total={30}
          label="Paginación de solicitudes"
          onChange={onChange}
        />,
      );

      const anterior = screen.getByRole('button', { name: 'Anterior' });
      const siguiente = screen.getByRole('button', { name: 'Siguiente' });

      expect(anterior.className).toContain('min-h-12');
      expect(siguiente.className).toContain('min-h-12');

      fireEvent.click(siguiente);
      expect(onChange).toHaveBeenCalledWith(3);
    });
  });
});
