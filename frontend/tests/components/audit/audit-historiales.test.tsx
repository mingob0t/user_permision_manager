/**
 * DIS-020: historial por usuario (`/audit/users/[id]`) y por plataforma
 * (`/audit/platforms/[id]`), rutas y antes/después.
 * - Cada historial usa su endpoint paginado y nombra al sujeto con los registros.
 * - Usuario: solo el suyo; otro id, "sin permiso" sin pedir nada.
 * - 404 del backend (fuera del alcance) en español.
 * - Historial de plataforma: sin filtros de área ni plataforma.
 */
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { AuditEntryV1, Paginated } from '@/lib/access/types';

vi.mock('@/lib/access/audit', () => ({
  auditApi: { list: vi.fn(), ofUser: vi.fn(), ofPlatform: vi.fn() },
}));
vi.mock('@/lib/api', async (original) => ({
  ...(await original<typeof import('@/lib/api')>()),
  api: { areas: vi.fn(), platforms: vi.fn() },
}));

let administra = true;
vi.mock('@/components/session-provider', () => ({
  useSession: () => ({
    loading: false,
    error: null,
    session: {
      id: 2,
      email: 'luis@ejemplo.local',
      role: administra ? 'admin_area' : 'usuario',
      managed_areas: administra ? [{ id: 3, name: 'Finanzas' }] : [],
      preferences: { refresh_interval: 60 },
      permissions: {
        is_admin: false, is_area_admin: administra, can_manage_areas: false, can_manage_system: false,
      },
    },
  }),
}));

import { ApiError, api } from '@/lib/api';
import { auditApi } from '@/lib/access/audit';
import { MOCK_AUDIT } from '@/lib/access/mocks';
import { FORBIDDEN_MESSAGE } from '@/components/require-role';
import { MENSAJE_NO_ENCONTRADO } from '@/components/audit/audit-history';
import { compararCampos, valorLegible } from '@/components/audit/audit-diff';
import { idDeRuta, rutaHistorialPlataforma, rutaHistorialUsuario } from '@/components/audit/audit-routes';
import { UserAuditHistory } from '@/components/audit/user-audit-history';
import { PlatformAuditHistory } from '@/components/audit/platform-audit-history';

function pagina<T>(items: T[]): Paginated<T> {
  return { items, page: 1, per_page: 25, total: items.length };
}

const ANA: AuditEntryV1 = {
  ...MOCK_AUDIT, id: 1, action: 'acceso_otorgado',
  target_user: { id: 8, email: 'ana@ejemplo.local' },
};

beforeEach(() => {
  vi.clearAllMocks();
  administra = true;
  vi.mocked(auditApi.ofUser).mockResolvedValue(pagina([ANA]));
  vi.mocked(auditApi.ofPlatform).mockResolvedValue(pagina([ANA]));
  vi.mocked(api.platforms).mockResolvedValue([]);
});

afterEach(cleanup);

describe('Historial de usuario', () => {
  it('admin: pide `GET /audit/users/<id>` paginado y nombra al usuario', async () => {
    render(<UserAuditHistory userId={8} />);
    expect(await screen.findByText('ana@ejemplo.local')).toBeTruthy();
    expect(screen.getByRole('heading', { name: 'Historial del usuario' })).toBeTruthy();
    expect(auditApi.ofUser).toHaveBeenCalledWith(8, { page: 1 });
    expect(auditApi.list).not.toHaveBeenCalled();
    expect(screen.getByRole('link', { name: 'Toda la auditoría' }).getAttribute('href')).toBe('/audit');
    expect(screen.getByLabelText('Área')).toBeTruthy();
  });

  it('usuario: el suyo sí ("Mi historial"); otro id, sin permiso y sin pedir nada', async () => {
    administra = false;
    render(<UserAuditHistory userId={2} />);
    expect(screen.getByRole('heading', { name: 'Mi historial' })).toBeTruthy();
    await waitFor(() => expect(auditApi.ofUser).toHaveBeenCalledWith(2, { page: 1 }));
    expect(screen.queryByLabelText('Área')).toBeNull();
    cleanup();
    vi.mocked(auditApi.ofUser).mockClear();
    render(<UserAuditHistory userId={8} />);
    expect(screen.getByRole('alert').textContent).toBe(FORBIDDEN_MESSAGE);
    expect(auditApi.ofUser).not.toHaveBeenCalled();
  });

  it('404 del backend: fuera del alcance, en español', async () => {
    vi.mocked(auditApi.ofUser).mockRejectedValue(new ApiError(404, 'Not Found'));
    render(<UserAuditHistory userId={99} />);
    expect((await screen.findByRole('alert')).textContent).toBe(MENSAJE_NO_ENCONTRADO);
  });
});

describe('Historial de plataforma', () => {
  it('pide `GET /audit/platforms/<id>`, la nombra y no ofrece área ni plataforma', async () => {
    render(<PlatformAuditHistory platformId={12} />);
    expect(await screen.findByText('Contabilidad', { selector: 'p' })).toBeTruthy();
    expect(auditApi.ofPlatform).toHaveBeenCalledWith(12, { page: 1 });
    expect(screen.queryByLabelText('Área')).toBeNull();
    expect(screen.queryByLabelText('Plataforma')).toBeNull();
    expect(screen.getByLabelText('Evento')).toBeTruthy();
    expect(api.platforms).not.toHaveBeenCalled();
  });
});

describe('Rutas y antes/después', () => {
  it('rutas e ids de ruta válidos', () => {
    expect(rutaHistorialUsuario(8)).toBe('/audit/users/8');
    expect(rutaHistorialPlataforma(12)).toBe('/audit/platforms/12');
    expect(idDeRuta('12')).toBe(12);
    for (const malo of ['0', '-1', '1e3', 'abc', '012', '1234567890', '']) {
      expect(idDeRuta(malo)).toBeNull();
    }
  });

  it('compararCampos: unión ordenada, ausentes como "—" y marca de cambio', () => {
    expect(compararCampos({ role: 'usuario', x: 1 }, { role: 'admin_area', y: null })).toEqual([
      { campo: 'role', antes: 'usuario', despues: 'admin_area', cambio: true },
      { campo: 'x', antes: '1', despues: '—', cambio: true },
      { campo: 'y', antes: '—', despues: '—', cambio: false },
    ]);
    expect(compararCampos(null, null)).toEqual([]);
  });

  it('valorLegible: booleanos, objetos como JSON y HTML como texto', () => {
    expect(valorLegible(true)).toBe('Sí');
    expect(valorLegible({ a: 1 })).toBe('{"a":1}');
    expect(valorLegible('<b>x</b>')).toBe('<b>x</b>');
  });
});
