'use client';

/**
 * Historial de un usuario (`/audit/users/[id]`; DIS-020, F-AUD-04;
 * `GET /audit/users/<id>`): eventos donde actuó o lo afectaron.
 *
 * - Admin y superadmin: cualquiera de su alcance (el backend responde 404 fuera de él).
 * - Usuario: solo el suyo; otro id muestra "sin permiso" sin pedir nada.
 */

import { ButtonLink } from '../form';
import { useCallback, useState } from 'react';
import { auditApi } from '@/lib/access/audit';
import type { AuditEntryV1, AuditParams } from '@/lib/access/types';
import { FORBIDDEN_MESSAGE } from '../require-role';
import { useSession } from '../session-provider';
import { ErrorNote, Spinner } from '../ui';
import { AuditHistory } from './audit-history';
import { RUTA_AUDITORIA } from './audit-routes';

/** Correo del usuario según los registros (actor o usuario afectado). */
export function correoDelUsuario(items: AuditEntryV1[], userId: number): string | null {
  for (const entry of items) {
    if (entry.target_user?.id === userId) return entry.target_user.email;
    if (entry.actor?.id === userId) return entry.actor.email;
  }
  return null;
}

export function UserAuditHistory({ userId }: { userId: number }) {
  const { session, loading, error } = useSession();
  const [correo, setCorreo] = useState<string | null>(null);

  const cargar = useCallback(
    (params: AuditParams) => auditApi.ofUser(userId, params), [userId]);
  const nombrar = useCallback((items: AuditEntryV1[]) => {
    setCorreo((actual) => actual ?? correoDelUsuario(items, userId));
  }, [userId]);

  if (loading) return <Spinner label="Cargando sesión…" />;
  if (error) return <ErrorNote message={error} />;
  if (!session) return null;

  const administra = session.permissions.is_admin || session.permissions.is_area_admin;
  if (!administra && session.id !== userId) return <ErrorNote message={FORBIDDEN_MESSAGE} />;

  const propio = session.id === userId;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-2xl font-semibold">
            {propio ? 'Mi historial' : 'Historial del usuario'}
          </h1>
          <p className="mt-1 break-words text-sm text-label">
            {(propio ? session.email : correo) ?? 'Eventos donde actuó o que lo afectaron.'}
          </p>
        </div>
        <ButtonLink href={RUTA_AUDITORIA} variant="secondary">
          Toda la auditoría
        </ButtonLink>
      </div>
      <AuditHistory cargar={cargar} onDatos={nombrar} />
    </div>
  );
}
