/**
 * Configuración del directorio en su forma de FNC-043 (`docs/contratos/
 * usuarios-directorio.md`). Solo lectura: la fuente son las variables `LDAP_*`.
 * La consume la pestaña Directorio de Ajustes (DIS-023), que retiró la forma
 * heredada de NEXUS (`api.authConfig` / `saveAuthConfig` / `testAuthConfig`).
 */

import { accessRequest } from './client';
import { MOCK_DIRECTORY_CONFIG } from './mocks';
import { jsonBody } from './query';
import type { DirectoryConfig } from './types';

export const directoryApi = {
  config: () =>
    accessRequest<DirectoryConfig>('/auth-config', undefined, () => MOCK_DIRECTORY_CONFIG),

  /** `PUT {}`: no edita nada; devuelve la configuración vigente. */
  reload: () =>
    accessRequest<{ status: 'success'; config: DirectoryConfig }>(
      '/auth-config', jsonBody('PUT'),
      () => ({ status: 'success', config: MOCK_DIRECTORY_CONFIG })),

  /** Sin cuerpo: `409 directorio_no_configurado` o `503 directorio_no_disponible`. */
  test: () =>
    accessRequest<{ status: 'success'; message: string }>(
      '/auth-config/test', jsonBody('POST'),
      () => ({ status: 'success', message: 'Conexión correcta.' })),
};
