'use client';

/** Tarjeta de un usuario en la lista: datos, insignias de rol y acciones de fila. */

import type { ManagedUser } from '@/lib/types';
import { Button } from '../form';
import { Badge, Card } from '../ui';

const ROLE_LABELS: Record<string, string> = {
  administrador: 'Admin global',
  admin_area: 'Admin de área',
  usuario: 'Usuario',
};

export function UserCard({
  user,
  isAdmin,
  onEdit,
  onAccess,
  onRemove,
  onRole,
}: {
  user: ManagedUser;
  /** Superadmin: ve las acciones de rol (DIS-019). */
  isAdmin: boolean;
  onEdit: (user: ManagedUser) => void;
  onAccess: (trigger: HTMLButtonElement, user: ManagedUser) => void;
  onRemove: (user: ManagedUser) => void;
  onRole: (trigger: HTMLButtonElement, user: ManagedUser, action: 'areas' | 'quitar') => void;
}) {
  return (
    <Card>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate font-medium">{user.name}</p>
          <p className="truncate text-sm text-label">{user.email}</p>
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          <Badge>{ROLE_LABELS[user.role] ?? user.role}</Badge>
          <Badge tone={user.is_active ? 'success' : 'warning'}>
            {user.is_active ? 'Activo' : 'Inactivo'}
          </Badge>
          <Badge>{user.auth_source}</Badge>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-1.5">
        {user.areas.length === 0 ? (
          <span className="text-xs text-label">Sin áreas asignadas</span>
        ) : (
          user.areas.map((area) => (
            <span
              key={area.id}
              className="rounded-full bg-surface-container px-2 py-0.5 text-xs text-label"
            >
              {area.name}
            </span>
          ))
        )}
        {user.managed_areas.length > 0 ? (
          <Badge tone="success">
            administra {user.managed_areas.length}
          </Badge>
        ) : null}
      </div>

      {/* Acciones de 48 px (DIS-008; las de rol, DIS-019); bajan de línea si no caben. */}
      <div className="mt-3 flex flex-wrap gap-1 border-t border-panel-border pt-3">
        <Button
          variant="fila"
          onClick={() => onEdit(user)}
          aria-label={`Editar ${user.name}`}
        >
          Editar
        </Button>
        <Button
          variant="fila"
          onClick={(event) => onAccess(event.currentTarget, user)}
          aria-label={`Accesos de ${user.name}`}
        >
          Accesos
        </Button>
        <Button
          variant="fila-peligro"
          onClick={() => onRemove(user)}
          aria-label={`Eliminar ${user.name}`}
        >
          Eliminar
        </Button>
        {/* DIS-019: acciones de rol solo para el superadmin. */}
        {isAdmin && user.role === 'usuario' ? (
          <Button
            variant="fila"
            onClick={(event) => onRole(event.currentTarget, user, 'areas')}
            aria-label={`Hacer admin de área a ${user.name}`}
          >
            Hacer admin
          </Button>
        ) : null}
        {isAdmin && user.role === 'admin_area' ? (
          <>
            <Button
              variant="fila"
              onClick={(event) => onRole(event.currentTarget, user, 'areas')}
              aria-label={`Áreas admin de ${user.name}`}
            >
              Áreas admin
            </Button>
            <Button
              variant="fila"
              onClick={(event) => onRole(event.currentTarget, user, 'quitar')}
              aria-label={`Quitar admin de área a ${user.name}`}
            >
              Quitar admin
            </Button>
          </>
        ) : null}
      </div>
    </Card>
  );
}
