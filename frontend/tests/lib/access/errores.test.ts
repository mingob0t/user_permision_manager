/**
 * Manejo uniforme de errores del contrato (FNC-069): `ApiError` expone
 * `status`, `message`, `code`, `fields` y `correlationId` (README de contratos).
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError, apiRequest } from '@/lib/api';
import { grantsApi } from '@/lib/access/grants';
import { requestsApi } from '@/lib/access/requests';
import { usersApi } from '@/lib/access/users';
import { connectorsApi } from '@/lib/access/connectors';

const fetchSimulado = vi.fn<typeof fetch>();

function respuesta(status: number, cuerpo: unknown): Response {
  return new Response(JSON.stringify(cuerpo), {
    status, headers: { 'Content-Type': 'application/json' },
  });
}

async function error(promesa: Promise<unknown>): Promise<ApiError> {
  const capturado = await promesa.catch((e: unknown) => e);
  expect(capturado).toBeInstanceOf(ApiError);
  return capturado as ApiError;
}

beforeEach(() => {
  fetchSimulado.mockReset();
  vi.stubGlobal('fetch', fetchSimulado);
});

describe('errores del contrato', () => {
  it('401 sin_sesion: no autenticado, con su code', async () => {
    fetchSimulado.mockResolvedValue(respuesta(401,
      { status: 'error', message: 'Sesión no válida.', code: 'sin_sesion' }));

    const e = await error(grantsApi.mine());

    expect(e.isUnauthenticated).toBe(true);
    expect(e.code).toBe('sin_sesion');
  });

  it('403 rol insuficiente: isForbidden y code', async () => {
    fetchSimulado.mockResolvedValue(respuesta(403,
      { status: 'error', message: 'No tienes permiso.', code: 'sin_permiso' }));

    const e = await error(usersApi.setManagedAreas(5, [1]));

    expect(e.isForbidden).toBe(true);
    expect(e).toMatchObject({ status: 403, code: 'sin_permiso', message: 'No tienes permiso.' });
  });

  it('409 de conflicto: conserva code y message del contrato', async () => {
    fetchSimulado.mockResolvedValue(respuesta(409, {
      status: 'error', code: 'solicitud_duplicada',
      message: 'Ya tienes una solicitud pendiente para esta plataforma.',
    }));

    const e = await error(requestsApi.create(
      { platform_id: 12, level: 'usuario', justification: 'Necesito el acceso.' }));

    expect(e).toMatchObject({
      status: 409, code: 'solicitud_duplicada',
      message: 'Ya tienes una solicitud pendiente para esta plataforma.',
    });
    expect(e.fields).toEqual({});
  });

  it('422 validacion: fields por campo, anidados aplanados con punto', async () => {
    fetchSimulado.mockResolvedValue(respuesta(422, {
      status: 'error', message: 'Revisa los campos marcados.', code: 'validacion',
      fields: { host: 'Usa un nombre de host autorizado.', params: { base_path: 'Obligatorio.' } },
    }));

    const e = await error(connectorsApi.save(12, {
      type: 'api', host: 'x', port: 443, params: {}, credential_ref: 'ref',
    }));

    expect(e.code).toBe('validacion');
    expect(e.fields).toEqual({
      host: 'Usa un nombre de host autorizado.', 'params.base_path': 'Obligatorio.',
    });
  });

  it('500: correlation_id disponible para soporte', async () => {
    fetchSimulado.mockResolvedValue(respuesta(500, {
      status: 'error', message: 'Ocurrió un error. Intenta de nuevo.',
      code: 'error_interno', correlation_id: 'abc-123',
    }));

    const e = await error(apiRequest('/home/summary'));

    expect(e).toMatchObject({ status: 500, code: 'error_interno', correlationId: 'abc-123' });
  });

  it('error heredado sin code: code null y fields vacío', async () => {
    fetchSimulado.mockResolvedValue(respuesta(400, { message: 'El correo es obligatorio.' }));

    const e = await error(apiRequest('/users', { method: 'POST', body: '{}' }));

    expect(e).toMatchObject({ code: null, fields: {}, correlationId: null });
    expect(e.message).toBe('El correo es obligatorio.');
  });
});
