'use client';

/**
 * Alta de una cuenta en el directorio (DIS-019, F-USR-02, RF-04,
 * `POST /users/directory`, contrato `usuarios-directorio.md` v1).
 *
 * - Campos de ADR-004: identificador (`uid`), correo, nombre y apellidos, y
 *   áreas a las que pertenece. La cuenta nace con rol `usuario`; hacerla
 *   admin es otra acción, solo del superadmin (`admin-role-dialog.tsx`).
 * - Sin contraseña (P8): la maneja Authelia; el portal no la pide ni la muestra.
 * - Admin de área: solo sus áreas y al menos una. Superadmin: cualquiera o ninguna.
 * - Patrón de `RevokeAccessDialog` (DIS-018): pistas y errores con
 *   `aria-describedby`, foco en el primer campo con error y `aria-disabled`
 *   durante el envío para que el foco no caiga en `body`.
 */

import { useState } from 'react';
import { usersApi } from '@/lib/access/users';
import type { AreaRef, ManagedUser } from '@/lib/types';
import { Button, Field, Modal, TextInput } from '../form';
import { FieldErrorNote, FieldHint, describedBy, focusFirstError } from '../platforms/field-notes';
import { ErrorNote } from '../ui';
import { AreaChecklist } from './area-checklist';
import {
  CORREO_MAX, NOMBRE_MAX, UID_MAX, cuerpoAlta, describeDirectoryAccountError, validarAlta,
  type CampoAlta, type FormularioAlta,
} from './directory-account-errors';

const FORM_ID = 'alta-directorio';
const IDS: Record<CampoAlta, string> = {
  uid: 'alta-directorio-uid',
  email: 'alta-directorio-correo',
  given_name: 'alta-directorio-nombre',
  surname: 'alta-directorio-apellidos',
  area_ids: 'alta-directorio-areas-1',
};
const ORDEN: [CampoAlta, string][] = [
  ['uid', IDS.uid], ['email', IDS.email], ['given_name', IDS.given_name],
  ['surname', IDS.surname], ['area_ids', IDS.area_ids],
];

const VACIO: FormularioAlta = { uid: '', email: '', given_name: '', surname: '', area_ids: [] };

export function DirectoryAccountForm({
  areas,
  areasLoading = false,
  areasError = null,
  areasRequired,
  onClose,
  onCreated,
}: {
  /** Áreas que el actor puede asignar (admin de área: solo las suyas). */
  areas: AreaRef[];
  areasLoading?: boolean;
  areasError?: string | null;
  /** El admin de área debe elegir al menos una; el superadmin no. */
  areasRequired: boolean;
  onClose: () => void;
  /** Recibe la cuenta que devolvió el servidor. */
  onCreated: (user: ManagedUser) => void;
}) {
  const [form, setForm] = useState<FormularioAlta>(VACIO);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fields, setFields] = useState<Partial<Record<CampoAlta, string>>>({});

  // El primer área es la casilla que recibe el foco si falta elegir una.
  const ordenConAreas: [CampoAlta, string][] = ORDEN.map(([campo, id]) =>
    campo === 'area_ids' && areas[0] ? [campo, `alta-directorio-areas-${areas[0].id}`] : [campo, id]);

  function cambiar<K extends keyof FormularioAlta>(campo: K, valor: FormularioAlta[K]) {
    setForm({ ...form, [campo]: valor });
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (sending) return;
    const errores = validarAlta(form, areasRequired);
    if (Object.keys(errores).length > 0) {
      setError(null);
      setFields(errores);
      focusFirstError(ordenConAreas, errores as Record<string, string>);
      return;
    }
    setSending(true);
    setError(null);
    setFields({});
    try {
      const result = await usersApi.createDirectoryAccount(cuerpoAlta(form));
      onCreated(result.user);
    } catch (err) {
      const view = describeDirectoryAccountError(err);
      setError(view.message);
      setFields(view.fields);
      focusFirstError(ordenConAreas, view.fields as Record<string, string>);
      setSending(false);
    }
  }

  function campoTexto(
    campo: Exclude<CampoAlta, 'area_ids'>,
    label: string,
    pista: string,
    extra: React.InputHTMLAttributes<HTMLInputElement> = {},
  ) {
    const pistaId = `${IDS[campo]}-pista`;
    const errorId = `${IDS[campo]}-error`;
    return (
      <div>
        <Field label={label}>
          <TextInput
            id={IDS[campo]}
            value={form[campo]}
            onChange={(event) => cambiar(campo, event.target.value)}
            required
            aria-required="true"
            {...extra}
            {...describedBy([errorId, fields[campo]], [pistaId, true])}
          />
        </Field>
        <FieldHint id={pistaId}>{pista}</FieldHint>
        <FieldErrorNote id={errorId} message={fields[campo]} />
      </div>
    );
  }

  return (
    <Modal
      title="Nueva cuenta en el directorio"
      onClose={onClose}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button
            type="submit"
            form={FORM_ID}
            aria-disabled={sending || undefined}
            className="aria-disabled:opacity-40"
          >
            {sending ? 'Creando…' : 'Crear cuenta'}
          </Button>
        </>
      }
    >
      <form id={FORM_ID} onSubmit={submit} noValidate aria-busy={sending} className="space-y-5">
        <p className="text-sm text-label">Todos los campos son obligatorios salvo las áreas.</p>
        <p className="text-sm text-label">
          La cuenta se crea en el directorio corporativo con rol Usuario. La persona define su
          contraseña al entrar por el inicio de sesión corporativo; el portal no la pide.
        </p>

        {campoTexto('uid', 'Identificador', `Cuenta de acceso, de 3 a ${UID_MAX}: minúsculas, números, punto, guion o guion bajo.`, {
          autoComplete: 'off', autoCapitalize: 'none', spellCheck: false, maxLength: UID_MAX,
        })}
        {campoTexto('email', 'Correo', `Hasta ${CORREO_MAX} caracteres.`, {
          type: 'email', autoComplete: 'off', maxLength: CORREO_MAX,
        })}
        <div className="grid gap-5 sm:grid-cols-2">
          {campoTexto('given_name', 'Nombre', `Hasta ${NOMBRE_MAX} caracteres.`, {
            autoComplete: 'off', maxLength: NOMBRE_MAX,
          })}
          {campoTexto('surname', 'Apellidos', `Hasta ${NOMBRE_MAX} caracteres.`, {
            autoComplete: 'off', maxLength: NOMBRE_MAX,
          })}
        </div>

        <AreaChecklist
          id="alta-directorio-areas"
          legend="Áreas a las que pertenece"
          hint={areasRequired ? 'Elige al menos una de las áreas que administras.' : 'Opcional.'}
          areas={areas}
          selected={form.area_ids}
          onChange={(ids) => cambiar('area_ids', ids)}
          error={fields.area_ids}
          loading={areasLoading}
          loadError={areasError}
          empty="No hay áreas en tu alcance."
        />

        {error ? <ErrorNote message={error} /> : null}
      </form>
    </Modal>
  );
}
