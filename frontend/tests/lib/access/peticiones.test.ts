/**
 * Forma de las peticiones del cliente del gestor de accesos (FNC-069):
 * ruta, método, cuerpo y consulta según `docs/contratos/`.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { auditApi } from '@/lib/access/audit';
import { connectorsApi } from '@/lib/access/connectors';
import { directoryApi } from '@/lib/access/directory';
import { grantsApi } from '@/lib/access/grants';
import { homeApi } from '@/lib/access/home';
import { inventoryApi } from '@/lib/access/inventory';
import { provisioningApi } from '@/lib/access/provisioning';
import { requestsApi } from '@/lib/access/requests';
import { usersApi } from '@/lib/access/users';

const fetchSimulado = vi.fn<typeof fetch>();

beforeEach(() => {
  fetchSimulado.mockReset();
  fetchSimulado.mockImplementation(async () => new Response('{}', { status: 200 }));
  vi.stubGlobal('fetch', fetchSimulado);
});

function ultima() {
  const [url, init] = fetchSimulado.mock.calls.at(-1)!;
  return {
    url,
    method: init?.method ?? 'GET',
    body: init?.body === undefined ? undefined : JSON.parse(String(init.body)),
    headers: init?.headers,
    credentials: init?.credentials,
  };
}

describe.each([
  ['catálogo con filtros', () => requestsApi.catalog({ area_id: 3, q: 'conta' }),
    '/api/v1/access-requests/catalog?area_id=3&q=conta', 'GET', undefined],
  ['crear solicitud', () => requestsApi.create(
    { platform_id: 12, level: 'admin', justification: 'Cierre mensual' }),
    '/api/v1/access-requests', 'POST',
    { platform_id: 12, level: 'admin', justification: 'Cierre mensual' }],
  ['crear solicitud sin justificación (contrato 1.1)', () => requestsApi.create(
    { platform_id: 12, level: 'usuario' }),
    '/api/v1/access-requests', 'POST', { platform_id: 12, level: 'usuario' }],
  ['mis solicitudes', () => requestsApi.mine({ status: 'pendiente', page: 2 }),
    '/api/v1/access-requests/mine?status=pendiente&page=2', 'GET', undefined],
  ['bandeja sin filtros', () => requestsApi.inbox(),
    '/api/v1/access-requests/inbox', 'GET', undefined],
  ['aprobar (cuerpo {})', () => requestsApi.approve(41),
    '/api/v1/access-requests/41/approve', 'POST', {}],
  ['rechazar con motivo', () => requestsApi.reject(41, 'Usa el reporte del área.'),
    '/api/v1/access-requests/41/reject', 'POST', { reason: 'Usa el reporte del área.' }],
  ['mis accesos', () => grantsApi.mine({ status: 'vigente' }),
    '/api/v1/me/access?status=vigente', 'GET', undefined],
  ['accesos de un usuario', () => grantsApi.ofUser(8),
    '/api/v1/users/8/access', 'GET', undefined],
  ['revocar sin motivo (P7)', () => grantsApi.revoke(77),
    '/api/v1/access/77/revoke', 'POST', {}],
  ['revocar con motivo', () => grantsApi.revoke(77, 'Baja'),
    '/api/v1/access/77/revoke', 'POST', { reason: 'Baja' }],
  ['inventario', () => inventoryApi.list({ level: 'admin', origin: 'solicitud', q: '' }),
    '/api/v1/access/inventory?level=admin&origin=solicitud', 'GET', undefined],
  ['auditoría siempre paginada', () => auditApi.list({ result: 'error' }),
    '/api/v1/audit?result=error&page=1', 'GET', undefined],
  ['auditoría de usuario', () => auditApi.ofUser(8, { page: 3, per_page: 50 }),
    '/api/v1/audit/users/8?page=3&per_page=50', 'GET', undefined],
  ['auditoría de plataforma', () => auditApi.ofPlatform(12),
    '/api/v1/audit/platforms/12?page=1', 'GET', undefined],
  ['leer conector', () => connectorsApi.get(12),
    '/api/v1/platforms/12/connector', 'GET', undefined],
  ['guardar conector', () => connectorsApi.save(12, {
    type: 'api', host: 'erp.ejemplo.local', port: 443, params: {}, credential_ref: 'p/c' }),
    '/api/v1/platforms/12/connector', 'PUT',
    { type: 'api', host: 'erp.ejemplo.local', port: 443, params: {}, credential_ref: 'p/c' }],
  ['borrar conector', () => connectorsApi.remove(12),
    '/api/v1/platforms/12/connector', 'DELETE', {}],
  ['probar conector', () => connectorsApi.test(12),
    '/api/v1/platforms/12/connector/test', 'POST', {}],
  ['ejecuciones', () => provisioningApi.jobs({ status: 'fallido', provider: 'ldap' }),
    '/api/v1/provisioning/jobs?status=fallido&provider=ldap', 'GET', undefined],
  ['detalle de ejecución', () => provisioningApi.job(301),
    '/api/v1/provisioning/jobs/301', 'GET', undefined],
  ['reintentar ejecución', () => provisioningApi.retry(301),
    '/api/v1/provisioning/jobs/301/retry', 'POST', {}],
  ['áreas administradas', () => usersApi.setManagedAreas(5, [3, 7]),
    '/api/v1/users/5/managed-areas', 'PUT', { area_ids: [3, 7] }],
  ['alta en el directorio', () => usersApi.createDirectoryAccount({
    uid: 'ana.ruiz', email: 'ana@ejemplo.local', given_name: 'Ana', surname: 'Ruiz', area_ids: [3] }),
    '/api/v1/users/directory', 'POST',
    { uid: 'ana.ruiz', email: 'ana@ejemplo.local', given_name: 'Ana', surname: 'Ruiz', area_ids: [3] }],
  ['configuración del directorio', () => directoryApi.config(),
    '/api/v1/auth-config', 'GET', undefined],
  ['recargar configuración (PUT {})', () => directoryApi.reload(),
    '/api/v1/auth-config', 'PUT', {}],
  ['probar directorio sin campos', () => directoryApi.test(),
    '/api/v1/auth-config/test', 'POST', {}],
  ['resumen de inicio', () => homeApi.summary(),
    '/api/v1/home/summary', 'GET', undefined],
] as const)('%s', (_nombre, llamar, url, metodo, cuerpo) => {
  it('pide la ruta del contrato con la sesión', async () => {
    await llamar();
    const peticion = ultima();

    expect(peticion.url).toBe(url);
    expect(peticion.method).toBe(metodo);
    expect(peticion.body).toEqual(cuerpo);
    expect(peticion.credentials).toBe('include');
    if (cuerpo !== undefined) {
      expect(peticion.headers).toMatchObject({ 'Content-Type': 'application/json' });
    }
  });
});

describe('plataformas v1 (api.createPlatform / updatePlatform de lib/api.ts)', () => {
  it('envía integration_type y DN, y devuelve warnings', async () => {
    const { api } = await import('@/lib/api');
    const warnings = [{ code: 'grupo_no_existe', message: 'El grupo no existe.' }];
    fetchSimulado.mockResolvedValueOnce(new Response(
      JSON.stringify({ status: 'success', platform: { id: 12 }, warnings }), { status: 201 }));

    const resultado = await api.createPlatform({
      name: 'Contabilidad', description: 'ERP', area_id: 3, integration_type: 'ldap',
      ldap_group_user_dn: 'cn=u,ou=p', ldap_group_admin_dn: 'cn=a,ou=p',
    });

    expect(ultima()).toMatchObject({ url: '/api/v1/platforms', method: 'POST' });
    expect(ultima().body).toMatchObject({ integration_type: 'ldap', ldap_group_admin_dn: 'cn=a,ou=p' });
    expect(resultado.warnings).toEqual(warnings);
  });

  it('PUT /platforms/<id> y 403 dn_solo_superadmin con su code', async () => {
    const { api, ApiError } = await import('@/lib/api');
    fetchSimulado.mockResolvedValueOnce(new Response(JSON.stringify({
      status: 'error', code: 'dn_solo_superadmin',
      message: 'Solo el superadmin define los grupos del directorio.',
    }), { status: 403 }));

    const e = await api.updatePlatform(12, { ldap_group_user_dn: 'cn=u,ou=p' })
      .catch((err: unknown) => err);

    expect(ultima()).toMatchObject({ url: '/api/v1/platforms/12', method: 'PUT' });
    expect(e).toBeInstanceOf(ApiError);
    expect(e).toMatchObject({ status: 403, code: 'dn_solo_superadmin' });
  });
});
