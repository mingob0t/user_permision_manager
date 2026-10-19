'use client';

/**
 * "Administradores del área" (DIS-016): solo el superadmin. Lista las cuentas
 * con rol `admin_area`, con búsqueda, y asigna o quita el área con
 * `PUT /users/<id>/managed-areas` (reemplaza la lista completa de cada usuario).
 * Quitar a un administrador se confirma antes de guardar.
 */

import { useState } from 'react';
import { api } from '@/lib/api';
import { usersApi } from '@/lib/access/users';
import { useAsync } from '@/lib/use-async';
import type { Area, ManagedUser } from '@/lib/types';
import { Button, Checkbox, ConfirmDialog, Field, Modal, TextInput } from '../form';
import { Badge, EmptyNote, ErrorNote, Spinner } from '../ui';
import { mensajeDeError } from './area-errors';

function administra(user: ManagedUser, areaId: number): boolean {
  return user.managed_areas.some((a) => a.id === areaId);
}

/** Lista nueva de áreas administradas del usuario tras marcar o desmarcar el área. */
function areasNuevas(user: ManagedUser, areaId: number, marcado: boolean): number[] {
  const otras = user.managed_areas.map((a) => a.id).filter((id) => id !== areaId);
  return marcado ? [...otras, areaId] : otras;
}

function coincide(user: ManagedUser, query: string): boolean {
  const q = query.trim().toLowerCase();
  return !q || user.name.toLowerCase().includes(q) || user.email.toLowerCase().includes(q);
}

export function AreaAdminsPanel({ area, onClose }: { area: Area; onClose: () => void }) {
  const { data, loading, error, reload } = useAsync(() => api.users(), []);
  const [cambios, setCambios] = useState<Record<number, boolean>>({});
  const [query, setQuery] = useState('');
  const [saving, setSaving] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [confirming, setConfirming] = useState(false);

  const admins = (data ?? []).filter((u) => u.role === 'admin_area');
  const visibles = admins.filter((u) => coincide(u, query));
  const marcado = (u: ManagedUser) => cambios[u.id] ?? administra(u, area.id);
  const pendientes = admins.filter((u) => marcado(u) !== administra(u, area.id));
  const quitados = pendientes.filter((u) => !marcado(u));

  function alternar(user: ManagedUser, valor: boolean) {
    setSaved(false);
    setCambios({ ...cambios, [user.id]: valor });
  }

  async function guardar() {
    setConfirming(false);
    setSaving(true);
    setProblem(null);
    setSaved(false);
    try {
      for (const user of pendientes) {
        await usersApi.setManagedAreas(user.id, areasNuevas(user, area.id, marcado(user)));
      }
      setSaved(true);
    } catch (err) {
      // Lo guardado antes del error queda aplicado: se recarga el estado real.
      setProblem(`${mensajeDeError(err, 'No se pudieron guardar los cambios')} Se muestran los datos actuales.`);
    } finally {
      setCambios({});
      setSaving(false);
      reload();
    }
  }

  if (confirming) {
    return (
      <ConfirmDialog
        title="Quitar administradores"
        message={`Dejarán de administrar "${area.name}": ${quitados.map((u) => u.name || u.email).join(', ')}.`}
        confirmLabel="Quitar"
        onConfirm={guardar}
        onCancel={() => setConfirming(false)}
      />
    );
  }

  return (
    <Modal
      title={`Administradores de ${area.name}`}
      onClose={onClose}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>Cerrar</Button>
          <Button
            onClick={() => (quitados.length > 0 ? setConfirming(true) : guardar())}
            disabled={saving || pendientes.length === 0}
          >
            {saving ? 'Guardando…' : 'Guardar'}
          </Button>
        </>
      }
    >
      {problem ? <ErrorNote message={problem} /> : null}
      {saved ? (
        <div role="status"><Badge tone="success">Cambios guardados</Badge></div>
      ) : null}

      <p className="text-sm font-bold text-label">
        Solo aparecen las cuentas con rol de administrador de área; el rol se asigna en Usuarios.
      </p>

      <Field label="Buscar administrador">
        <TextInput
          type="search"
          placeholder="Nombre o correo"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </Field>

      {loading && !data ? <Spinner /> : null}
      {error ? <ErrorNote message={error} /> : null}

      {data && !error ? (
        admins.length === 0 ? (
          <EmptyNote message="No hay cuentas con rol de administrador de área." />
        ) : visibles.length === 0 ? (
          <EmptyNote message="Ningún administrador coincide con la búsqueda." />
        ) : (
          <ul className="max-h-72 space-y-3 overflow-y-auto" aria-label="Administradores de área">
            {visibles.map((user) => (
              <li key={user.id}>
                <Checkbox
                  label={`${user.name || user.email} · ${user.email}`}
                  checked={marcado(user)}
                  disabled={saving}
                  onChange={(e) => alternar(user, e.target.checked)}
                />
              </li>
            ))}
          </ul>
        )
      ) : null}
    </Modal>
  );
}
