'use client';

/** Modal de alta y edición de un usuario (áreas y plataformas por chips). */

import { useState } from 'react';
import { api } from '@/lib/api';
import type { Area, DirectoryUser, ManagedUser, Platform, UserInput } from '@/lib/types';
import { Button, Checkbox, Field, Modal, TextInput } from '../form';
import { ErrorNote } from '../ui';
import { GrupoChips } from './grupo-chips';
import { TagPicker } from './tag-picker';

/** El alta de cuentas que ya existen en el directorio llega con FNC-079. */
const DIRECTORY_IMPORT_PENDING =
  'El alta de cuentas del directorio aún no está disponible en el portal.';


export function UserForm({
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
  // DIS-019: el rol y las áreas administradas ya no se editan aquí (acciones
  // "Hacer admin" / "Quitar admin" del superadmin). La contraseña solo se
  // ofrece para la cuenta de emergencia (superadmin local, contrato v2).
  const conContrasena = user?.role === 'administrador' && user.auth_source === 'local';
  const [form, setForm] = useState<UserInput>(
    user
      ? { name: user.name, is_active: user.is_active }
      : {
          email: prefill?.email ?? prefill?.account ?? '',
          name: prefill?.name ?? '',
          role: 'usuario',
          is_active: true,
          // `auth_source` lo fija el servidor (FNC-044): no se envía.
        },
  );
  const [areaIds, setAreaIds] = useState<number[]>(
    (user?.areas ?? []).map((a) => a.id),
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
        await api.setUserAreas(user.id, areaIds);
        if (platformIds.length > 0) {
          await api.setUserPlatforms(user.id, platformIds);
        }
      } else {
        await api.createUser({ ...form, area_ids: areaIds });
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

      {conContrasena ? (
        <Field
          label="Contraseña"
          hint="Solo la cuenta de emergencia tiene contraseña en el portal. Vacío conserva la actual."
        >
          <TextInput
            type="password" autoComplete="new-password"
            value={form.password ?? ''}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
          />
        </Field>
      ) : null}

      <GrupoChips legend="Áreas a las que pertenece">
        <TagPicker
          options={areas} selected={areaIds} onChange={setAreaIds}
          empty="No hay áreas en tu alcance."
        />
      </GrupoChips>

      {user ? (
        <GrupoChips legend="Plataformas asignadas" hint="Vacío deja las actuales sin cambios.">
          <TagPicker
            options={platforms} selected={platformIds} onChange={setPlatformIds}
            empty="No hay plataformas en tu alcance."
          />
        </GrupoChips>
      ) : null}

      <Checkbox
        label="Cuenta activa"
        checked={Boolean(form.is_active)}
        onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
      />
    </Modal>
  );
}
