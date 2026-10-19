'use client';

/**
 * Administración de plataformas: crear, editar y eliminar, con el tipo de
 * integración y los grupos de acceso por nivel (DIS-017).
 */

import { useState } from 'react';
import { api } from '@/lib/api';
import { enlaceSeguro } from '@/lib/enlace-seguro';
import { useAsync } from '@/lib/use-async';
import type { Area, Platform, PlatformInput, PlatformWarning } from '@/lib/types';
import { Button, Checkbox, ConfirmDialog, Field, Modal, Select, TextArea, TextInput } from './form';
import {
  PlatformIntegrationFields,
  type IntegrationValue,
} from './platforms/platform-integration-fields';
import { describeSaveError, MENSAJE_REVISA_CAMPOS } from './platforms/platform-save-errors';
import { PlatformSaveNotice, type SaveNotice } from './platforms/platform-save-notice';
import { RequireRole } from './require-role';
import { useSession } from './session-provider';
import { Badge, Card, EmptyNote, ErrorNote, Spinner } from './ui';

const EMPTY: PlatformInput = {
  name: '',
  description: '',
  direct_link: '',
  bg_color: '#6366f1',
  text_color: '#ffffff',
  status: 'Activo',
};

/** Largos de la lista blanca del contrato (`plataformas-integracion.md`). */
const NOMBRE_MIN = 2;
const NOMBRE_MAX = 100;
const DESCRIPCION_MAX = 1000;
const URL_MAX = 255;

function FieldErrorNote({ message }: { message?: string }) {
  return message ? <ErrorNote message={message} /> : null;
}

/** Validación previa al envío; el backend vuelve a validar todo. */
function validate(form: PlatformInput, integration: IntegrationValue, isEdit: boolean) {
  const errors: Record<string, string> = {};
  const name = form.name?.trim() ?? '';
  if (name.length < NOMBRE_MIN || name.length > NOMBRE_MAX) {
    errors.name = `El nombre debe tener entre ${NOMBRE_MIN} y ${NOMBRE_MAX} caracteres.`;
  }
  if (!form.description?.trim()) errors.description = 'La descripción es obligatoria.';
  if (!form.area_id) errors.area_id = 'Selecciona un área.';
  const link = form.direct_link?.trim();
  if (link && !enlaceSeguro(link)) errors.direct_link = 'Usa una dirección https://.';
  if (!isEdit && !integration.integration_type) {
    errors.integration_type = 'Selecciona el tipo de integración.';
  }
  const dnUsuario = integration.ldap_group_user_dn.trim().toLowerCase();
  if (dnUsuario && dnUsuario === integration.ldap_group_admin_dn.trim().toLowerCase()) {
    errors.ldap_group_admin_dn = 'Los grupos de usuario y admin deben ser distintos.';
  }
  return errors;
}

/**
 * Cuerpo de `POST/PUT /platforms`. Un admin de área nunca envía DN ni, en la
 * edición, el tipo (`403 dn_solo_superadmin`); un DN vacío o sin cambios no
 * se envía (el backend lo deriva en el alta y lo conserva en la edición).
 */
function buildPayload(
  form: PlatformInput,
  integration: IntegrationValue,
  initial: IntegrationValue,
  { isEdit, isSuperadmin, currentType }: {
    isEdit: boolean; isSuperadmin: boolean; currentType: Platform['integration_type'] | null;
  },
): PlatformInput {
  const payload: PlatformInput = {
    ...form,
    name: form.name?.trim(),
    description: form.description?.trim(),
    direct_link: form.direct_link?.trim() ?? '',
  };
  const tipo = integration.integration_type || currentType || '';
  if (integration.integration_type && (!isEdit || isSuperadmin)) {
    payload.integration_type = integration.integration_type;
  }
  if (isSuperadmin && tipo === 'ldap') {
    for (const campo of ['ldap_group_user_dn', 'ldap_group_admin_dn'] as const) {
      const dn = integration[campo].trim();
      if (dn && dn !== initial[campo]) payload[campo] = dn;
    }
  }
  return payload;
}

