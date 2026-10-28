'use client';

/**
 * Áreas: consulta y administración. El superadmin gestiona todas y asigna sus
 * administradores; el admin de área da de alta áreas y gestiona las suyas
 * (DIS-016). Formulario y panel de administradores viven en `areas/`.
 */

import { useState } from 'react';
import { api } from '@/lib/api';
import { useAsync } from '@/lib/use-async';
import type { Area } from '@/lib/types';
import { variablesCss } from '@/lib/variables-css';
import { AreaAdminsPanel } from './areas/area-admins-panel';
import { mensajeDeError } from './areas/area-errors';
import { AreaForm } from './areas/area-form';
import { Button, ConfirmDialog } from './form';
import { RequireRole, meetsRequirement } from './require-role';
import { useSession } from './session-provider';
import { Badge, Card, EmptyNote, ErrorNote, Spinner } from './ui';

/** Sin rol de administración muestra el estado "sin permiso" y no llama a la API. */
export function AreasList() {
  return (
    <RequireRole requires="any_admin">
      <AreasScreen />
    </RequireRole>
  );
}

function AreasScreen() {
  const { session } = useSession();
  const { data, loading, error, reload } = useAsync(() => api.areas(), []);
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<Area | null>(null);
  const [removing, setRemoving] = useState<Area | null>(null);
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const [assigning, setAssigning] = useState<Area | null>(null);
  // `/me` se pide una vez: las áreas creadas en esta visita aún no están en
  // `session.managed_areas`, pero el admin de área ya las administra.
  const [created, setCreated] = useState<number[]>([]);

  const isAdmin = session?.permissions.is_admin ?? false;
  // `can_manage_areas` de `/me` sigue siendo solo del superadmin (FNC-045);
  // el alta se decide por rol: superadmin o admin de área.
  const canCreate = session ? meetsRequirement('any_admin', session.permissions) : false;
  const managedIds = new Set([
    ...(session?.managed_areas ?? []).map((a) => a.id),
    ...created,
  ]);

  async function remove() {
    if (!removing) return;
    setBusy(true);
    setProblem(null);
    try {
      await api.deleteArea(removing.id);
      setRemoving(null);
      reload();
    } catch (err) {
      setRemoving(null);
      setProblem(mensajeDeError(err, 'No se pudo eliminar'));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Áreas</h1>
          <p className="mt-1 text-sm text-label">
            {isAdmin ? 'Todas las áreas del sistema.' : 'Áreas que administras.'}
          </p>
        </div>
        {canCreate ? <Button onClick={() => setCreating(true)}>Nueva área</Button> : null}
      </div>

      {problem ? <ErrorNote message={problem} /> : null}
      {loading ? <Spinner /> : null}
      {error ? <ErrorNote message={error} /> : null}

      {!loading && !error ? (
        (data ?? []).length === 0 ? (
          <EmptyNote message="No hay áreas dentro de tu alcance." />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {(data ?? []).map((area) => {
              const canEdit = isAdmin || managedIds.has(area.id);
              return (
                <Card key={area.id}>
                  <div className="flex items-start justify-between gap-3">
                    <span
                      className="nx-chip-tint grid h-9 w-9 shrink-0 place-items-center rounded-lg text-xs font-semibold"
                      style={variablesCss({ '--chip-color': area.color })}
                      aria-hidden
                    >
                      {area.name.slice(0, 2).toUpperCase()}
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {area.status !== 'Activo' ? (
                        <Badge tone="warning">{area.status}</Badge>
                      ) : null}
                      {!isAdmin && managedIds.has(area.id) ? (
                        <Badge tone="success">Administras</Badge>
                      ) : null}
                    </div>
                  </div>

                  <p className="mt-3 truncate font-medium">{area.name}</p>
                  <p className="mt-0.5 line-clamp-2 text-sm text-label">
                    {area.description || 'Sin descripción.'}
                  </p>

                  <dl className="mt-4 flex gap-6 border-t border-panel-border pt-3 text-sm">
                    <div>
                      <dt className="text-xs text-label">Plataformas</dt>
                      <dd className="font-medium tabular-nums">{area.platforms_count}</dd>
                    </div>
                    <div>
                      <dt className="text-xs text-label">Usuarios</dt>
                      <dd className="font-medium tabular-nums">{area.users_count}</dd>
                    </div>
                  </dl>

                  {/* Acciones de 48 px (DIS-008); bajan de línea si no caben. */}
                  {canEdit ? (
                    <div className="mt-3 flex flex-wrap gap-1 border-t border-panel-border pt-3">
                      <Button
                        variant="fila"
                        onClick={() => setEditing(area)}
                        aria-label={`Editar ${area.name}`}
                      >
                        Editar
                      </Button>
                      {isAdmin ? (
                        <Button
                          variant="fila"
                          onClick={() => setAssigning(area)}
                          aria-label={`Administradores de ${area.name}`}
                        >
                          Administradores
                        </Button>
                      ) : null}
                      <Button
                        variant="fila-peligro"
                        onClick={() => setRemoving(area)}
                        aria-label={`Eliminar ${area.name}`}
                      >
                        Eliminar
                      </Button>
                    </div>
                  ) : null}
                </Card>
              );
            })}
          </div>
        )
      ) : null}

      {creating ? (
        <AreaForm
          area={null}
          onClose={() => setCreating(false)}
          onSaved={(area) => {
            setCreating(false);
            if (!isAdmin) setCreated((ids) => [...ids, area.id]);
            reload();
          }}
        />
      ) : null}

      {editing ? (
        <AreaForm
          area={editing}
          onClose={() => setEditing(null)}
          onSaved={() => { setEditing(null); reload(); }}
        />
      ) : null}

      {assigning ? (
        <AreaAdminsPanel area={assigning} onClose={() => setAssigning(null)} />
      ) : null}

      {removing ? (
        <ConfirmDialog
          title="Eliminar área"
          message={`Se eliminará "${removing.name}". Si tiene plataformas asignadas, primero hay que reasignarlas.`}
          onConfirm={remove}
          onCancel={() => setRemoving(null)}
          busy={busy}
        />
      ) : null}
    </div>
  );
}
