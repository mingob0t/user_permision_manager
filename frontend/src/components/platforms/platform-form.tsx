'use client';

/**
 * Alta y edición de una plataforma (DIS-017): campos base, sección
 * Integración, errores por campo ligados con `aria-describedby` y foco al
 * primer campo con error. Extraído de `platform-admin.tsx`.
 */

import { useState } from 'react';
import { api } from '@/lib/api';
import type { Area, Platform, PlatformInput, PlatformWarning } from '@/lib/types';
import { Button, Checkbox, Field, Modal, Select, TextArea, TextInput } from '../form';
import { ErrorNote } from '../ui';
import { describedBy, FieldErrorNote, FieldHint, focusFirstError } from './field-notes';
import {
  INTEGRATION_IDS, LOCKED_NOTE_ID, PlatformIntegrationFields, type IntegrationValue,
} from './platform-integration-fields';
import {
  buildPayload, DESCRIPCION_MAX, NOMBRE_MAX, URL_MAX, validate,
} from './platform-payload';
import { describeSaveError, MENSAJE_REVISA_CAMPOS } from './platform-save-errors';

/**
 * Alta: los colores no se envían hasta que se eligen; el servidor aplica sus
 * colores por omisión (`POR_DEFECTO_ALTA`, los mismos que antes fijaba aquí la
 * pantalla). Mismo criterio que `areas/area-form.tsx` (DIS-016).
 */
const EMPTY: PlatformInput = {
  name: '',
  description: '',
  direct_link: '',
  status: 'Activo',
};

/** Ids de los controles base, en el orden del formulario (foco al primer error). */
const IDS = {
  name: 'platform-name',
  description: 'platform-description',
  direct_link: 'platform-link',
  area_id: 'platform-area',
} as const;
const ORDEN_CAMPOS = Object.entries({ ...IDS, ...INTEGRATION_IDS }) as [string, string][];

export function PlatformForm({
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
      focusFirstError(ORDEN_CAMPOS, errors);
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
      focusFirstError(ORDEN_CAMPOS, view.fields);
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

      <div>
        <Field label="Nombre">
          <TextInput
            id={IDS.name}
            value={form.name ?? ''}
            onChange={(e) => set('name', e.target.value)}
            placeholder="Nombre de la plataforma"
            maxLength={NOMBRE_MAX}
            {...describedBy([`${IDS.name}-error`, fieldErrors.name])}
          />
        </Field>
        <FieldErrorNote id={`${IDS.name}-error`} message={fieldErrors.name} />
      </div>

      <div>
        <Field label="Descripción">
          <TextArea
            id={IDS.description}
            rows={2}
            value={form.description ?? ''}
            onChange={(e) => set('description', e.target.value)}
            maxLength={DESCRIPCION_MAX}
            {...describedBy([`${IDS.description}-error`, fieldErrors.description])}
          />
        </Field>
        <FieldErrorNote id={`${IDS.description}-error`} message={fieldErrors.description} />
      </div>

      <div>
        <Field label="Enlace">
          <TextInput
            id={IDS.direct_link}
            type="url"
            value={form.direct_link ?? ''}
            onChange={(e) => set('direct_link', e.target.value)}
            placeholder="https://…"
            maxLength={URL_MAX}
            {...describedBy([`${IDS.direct_link}-error`, fieldErrors.direct_link],
              [`${IDS.direct_link}-hint`, true])}
          />
        </Field>
        <FieldHint id={`${IDS.direct_link}-hint`}>
          Dirección https:// a la que lleva la tarjeta. Sin enlace, la plataforma se muestra pero
          no se puede abrir.
        </FieldHint>
        <FieldErrorNote id={`${IDS.direct_link}-error`} message={fieldErrors.direct_link} />
      </div>

      <div>
        <Field label="Área">
          <Select
            id={IDS.area_id}
            value={form.area_id ?? ''}
            disabled={locked}
            {...describedBy([`${IDS.area_id}-error`, fieldErrors.area_id], [LOCKED_NOTE_ID, locked])}
            onChange={(e) => set('area_id', Number(e.target.value))}
          >
            {areas.map((area) => (
              <option key={area.id} value={area.id}>
                {area.name}
              </option>
            ))}
          </Select>
        </Field>
        <FieldErrorNote id={`${IDS.area_id}-error`} message={fieldErrors.area_id} />
      </div>

      <PlatformIntegrationFields
        value={integration}
        onChange={(patch) => setIntegration((prev) => ({ ...prev, ...patch }))}
        isSuperadmin={isSuperadmin}
        isEdit={isEdit}
        currentType={currentType}
        activeGrants={platform?.active_grants}
        errors={fieldErrors}
      />

      <div>
        <div className="grid grid-cols-2 gap-4">
          <Field label="Color de fondo">
            <TextInput
              type="color"
              value={form.bg_color ?? ''}
              onChange={(e) => set('bg_color', e.target.value)}
              className="p-1"
              {...describedBy(['platform-colors-error', false],
                ['platform-colors-hint', !form.bg_color])}
            />
          </Field>
          <Field label="Color de texto">
            <TextInput
              type="color"
              value={form.text_color ?? ''}
              onChange={(e) => set('text_color', e.target.value)}
              className="p-1"
              {...describedBy(['platform-colors-error', false],
                ['platform-colors-hint', !form.text_color])}
            />
          </Field>
        </div>
        {!form.bg_color || !form.text_color ? (
          <FieldHint id="platform-colors-hint">
            Si no eliges un color, se usa el color por omisión.
          </FieldHint>
        ) : null}
      </div>

      <Checkbox
        label="Activa"
        checked={form.status === 'Activo'}
        onChange={(e) => set('status', e.target.checked ? 'Activo' : 'Inactivo')}
      />
    </Modal>
  );
}