function PlatformForm({
  areas,
  platform,
  isSuperadmin,
  onClose,
  onSaved,
}: {
  areas: Area[];
  platform: Platform | null;
  isSuperadmin: boolean;
  onClose: () => void;
  onSaved: (result: { platform: Platform; warnings: PlatformWarning[] }) => void;
}) {
  const isEdit = platform !== null;
  // `GET /platforms` aún no expone los campos de integración (FNC-063).
  const currentType = platform?.integration_type ?? null;
  const locked = isEdit && (platform?.active_grants ?? 0) > 0;
  const initialIntegration: IntegrationValue = {
    integration_type: '',
    ldap_group_user_dn: platform?.ldap_group_user_dn ?? '',
    ldap_group_admin_dn: platform?.ldap_group_admin_dn ?? '',
  };
  const [form, setForm] = useState<PlatformInput>(
    platform
      ? {
          name: platform.name,
          description: platform.description,
          area_id: platform.area_id,
          direct_link: platform.direct_link ?? '',
          bg_color: platform.bg_color,
          text_color: platform.text_color,
          status: platform.status,
        }
      : { ...EMPTY, area_id: areas[0]?.id },
  );
  const [integration, setIntegration] = useState<IntegrationValue>(initialIntegration);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  function set<K extends keyof PlatformInput>(key: K, value: PlatformInput[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function save() {
    const errors = validate(form, integration, isEdit);
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) {
      setError(MENSAJE_REVISA_CAMPOS);
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const payload = buildPayload(form, integration, initialIntegration,
        { isEdit, isSuperadmin, currentType });
      const result = platform
        ? await api.updatePlatform(platform.id, payload)
        : await api.createPlatform(payload);
      onSaved({ platform: result.platform, warnings: result.warnings ?? [] });
    } catch (err) {
      const view = describeSaveError(err);
      setError(view.message);
      setFieldErrors(view.fields);
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal
      title={platform ? `Editar ${platform.name}` : 'Nueva plataforma'}
      onClose={onClose}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button onClick={save} disabled={saving}>
            {saving ? 'Guardando…' : 'Guardar'}
          </Button>
        </>
      }
    >
      {error ? <ErrorNote message={error} /> : null}

      <Field label="Nombre">
        <TextInput
          value={form.name ?? ''}
          onChange={(e) => set('name', e.target.value)}
          placeholder="Nombre de la plataforma"
          maxLength={NOMBRE_MAX}
          aria-invalid={fieldErrors.name ? true : undefined}
        />
        <FieldErrorNote message={fieldErrors.name} />
      </Field>

      <Field label="Descripción">
        <TextArea
          rows={2}
          value={form.description ?? ''}
          onChange={(e) => set('description', e.target.value)}
          maxLength={DESCRIPCION_MAX}
          aria-invalid={fieldErrors.description ? true : undefined}
        />
        <FieldErrorNote message={fieldErrors.description} />
      </Field>

      <Field
        label="Enlace"
        hint="Dirección https:// a la que lleva la tarjeta. Sin enlace, la plataforma se muestra pero no se puede abrir."
      >
        <TextInput
          type="url"
          value={form.direct_link ?? ''}
          onChange={(e) => set('direct_link', e.target.value)}
          placeholder="https://…"
          maxLength={URL_MAX}
          aria-invalid={fieldErrors.direct_link ? true : undefined}
        />
        <FieldErrorNote message={fieldErrors.direct_link} />
      </Field>

      <Field
        label="Área"
        hint={locked ? 'Con accesos vigentes no se puede cambiar el área.' : undefined}
      >
        <Select
          value={form.area_id ?? ''}
          disabled={locked}
          aria-invalid={fieldErrors.area_id ? true : undefined}
          onChange={(e) => set('area_id', Number(e.target.value))}
        >
          {areas.map((area) => (
            <option key={area.id} value={area.id}>
              {area.name}
            </option>
          ))}
        </Select>
        <FieldErrorNote message={fieldErrors.area_id} />
      </Field>

      <PlatformIntegrationFields
        value={integration}
        onChange={(patch) => setIntegration((prev) => ({ ...prev, ...patch }))}
        isSuperadmin={isSuperadmin}
        isEdit={isEdit}
        currentType={currentType}
        activeGrants={platform?.active_grants}
        errors={fieldErrors}
      />

      <div className="grid grid-cols-2 gap-4">
        <Field label="Color de fondo">
          <TextInput
            type="color"
            value={form.bg_color ?? '#6366f1'}
            onChange={(e) => set('bg_color', e.target.value)}
            className="h-10 p-1"
          />
        </Field>
        <Field label="Color de texto">
          <TextInput
            type="color"
            value={form.text_color ?? '#ffffff'}
            onChange={(e) => set('text_color', e.target.value)}
            className="h-10 p-1"
          />
        </Field>
      </div>

      <Checkbox
        label="Activa"
        checked={form.status === 'Activo'}
        onChange={(e) => set('status', e.target.checked ? 'Activo' : 'Inactivo')}
      />
    </Modal>
  );
}

export function PlatformAdmin() {
  return (
    <RequireRole requires="any_admin">
      <PlatformAdminContent />
    </RequireRole>
  );
}

function PlatformAdminContent() {
  const { session } = useSession();
  const areas = useAsync(() => api.areas(), []);
  const platforms = useAsync(() => api.platforms(), []);
  const [editing, setEditing] = useState<Platform | null>(null);
  const [creating, setCreating] = useState(false);
  const [removing, setRemoving] = useState<Platform | null>(null);
  const [busy, setBusy] = useState(false);
  const [removeError, setRemoveError] = useState<string | null>(null);
  const [notice, setNotice] = useState<SaveNotice | null>(null);

  const isSuperadmin = Boolean(session?.permissions.is_admin);
  const canManage =
    session?.permissions.is_admin || session?.permissions.is_area_admin;

  async function remove() {
    if (!removing) return;
    setBusy(true);
    setRemoveError(null);
    try {
      await api.deletePlatform(removing.id);
      setRemoving(null);
      platforms.reload();
    } catch (err) {
      setRemoving(null);
      setRemoveError(err instanceof Error ? err.message : 'No se pudo eliminar la plataforma.');
    } finally {
      setBusy(false);
    }
  }

  function handleSaved(result: { platform: Platform; warnings: PlatformWarning[] }) {
    setCreating(false);
    setEditing(null);
    setNotice({ name: result.platform.name, warnings: result.warnings });
    platforms.reload();
  }

  const missingLink = (platforms.data ?? []).filter((p) => !enlaceSeguro(p.direct_link));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Administrar plataformas</h1>
          <p className="mt-1 text-sm text-label">
            Los enlaces del catálogo y a qué área pertenecen.
          </p>
        </div>
        {canManage ? (
          <Button
            onClick={() => setCreating(true)}
            disabled={areas.loading || (areas.data ?? []).length === 0}
          >
            Nueva plataforma
          </Button>
        ) : null}
      </div>

      {notice ? (
        <PlatformSaveNotice notice={notice} onDismiss={() => setNotice(null)} />
      ) : null}
      {removeError ? <ErrorNote message={removeError} /> : null}
      {areas.error ? <ErrorNote message={areas.error} /> : null}
      {canManage && !areas.loading && !areas.error && (areas.data ?? []).length === 0 ? (
        <EmptyNote message="No hay áreas en tu alcance: da de alta un área antes de crear plataformas." />
      ) : null}

      {missingLink.length > 0 ? (
        <Card className="border-amber-500/40 bg-amber-500/10">
          <p className="text-sm">
            <strong>{missingLink.length}</strong>{' '}
            {missingLink.length === 1 ? 'plataforma no tiene' : 'plataformas no tienen'}{' '}
            enlace configurado, así que no se pueden abrir desde el catálogo.
          </p>
        </Card>
      ) : null}

      {platforms.loading || areas.loading ? <Spinner /> : null}
      {platforms.error ? <ErrorNote message={platforms.error} /> : null}

      {!platforms.loading && !platforms.error ? (
        (platforms.data ?? []).length === 0 ? (
          <EmptyNote message="No hay plataformas en tu alcance." />
        ) : (
          <Card className="overflow-x-auto p-0">
            <table className="w-full min-w-[44rem] text-sm">
              <thead className="border-b border-panel-border text-left text-xs uppercase tracking-wide text-label">
                <tr>
                  <th className="px-4 py-3 font-medium">Plataforma</th>
                  <th className="px-4 py-3 font-medium">Área</th>
                  <th className="px-4 py-3 font-medium">Enlace</th>
                  <th className="px-4 py-3 font-medium">Estado</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-panel-border">
                {(platforms.data ?? []).map((platform) => (
                  <tr key={platform.id}>
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-2">
                        <span
                          className="grid h-7 w-7 shrink-0 place-items-center rounded text-[10px] font-semibold"
                          style={{
                            background: platform.bg_color,
                            color: platform.text_color,
                          }}
                          aria-hidden
                        >
                          {platform.name.slice(0, 2).toUpperCase()}
                        </span>
                        <span className="truncate font-medium">{platform.name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-2.5 text-label">
                      {platform.area_name ?? '—'}
                    </td>
                    <td className="max-w-xs px-4 py-2.5">
                      {enlaceSeguro(platform.direct_link) ? (
                        <span className="block truncate text-label" title={platform.direct_link ?? undefined}>
                          {platform.direct_link}
                        </span>
                      ) : (
                        <Badge tone="warning">Sin enlace</Badge>
                      )}
                    </td>
                    <td className="px-4 py-2.5">
                      <Badge tone={platform.status === 'Activo' ? 'success' : 'warning'}>
                        {platform.status}
                      </Badge>
                    </td>
                    <td className="whitespace-nowrap px-4 py-2.5 text-right">
                      {canManage ? (
                        <div className="flex justify-end gap-1">
                          <button
                            type="button"
                            onClick={() => setEditing(platform)}
                            className="rounded px-2 py-1 text-xs text-primary hover:bg-primary/10"
                          >
                            Editar
                          </button>
                          <button
                            type="button"
                            onClick={() => setRemoving(platform)}
                            className="rounded px-2 py-1 text-xs text-red-600 hover:bg-red-500/10 dark:text-red-300"
                          >
                            Eliminar
                          </button>
                        </div>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )
      ) : null}

      {creating ? (
        <PlatformForm
          areas={areas.data ?? []}
          platform={null}
          isSuperadmin={isSuperadmin}
          onClose={() => setCreating(false)}
          onSaved={handleSaved}
        />
      ) : null}

      {editing ? (
        <PlatformForm
          areas={areas.data ?? []}
          platform={editing}
          isSuperadmin={isSuperadmin}
          onClose={() => setEditing(null)}
          onSaved={handleSaved}
        />
      ) : null}

      {removing ? (
        <ConfirmDialog
          title="Eliminar plataforma"
          message={`Se eliminará "${removing.name}". Esta acción no se puede deshacer.`}
          onConfirm={remove}
          onCancel={() => setRemoving(null)}
          busy={busy}
        />
      ) : null}
    </div>
  );
}
