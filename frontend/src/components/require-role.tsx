'use client';

/**
 * Guarda de ruta por rol (FNC-070).
 *
 * Solo decide qué se muestra: sin el permiso pinta el estado "sin permiso" y
 * no monta el contenido, así que las pantallas protegidas no llaman a la API.
 * La autorización real la hace el backend en cada endpoint.
 */

import type { Session } from '@/lib/types';
import { useSession } from './session-provider';
import { ErrorNote, Spinner } from './ui';

/**
 * Permiso que exige una ruta o una entrada del menú.
 * - `any_admin`: superadmin o admin de área.
 * - `admin`: solo superadmin.
 * - `requester`: quien solicita accesos (usuario y admin de área; el
 *   superadmin no solicita, tabla de pantallas por rol).
 */
export type RoleRequirement = 'any_admin' | 'admin' | 'requester';

/** Sin requisito, cualquier sesión cumple. */
export function meetsRequirement(
  requires: RoleRequirement | undefined,
  permissions: Session['permissions'],
): boolean {
  const { is_admin: isAdmin, is_area_admin: isAreaAdmin } = permissions;
  switch (requires) {
    case 'admin':
      return isAdmin;
    case 'any_admin':
      return isAdmin || isAreaAdmin;
    case 'requester':
      return !isAdmin;
    default:
      return true;
  }
}

export const FORBIDDEN_MESSAGE = 'No tienes permiso para ver esta sección.';

export function RequireRole({
  requires,
  children,
}: {
  requires: RoleRequirement;
  children: React.ReactNode;
}) {
  const { session, loading, error } = useSession();

  if (loading) return <Spinner label="Cargando sesión…" />;
  if (error) return <ErrorNote message={error} />;
  if (!session) return null;
  if (!meetsRequirement(requires, session.permissions)) {
    return <ErrorNote message={FORBIDDEN_MESSAGE} />;
  }
  return <>{children}</>;
}
