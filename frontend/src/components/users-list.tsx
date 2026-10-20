'use client';

/** Usuarios: alta, edición, baja y asignación de áreas y plataformas. */

import { useState } from 'react';
import { api } from '@/lib/api';
import { usersApi } from '@/lib/access/users';
import { useAsync } from '@/lib/use-async';
import type {
  Area, DirectoryUser, InactiveUser, ManagedUser, Platform, Role, UserInput,
} from '@/lib/types';
import { Button, Checkbox, ConfirmDialog, Field, Modal, Select, TextInput } from './form';
import { useSession } from './session-provider';
import { Badge, Card, EmptyNote, ErrorNote, Spinner } from './ui';

/** El alta de cuentas que ya existen en el directorio llega con FNC-079. */
const DIRECTORY_IMPORT_PENDING =
  'El alta de cuentas del directorio aún no está disponible en el portal.';

const ROLE_LABELS: Record<string, string> = {
  administrador: 'Admin global',
  admin_area: 'Admin de área',
  usuario: 'Usuario',
};

/** Selector de etiquetas múltiple. */
function TagPicker<T extends { id: number; name: string }>({
  options,
  selected,
  onChange,
  empty,
}: {
  options: T[];
  selected: number[];
  onChange: (ids: number[]) => void;
  empty: string;
}) {
  if (options.length === 0) {
    return <p className="text-xs text-label">{empty}</p>;
  }
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((option) => {
        const on = selected.includes(option.id);
        return (
          <button
            key={option.id}
            type="button"
            aria-pressed={on}
            onClick={() =>
              onChange(on ? selected.filter((id) => id !== option.id) : [...selected, option.id])
            }
            className={`rounded-full border px-2.5 py-1 text-xs transition-colors ${
              on
                ? 'border-primary bg-primary/15 text-primary-text'
                : 'border-panel-border text-label hover:text-body-text'
            }`}
          >
            {option.name}
          </button>
        );
      })}
    </div>
  );
}

