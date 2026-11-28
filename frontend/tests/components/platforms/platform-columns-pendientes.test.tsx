/**
 * DIS-161: columna «Solicitudes pendientes» en Gestión > área > plataformas, con enlace al
 * Historial filtrado por área y plataforma (`inbox/stats.pending_by_platform`, FNC-219).
 */
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { ReactNode } from 'react';
import { columnasPlataformas, rutaPendientesPlataforma } from '@/components/platforms/platform-columns';
import type { Platform } from '@/lib/types';

const WIKI = { id: 14, name: 'Wiki', area_id: 3, area_name: 'Finanzas', status: 'Activo', direct_link: '' } as unknown as Platform;
const CRM = { id: 15, name: 'CRM', area_id: 3, area_name: 'Finanzas', status: 'Activo', direct_link: '' } as unknown as Platform;

function columnas(pendientes?: Record<number, number>) {
  return columnasPlataformas({
    selectedPlatformIds: new Set(),
    allSelected: false,
    someSelected: false,
    toggleSelectAll: () => undefined,
    togglePlatform: () => undefined,
    pendientes,
  });
}

afterEach(cleanup);

describe('Columna Solicitudes pendientes (DIS-161)', () => {
  it('ruta al Historial con estado pendiente, área y plataforma', () => {
    expect(rutaPendientesPlataforma(WIKI)).toBe('/approvals?status=pendiente&area_id=3&platform_id=14');
  });

  it('con datos: enlace con la cifra (0 si no tiene) y nombre accesible con el texto visible', () => {
    const columna = columnas({ 14: 2 }).find((c) => c.key === 'pendientes');
    expect(columna?.header).toBe('Solicitudes pendientes');
    render(<>{columna?.cell?.(WIKI) as ReactNode}{columna?.cell?.(CRM) as ReactNode}</>);
    const wiki = screen.getByRole('link', { name: 'Solicitudes pendientes: 2, en Wiki. Abrir Historial.' });
    expect(wiki.textContent).toBe('2');
    expect(wiki.getAttribute('href')).toBe('/approvals?status=pendiente&area_id=3&platform_id=14');
    expect(wiki.className).toContain('min-h-12');
    expect(screen.getByRole('link', { name: /Solicitudes pendientes: 0, en CRM/ }).textContent).toBe('0');
  });

  it('el clic en el enlace no llega a la fila (no la selecciona)', () => {
    const columna = columnas({ 14: 2 }).find((c) => c.key === 'pendientes');
    const fila = vi.fn();
    render(<div onClick={fila}>{columna?.cell?.(WIKI) as ReactNode}</div>);
    fireEvent.click(screen.getByRole('link', { name: /Solicitudes pendientes: 2, en Wiki/ }));
    expect(fila).not.toHaveBeenCalled();
  });

  it('sin datos (consulta fallida o sin permiso) no hay columna', () => {
    expect(columnas(undefined).some((c) => c.key === 'pendientes')).toBe(false);
  });
});
