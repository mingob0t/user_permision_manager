/**
 * DIS-031: los diálogos de confirmación ligan su texto explicativo con `describedBy`
 * (`aria-describedby` del `role="dialog"`). DIS-043: los destructivos confirman con el
 * botón de peligro (`danger`); los que no lo son, con el primario.
 */
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import type { Platform } from '@/lib/types';
import { MOCK_ACCESS, MOCK_JOB, MOCK_REQUEST, MOCK_USER } from '@/lib/access/mocks';
import { ApproveDialog } from '@/components/access/approve-dialog';
import { RejectDialog } from '@/components/access/reject-dialog';
import { RevokeAccessDialog } from '@/components/users/revoke-access-dialog';
import { AdminAreasDialog, RemoveAdminDialog } from '@/components/users/admin-role-dialog';
import { ConnectorDeleteDialog } from '@/components/connectors/connector-delete-dialog';
import { JobRetryDialog } from '@/components/connectors/job-retry-dialog';

afterEach(cleanup);

const nada = () => undefined;
const PLATAFORMA = { id: 4, name: 'Jira' } as Platform;
const ADMIN = { ...MOCK_USER, role: 'admin_area' as const, managed_areas: [{ id: 3, name: 'Finanzas' }] };

/** Texto que lee el lector de pantalla como descripción del diálogo. */
function descripcion(): string {
  const ids = screen.getByRole('dialog').getAttribute('aria-describedby') ?? '';
  expect(ids).not.toBe('');
  return ids
    .split(' ')
    .map((id) => {
      const el = document.getElementById(id);
      expect(el, `falta el elemento #${id}`).not.toBeNull();
      return el!.textContent ?? '';
    })
    .join(' ');
}

function confirmar(nombre: RegExp) {
  return screen.getByRole('button', { name: nombre });
}

const PELIGRO = 'bg-error-solid';

describe('describedBy y botón de confirmar', () => {
  it('Aprobar: describe el efecto y el área; botón primario', () => {
    render(<ApproveDialog request={MOCK_REQUEST} onClose={nada} onDecided={nada} onStale={nada} />);
    expect(descripcion()).toContain(MOCK_REQUEST.platform.name);
    expect(descripcion()).toContain(`Área ${MOCK_REQUEST.area.name}`);
    expect(confirmar(/^Aprobar$/).className).not.toContain(PELIGRO);
  });

  it('Rechazar: describe la solicitud; botón de peligro', () => {
    render(<RejectDialog request={MOCK_REQUEST} onClose={nada} onDecided={nada} onStale={nada} />);
    expect(descripcion()).toContain(MOCK_REQUEST.requester.name);
    expect(confirmar(/^Rechazar$/).className).toContain(PELIGRO);
  });

  it('Revocar: describe el efecto y que no se deshace; botón de peligro', () => {
    render(<RevokeAccessDialog access={MOCK_ACCESS} onClose={nada} onRevoked={nada} onStale={nada} />);
    expect(descripcion()).toContain(MOCK_ACCESS.platform.name);
    expect(descripcion()).toContain('no se puede deshacer');
    expect(confirmar(/^Revocar$/).className).toContain(PELIGRO);
  });

  it('Hacer admin: describe el efecto de las áreas; botón primario', () => {
    render(
      <AdminAreasDialog
        user={ADMIN}
        areas={[{ id: 3, name: 'Finanzas' }]}
        onClose={nada}
        onSaved={nada}
        onStale={nada}
      />,
    );
    expect(descripcion()).toContain('Sin cambios en sus áreas.');
    expect(confirmar(/^Guardar áreas$/).className).not.toContain(PELIGRO);
  });

  it('Quitar admin: describe el efecto y los accesos automáticos; botón de peligro', () => {
    render(<RemoveAdminDialog user={ADMIN} onClose={nada} onSaved={nada} onStale={nada} />);
    expect(descripcion()).toContain('dejará de administrar: Finanzas');
    expect(descripcion()).toContain('accesos automáticos');
    expect(confirmar(/^Quitar admin$/).className).toContain(PELIGRO);
  });

  it('Eliminar conector: describe el efecto; botón de peligro', () => {
    render(<ConnectorDeleteDialog platform={PLATAFORMA} onClose={nada} onDeleted={nada} onStale={nada} />);
    expect(descripcion()).toContain('conector de Jira');
    expect(descripcion()).toContain('accesos vigentes');
    expect(confirmar(/^Eliminar$/).className).toContain(PELIGRO);
  });

  it('Reintentar ejecución: describe el efecto; botón primario', () => {
    render(<JobRetryDialog job={MOCK_JOB} onClose={nada} onRetried={nada} onStale={nada} />);
    expect(descripcion()).toContain(MOCK_JOB.platform.name);
    expect(descripcion()).toContain(`n.º ${MOCK_JOB.id}`);
    expect(confirmar(/^Reintentar$/).className).not.toContain(PELIGRO);
  });
});
