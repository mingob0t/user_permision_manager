import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import React, { createRef } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  PageHeader,
  PantallaDetalle,
  PantallaFormulario,
  PantallaListado,
  PantallaPanel,
} from '@/components/plantillas';

afterEach(() => {
  cleanup();
});

describe('DIS-070: PageHeader y Plantillas canónicas de pantalla', () => {
  describe('PageHeader', () => {
    it('renderiza título dentro de h1 con tabIndex -1 y descripción', () => {
      const h1Ref = createRef<HTMLHeadingElement>();
      render(
        <PageHeader
          title="Plataformas"
          description="Gestión del catálogo"
          h1Ref={h1Ref}
        />,
      );

      const h1 = screen.getByRole('heading', { level: 1, name: 'Plataformas' });
      expect(h1).toBeDefined();
      expect(h1.getAttribute('tabindex')).toBe('-1');
      expect(h1Ref.current).toBe(h1);
      expect(screen.getByText('Gestión del catálogo')).toBeDefined();
    });

    it('renderiza botón volver y acciones cuando se especifican', () => {
      render(
        <PageHeader
          title="Detalle"
          backHref="/admin"
          backLabel="Administración"
          actions={<button type="button">Crear</button>}
        />,
      );

      const volver = screen.getByRole('link', { name: /Administración/ });
      expect(volver.getAttribute('href')).toBe('/admin');
      expect(screen.getByRole('button', { name: 'Crear' })).toBeDefined();
    });
  });

  describe('PantallaListado', () => {
    it('muestra esqueleto de carga cuando loading=true', () => {
      render(
        <PantallaListado
          headerProps={{ title: 'Listado' }}
          loading={true}
          skeletonCount={3}
        >
          <div>Contenido de lista</div>
        </PantallaListado>,
      );

      expect(screen.getAllByRole('status', { name: 'Cargando listado…' }).length).toBe(3);
      expect(screen.queryByText('Contenido de lista')).toBeNull();
    });

    it('muestra error cuando error está presente', () => {
      render(
        <PantallaListado
          headerProps={{ title: 'Listado' }}
          error="Error al cargar datos"
        >
          <div>Contenido</div>
        </PantallaListado>,
      );

      expect(screen.getByText('Error al cargar datos')).toBeDefined();
    });

    it('muestra estado vacío cuando empty=true', () => {
      render(
        <PantallaListado
          headerProps={{ title: 'Listado' }}
          empty={true}
          emptyMessage="Sin elementos disponibles"
          emptyAction={<button type="button">Nuevo elemento</button>}
        >
          <div>Contenido</div>
        </PantallaListado>,
      );

      expect(screen.getByText('Sin elementos disponibles')).toBeDefined();
      expect(screen.getByRole('button', { name: 'Nuevo elemento' })).toBeDefined();
      expect(screen.queryByText('Contenido')).toBeNull();
    });

    it('muestra contenido y paginador cuando no está en carga ni vacío', () => {
      render(
        <PantallaListado
          headerProps={{ title: 'Listado' }}
          pager={<nav aria-label="Paginador">Página 1</nav>}
        >
          <div>Filas de la tabla</div>
        </PantallaListado>,
      );

      expect(screen.getByText('Filas de la tabla')).toBeDefined();
      expect(screen.getByText('Página 1')).toBeDefined();
    });
  });

  describe('PantallaDetalle', () => {
    it('renderiza resumen y secciones cuando no está cargando', () => {
      render(
        <PantallaDetalle
          headerProps={{ title: 'Detalle de elemento' }}
          summary={<div>Tarjeta resumen</div>}
        >
          <div>Sección adicional</div>
        </PantallaDetalle>,
      );

      expect(screen.getByText('Detalle de elemento')).toBeDefined();
      expect(screen.getByText('Tarjeta resumen')).toBeDefined();
      expect(screen.getByText('Sección adicional')).toBeDefined();
    });

    it('muestra esqueleto cuando loading=true', () => {
      render(
        <PantallaDetalle
          headerProps={{ title: 'Detalle' }}
          loading={true}
        >
          <div>Contenido</div>
        </PantallaDetalle>,
      );

      expect(screen.getByRole('status', { name: 'Cargando resumen…' })).toBeDefined();
      expect(screen.queryByText('Contenido')).toBeNull();
    });
  });

  describe('PantallaFormulario', () => {
    it('renderiza formulario y ejecuta onSubmit', () => {
      const onSubmit = vi.fn((e: React.FormEvent) => e.preventDefault());
      render(
        <PantallaFormulario
          headerProps={{ title: 'Nuevo usuario' }}
          onSubmit={onSubmit}
          actions={<button type="submit">Guardar</button>}
        >
          <input placeholder="Nombre" readOnly />
        </PantallaFormulario>,
      );

      expect(screen.getByPlaceholderText('Nombre')).toBeDefined();
      fireEvent.click(screen.getByRole('button', { name: 'Guardar' }));
      expect(onSubmit).toHaveBeenCalledTimes(1);
    });
  });

  describe('PantallaPanel', () => {
    it('renderiza métricas y bloques de panel', () => {
      render(
        <PantallaPanel
          headerProps={{ title: 'Panel Principal' }}
          stats={<div>Métricas KPI</div>}
        >
          <div>Bloque de actividad</div>
        </PantallaPanel>,
      );

      expect(screen.getByText('Panel Principal')).toBeDefined();
      expect(screen.getByText('Métricas KPI')).toBeDefined();
      expect(screen.getByText('Bloque de actividad')).toBeDefined();
    });
  });
});
