/**
 * Prueba de componente (FNC-025): `AuditLog` con la API simulada.
 * Se eligió por ser la pantalla con datos más simple (una sola llamada,
 * tabla, filtro y estados de carga, vacío y error).
 */
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { AuditEntry } from '@/lib/types';

vi.mock('@/lib/api', () => ({ api: { audit: vi.fn() } }));

import { api } from '@/lib/api';
import { AuditLog } from '@/components/audit-log';

const auditSimulado = vi.mocked(api.audit);

const REGISTROS: AuditEntry[] = [
  {
    id: 1, time: '2026-10-13 10:00', user: 'ana', action: 'Creó el área Ventas',
    module: 'areas', target: null, detail: null, ip: null, status: 'success',
  },
  {
    id: 2, time: '2026-10-13 11:00', user: 'luis', action: 'Borró una plataforma',
    module: 'plataformas', target: null, detail: null, ip: null, status: 'error',
  },
];

beforeEach(() => {
  auditSimulado.mockReset();
});

afterEach(() => {
  cleanup();
});

describe('AuditLog', () => {
  it('muestra la carga y luego los registros de la API', async () => {
    auditSimulado.mockResolvedValue(REGISTROS);
    render(<AuditLog />);

    expect(screen.getByRole('status')).toBeTruthy();
    expect(await screen.findByText('Creó el área Ventas')).toBeTruthy();
    expect(screen.getByText('Borró una plataforma')).toBeTruthy();
    expect(screen.getAllByRole('row')).toHaveLength(3); // cabecera + 2
    expect(auditSimulado).toHaveBeenCalledWith(200);
  });

  it('filtra por usuario, acción o módulo', async () => {
    auditSimulado.mockResolvedValue(REGISTROS);
    render(<AuditLog />);
    await screen.findByText('Creó el área Ventas');

    fireEvent.change(screen.getByLabelText('Filtrar registros'), { target: { value: 'luis' } });

    expect(screen.queryByText('Creó el área Ventas')).toBeNull();
    expect(screen.getByText('Borró una plataforma')).toBeTruthy();
  });

  it('muestra el estado vacío sin registros', async () => {
    auditSimulado.mockResolvedValue([]);
    render(<AuditLog />);

    expect(await screen.findByText('No hay registros dentro de tu alcance.')).toBeTruthy();
  });

  it('muestra el error de la API', async () => {
    auditSimulado.mockRejectedValue(new Error('Sin permiso'));
    render(<AuditLog />);

    expect((await screen.findByRole('alert')).textContent).toBe('Sin permiso');
  });
});
