'use client';

/** Usuarios: alta, edición, baja y asignación de áreas y plataformas. */

import { useCallback, useRef, useState } from 'react';
import { api } from '@/lib/api';
import { useAsync } from '@/lib/use-async';
import type { DirectoryUser, ManagedUser } from '@/lib/types';
import { Button, ConfirmDialog } from './form';
import { useSession } from './session-provider';
import { Card, EmptyNote, ErrorNote, Spinner, SuccessNote } from './ui';
import { AdminAreasDialog, RemoveAdminDialog } from './users/admin-role-dialog';
import { DirectoryAccountForm } from './users/directory-account-form';
import { DirectoryPicker } from './users/directory-picker';
import { PurgePanel } from './users/purge-panel';
import { UserAccessPanel } from './users/user-access-panel';
import { UserCard } from './users/user-card';
import { UserForm } from './users/user-form';

export function UsersList() {
  const { session } = useSession();
  const users = useAsync(() => api.users(), []);
  const areas = useAsync(() => api.areas(), []);
  const platforms = useAsync(() => api.platforms(), []);
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<ManagedUser | null>(null);
  const [removing, setRemoving] = useState<ManagedUser | null>(null);
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const [directory, setDirectory] = useState(false);
  const [showPurge, setShowPurge] = useState(false);
  const [prefill, setPrefill] = useState<DirectoryUser | null>(null);
  // DIS-018: accesos del usuario; al cerrar, el foco vuelve a su botón.
  const [accessOf, setAccessOf] = useState<ManagedUser | null>(null);
  const accessTrigger = useRef<HTMLButtonElement | null>(null);
  // DIS-019: alta en el directorio y acciones de rol (solo superadmin); el
  // resultado se anuncia en una región `status` que recibe el foco.
  const [creatingAccount, setCreatingAccount] = useState(false);
  const [roleOf, setRoleOf] = useState<{ user: ManagedUser; action: 'areas' | 'quitar' } | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const avisoRef = useRef<HTMLDivElement>(null);

  const isAdmin = session?.permissions.is_admin ?? false;
  // El superadmin asigna cualquier área; el admin de área, solo las suyas.
  const assignableAreas = isAdmin ? (areas.data ?? []) : (session?.managed_areas ?? []);

  const roleTrigger = useRef<HTMLButtonElement | null>(null);

  function abrirRol(trigger: HTMLButtonElement, user: ManagedUser, action: 'areas' | 'quitar') {
    roleTrigger.current = trigger;
    setRoleOf({ user, action });
  }

  // Estables (`useCallback`): `Modal` re-ejecuta su efecto, y enfoca su panel,
  // cada vez que cambia `onClose`; con una función nueva por render robaría el foco.
  const cancelarRol = useCallback(() => {
    setRoleOf(null);
    roleTrigger.current?.focus();
  }, []);
  const cerrarAlta = useCallback(() => setCreatingAccount(false), []);

  function anunciar(mensaje: string) {
    setCreatingAccount(false);
    setRoleOf(null);
    setAviso(mensaje);
    users.reload();
    // Tras desmontar el diálogo, el foco va al aviso.
    setTimeout(() => avisoRef.current?.focus(), 0);
  }

  async function remove() {
    if (!removing) return;
    setBusy(true);
    setProblem(null);
    try {
      await api.deleteUser(removing.id);
      setRemoving(null);
      users.reload();
    } catch (err) {
      setProblem(err instanceof Error ? err.message : 'No se pudo eliminar');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Usuarios</h1>
          <p className="mt-1 text-sm text-label">
            {session?.permissions.is_admin
              ? 'Todos los usuarios del sistema.'
              : 'Usuarios de las áreas que administras.'}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {isAdmin ? (
            <>
              <Button variant="secondary" onClick={() => setDirectory(true)}>
                Buscar en directorio
              </Button>
              <Button variant="secondary" onClick={() => setShowPurge((v) => !v)}>
                {showPurge ? 'Ocultar purga' : 'Purgar inactivas'}
              </Button>
            </>
          ) : null}
          <Button onClick={() => setCreatingAccount(true)}>Nuevo usuario</Button>
        </div>
      </div>

      <div role="status" ref={avisoRef} tabIndex={-1} className="rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-primary">
        {aviso ? (
          <Card>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <SuccessNote>{aviso}</SuccessNote>
              <Button variant="secondary" onClick={() => setAviso(null)}>Cerrar aviso</Button>
            </div>
          </Card>
        ) : null}
      </div>

      {showPurge ? <PurgePanel onDone={users.reload} /> : null}

      {accessOf ? (
        <UserAccessPanel
          key={accessOf.id}
          user={accessOf}
          onClose={() => {
            setAccessOf(null);
            accessTrigger.current?.focus();
          }}
        />
      ) : null}

      {problem ? <ErrorNote message={problem} /> : null}
      {users.loading ? <Spinner /> : null}
      {users.error ? <ErrorNote message={users.error} /> : null}

      {!users.loading && !users.error ? (
        (users.data ?? []).length === 0 ? (
          <EmptyNote message="No hay usuarios dentro de tu alcance." />
        ) : (
          <div className="space-y-3">
            {(users.data ?? []).map((user) => (
              <UserCard
                key={user.id}
                user={user}
                isAdmin={isAdmin}
                onEdit={setEditing}
                onAccess={(trigger, target) => {
                  accessTrigger.current = trigger;
                  setAccessOf(target);
                }}
                onRemove={setRemoving}
                onRole={abrirRol}
              />
            ))}
          </div>
        )
      ) : null}

      {directory ? (
        <DirectoryPicker
          onClose={() => setDirectory(false)}
          onPick={(found) => {
            // Prellena el alta con lo que devuelve el directorio.
            setPrefill(found);
            setDirectory(false);
            setCreating(true);
          }}
        />
      ) : null}

      {creatingAccount ? (
        <DirectoryAccountForm
          areas={assignableAreas}
          areasLoading={isAdmin && areas.loading}
          areasError={isAdmin && areas.error ? 'No se pudieron cargar las áreas.' : null}
          areasRequired={!isAdmin}
          onClose={cerrarAlta}
          onCreated={(created) => anunciar(`Se creó la cuenta de ${created.name || created.email}.`)}
        />
      ) : null}

      {roleOf?.action === 'areas' ? (
        <AdminAreasDialog
          user={roleOf.user}
          areas={areas.data ?? []}
          areasLoading={areas.loading}
          areasError={areas.error ? 'No se pudieron cargar las áreas.' : null}
          onClose={cancelarRol}
          onSaved={anunciar}
          onStale={users.reload}
        />
      ) : null}

      {roleOf?.action === 'quitar' ? (
        <RemoveAdminDialog
          user={roleOf.user}
          onClose={cancelarRol}
          onSaved={anunciar}
          onStale={users.reload}
        />
      ) : null}

      {creating ? (
        <UserForm
          user={null} areas={areas.data ?? []} platforms={platforms.data ?? []}
          prefill={prefill}
          onClose={() => { setCreating(false); setPrefill(null); }}
          onSaved={() => {
            setCreating(false);
            setPrefill(null);
            users.reload();
          }}
        />
      ) : null}

      {editing ? (
        <UserForm
          user={editing} areas={areas.data ?? []} platforms={platforms.data ?? []}
          onClose={() => setEditing(null)}
          onSaved={() => { setEditing(null); users.reload(); }}
        />
      ) : null}

      {removing ? (
        <ConfirmDialog
          title="Eliminar usuario"
          message={`Se eliminará la cuenta de ${removing.email}. Esta acción no se puede deshacer.`}
          onConfirm={remove}
          onCancel={() => setRemoving(null)}
          busy={busy}
        />
      ) : null}
    </div>
  );
}