function UserForm({
  user,
  areas,
  platforms,
  prefill,
  onClose,
  onSaved,
}: {
  user: ManagedUser | null;
  areas: Area[];
  platforms: Platform[];
  /** Datos traídos del directorio para un alta. */
  prefill?: DirectoryUser | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const { session } = useSession();
  const isAdmin = session?.permissions.is_admin ?? false;

  const [form, setForm] = useState<UserInput>(
    user
      ? { name: user.name, role: user.role, is_active: user.is_active }
      : {
          email: prefill?.email ?? prefill?.account ?? '',
          name: prefill?.name ?? '',
          role: 'usuario',
          is_active: true,
          password: '',
          // `auth_source` lo fija el servidor (FNC-044): no se envía.
        },
  );
  const [areaIds, setAreaIds] = useState<number[]>(
    (user?.areas ?? []).map((a) => a.id),
  );
  const [managedIds, setManagedIds] = useState<number[]>(
    (user?.managed_areas ?? []).map((a) => a.id),
  );
  const [platformIds, setPlatformIds] = useState<number[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function save() {
    if (!user && !form.email?.trim()) {
      setError('El correo es obligatorio.');
      return;
    }
    // `POST /users` solo crea cuentas locales: dar de alta a alguien del
    // directorio así le daría una contraseña local. Espera a FNC-079.
    if (!user && prefill) {
      setError(DIRECTORY_IMPORT_PENDING);
      return;
    }
    setSaving(true);
    setError(null);
    try {
      if (user) {
        await api.updateUser(user.id, form);
        if (isAdmin && form.role === 'admin_area') {
          await usersApi.setManagedAreas(user.id, managedIds);
        }
        await api.setUserAreas(user.id, areaIds);
        if (platformIds.length > 0) {
          await api.setUserPlatforms(user.id, platformIds);
        }
      } else {
        const created = await api.createUser({ ...form, area_ids: areaIds });
        if (isAdmin && form.role === 'admin_area' && managedIds.length > 0) {
          await usersApi.setManagedAreas(created.id, managedIds);
        }
      }
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo guardar');
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal
      title={user ? `Editar ${user.name}` : 'Nuevo usuario'}
      onClose={onClose}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>Cancelar</Button>
          <Button onClick={save} disabled={saving}>
            {saving ? 'Guardando…' : 'Guardar'}
          </Button>
        </>
      }
    >
      {error ? <ErrorNote message={error} /> : null}

      {!user ? (
        <Field label="Correo">
          <TextInput
            type="email"
            value={form.email ?? ''}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
        </Field>
      ) : null}

      <Field label="Nombre">
        <TextInput
          value={form.name ?? ''}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
        />
      </Field>

      <Field
        label="Contraseña"
        hint={user ? 'Vacío conserva la actual.' : 'Si se deja vacío se usa la inicial por defecto.'}
      >
        <TextInput
          type="password" autoComplete="new-password"
          value={form.password ?? ''}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
        />
      </Field>

      <Field
        label="Rol"
        hint={isAdmin ? undefined : 'Solo un administrador global puede asignar ese rol.'}
      >
        <Select
          value={form.role ?? 'usuario'}
          onChange={(e) => setForm({ ...form, role: e.target.value as Role })}
        >
          <option value="usuario">Usuario</option>
          <option value="admin_area">Administrador de área</option>
          {/* El backend rechaza este rol si quien lo pide no es superadmin. */}
          {isAdmin ? <option value="administrador">Administrador global</option> : null}
        </Select>
      </Field>

      <Field label="Áreas a las que pertenece">
        <TagPicker
          options={areas} selected={areaIds} onChange={setAreaIds}
          empty="No hay áreas en tu alcance."
        />
      </Field>

      {/* Solo el superadmin asigna áreas administradas (FNC-044). */}
      {isAdmin && form.role === 'admin_area' ? (
        <Field label="Áreas que administra" hint="Solo entre las de tu alcance.">
          <TagPicker
            options={areas} selected={managedIds} onChange={setManagedIds}
            empty="No hay áreas en tu alcance."
          />
        </Field>
      ) : null}

      {user ? (
        <Field label="Plataformas asignadas" hint="Vacío deja las actuales sin cambios.">
          <TagPicker
            options={platforms} selected={platformIds} onChange={setPlatformIds}
            empty="No hay plataformas en tu alcance."
          />
        </Field>
      ) : null}

      <Checkbox
        label="Cuenta activa"
        checked={Boolean(form.is_active)}
        onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
      />
    </Modal>
  );
}

/** Alta de usuarios desde el directorio corporativo. */
function DirectoryPicker({
  onPick,
  onClose,
}: {
  onPick: (found: DirectoryUser) => void;
  onClose: () => void;
}) {
  const [term, setTerm] = useState('');
  const [results, setResults] = useState<DirectoryUser[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function search() {
    setBusy(true);
    setError(null);
    try {
      const found = await api.searchDirectory(term);
      setResults(found.users);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo buscar');
      setResults(null);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal
      title="Buscar en el directorio"
      onClose={onClose}
      footer={<Button variant="secondary" onClick={onClose}>Cerrar</Button>}
    >
      {error ? <ErrorNote message={error} /> : null}

      <div className="flex gap-2">
        <TextInput
          value={term}
          onChange={(e) => setTerm(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') void search(); }}
          placeholder="Nombre, cuenta o correo"
          autoFocus
        />
        <Button onClick={search} disabled={busy || term.trim().length < 2}>
          {busy ? 'Buscando…' : 'Buscar'}
        </Button>
      </div>

      {results !== null ? (
        results.length === 0 ? (
          <p className="text-sm text-label">Sin resultados.</p>
        ) : (
          <ul className="max-h-72 divide-y divide-panel-border overflow-y-auto">
            {results.map((found) => (
              <li
                key={found.account || found.email}
                className="flex items-center justify-between gap-3 py-2"
              >
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{found.name}</p>
                  <p className="truncate text-xs text-label">
                    {found.email || found.account}
                  </p>
                </div>
                {found.exists ? (
                  <Badge>Ya existe</Badge>
                ) : (
                  <Button variant="secondary" onClick={() => onPick(found)}>
                    Dar de alta
                  </Button>
                )}
              </li>
            ))}
          </ul>
        )
      ) : null}
    </Modal>
  );
}

/** Purga de cuentas sin actividad. */
function PurgePanel({ onDone }: { onDone: () => void }) {
  const [days, setDays] = useState(30);
  const [preview, setPreview] = useState<InactiveUser[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);

  async function load() {
    setBusy(true);
    setError(null);
    try {
      const result = await api.inactiveUsers(days);
      setPreview(result.users);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo consultar');
    } finally {
      setBusy(false);
    }
  }

  async function purge() {
    setBusy(true);
    try {
      await api.purgeInactiveUsers(days);
      setConfirming(false);
      setPreview(null);
      onDone();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo purgar');
      setConfirming(false);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="space-y-3">
      <div>
        <h2 className="text-sm font-medium">Purgar cuentas inactivas</h2>
        <p className="mt-1 text-sm text-label">
          Elimina las cuentas sin acceso en el periodo indicado, incluidas las
          que nunca han iniciado sesión. Nunca afecta a los administradores
          globales.
        </p>
      </div>

      {error ? <ErrorNote message={error} /> : null}

      <div className="flex flex-wrap items-end gap-2">
        <Field label="Días sin actividad">
          <TextInput
            type="number" min={7} className="w-28"
            value={String(days)}
            onChange={(e) => setDays(Number(e.target.value))}
          />
        </Field>
        <Button variant="secondary" onClick={load} disabled={busy}>
          {busy ? 'Consultando…' : 'Ver candidatas'}
        </Button>
      </div>

      {preview !== null ? (
        preview.length === 0 ? (
          <p className="text-sm text-label">
            Ninguna cuenta cumple ese criterio.
          </p>
        ) : (
          <div className="space-y-2">
            <p className="text-sm">
              <strong>{preview.length}</strong> cuenta(s) se eliminarían:
            </p>
            <ul className="max-h-48 space-y-1 overflow-y-auto text-sm text-label">
              {preview.map((user) => (
                <li key={user.id} className="truncate">
                  {user.email}
                  {' · '}
                  {user.last_login_at
                    ? `último acceso ${user.last_login_at.slice(0, 10)}`
                    : 'nunca ha entrado'}
                </li>
              ))}
            </ul>
            <Button variant="danger" onClick={() => setConfirming(true)}>
              Purgar {preview.length} cuenta(s)
            </Button>
          </div>
        )
      ) : null}

      {confirming ? (
        <ConfirmDialog
          title="Purgar cuentas inactivas"
          message={`Se eliminarán ${preview?.length ?? 0} cuenta(s) de forma permanente.`}
          confirmLabel="Purgar"
          onConfirm={purge}
          onCancel={() => setConfirming(false)}
          busy={busy}
        />
      ) : null}
    </Card>
  );
}

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

  const isAdmin = session?.permissions.is_admin ?? false;

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
          <Button onClick={() => setCreating(true)}>Nuevo usuario</Button>
        </div>
      </div>

      {showPurge ? <PurgePanel onDone={users.reload} /> : null}

      {problem ? <ErrorNote message={problem} /> : null}
      {users.loading ? <Spinner /> : null}
      {users.error ? <ErrorNote message={users.error} /> : null}

      {!users.loading && !users.error ? (
        (users.data ?? []).length === 0 ? (
          <EmptyNote message="No hay usuarios dentro de tu alcance." />
        ) : (
          <div className="space-y-3">
            {(users.data ?? []).map((user) => (
              <Card key={user.id}>
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

                <div className="mt-3 flex gap-1 border-t border-panel-border pt-3">
                  <button
                    type="button"
                    onClick={() => setEditing(user)}
                    className="rounded px-2 py-1 text-xs text-primary-text hover:bg-primary/10"
                  >
                    Editar
                  </button>
                  <button
                    type="button"
                    onClick={() => setRemoving(user)}
                    className="rounded px-2 py-1 text-xs text-error-text hover:bg-error/10"
                  >
                    Eliminar
                  </button>
                </div>
              </Card>
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
