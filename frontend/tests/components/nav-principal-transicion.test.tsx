import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { NavPrincipal } from '@/components/marco/nav-principal';
import {
  CLAVE_OMITIR_MODAL_PORTAL,
  guardarOmitirModalPortal,
} from '@/components/marco/modal-transicion-portal';

const rutaMock = vi.hoisted(() => ({ actual: '/', push: vi.fn() }));
vi.mock('next/navigation', () => ({
  usePathname: () => rutaMock.actual,
  useRouter: () => ({ push: rutaMock.push }),
}));

vi.mock('@/components/session-provider', () => ({
  useSession: () => ({
    session: {
      id: 1,
      email: 'admin@test.local',
      role: 'administrador',
      permissions: {
        is_admin: true,
        is_area_admin: false,
        can_manage_areas: true,
        can_manage_system: true,
      },
    },
  }),
}));

describe('NavPrincipal transición hacia Portal', () => {
  beforeEach(() => {
    window.localStorage.clear();
    rutaMock.actual = '/';
    rutaMock.push.mockReset();
  });

  afterEach(() => {
    cleanup();
  });

  it('al pulsar Portal desde admin cuando no está omitido, abre el modal preventivo en lugar de redirigir de inmediato', () => {
    render(<NavPrincipal />);

    const linkPortal = screen.getByRole('link', { name: 'Portal' });
    fireEvent.click(linkPortal);

    // Debe abrir el diálogo modal y no llamar directamente a router.push
    expect(screen.getByRole('dialog')).toBeTruthy();
    expect(screen.getByText('Ir al Portal de Usuario')).toBeTruthy();
    expect(rutaMock.push).not.toHaveBeenCalled();
  });

  it('al pulsar Ir al portal en el modal, redirige a /platforms con router.push', () => {
    render(<NavPrincipal />);

    fireEvent.click(screen.getByRole('link', { name: 'Portal' }));
    expect(screen.getByRole('dialog')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Ir al portal' }));
    expect(rutaMock.push).toHaveBeenCalledWith('/platforms');
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('al marcar el checkbox y continuar, guarda la preferencia para omitir en localStorage', () => {
    render(<NavPrincipal />);

    fireEvent.click(screen.getByRole('link', { name: 'Portal' }));
    const checkbox = screen.getByLabelText('No volver a mostrar este aviso');
    fireEvent.click(checkbox);

    fireEvent.click(screen.getByRole('button', { name: 'Ir al portal' }));
    expect(window.localStorage.getItem(CLAVE_OMITIR_MODAL_PORTAL)).toBe('true');
  });

  it('si la preferencia está omitida, al hacer clic en Portal no abre el modal', () => {
    guardarOmitirModalPortal(true);
    render(<NavPrincipal />);

    const linkPortal = screen.getByRole('link', { name: 'Portal' });
    fireEvent.click(linkPortal);

    // No debe haber modal en pantalla
    expect(screen.queryByRole('dialog')).toBeNull();
  });
});


describe('NavPrincipal: ítem activo en subrutas (DIS-163)', () => {
  afterEach(() => {
    cleanup();
    rutaMock.actual = '/';
  });

  it('en `/approvals/historial` queda activo «Solicitudes» y solo él', () => {
    rutaMock.actual = '/approvals/historial';
    render(<NavPrincipal />);
    const activos = document.querySelectorAll('[aria-current="page"]');
    expect(activos).toHaveLength(1);
    expect(activos[0].getAttribute('href')).toBe('/approvals');
  });

  it('en `/approvals` sigue activo «Solicitudes»', () => {
    rutaMock.actual = '/approvals';
    render(<NavPrincipal />);
    expect(document.querySelector('[aria-current="page"]')?.getAttribute('href')).toBe('/approvals');
  });
});
