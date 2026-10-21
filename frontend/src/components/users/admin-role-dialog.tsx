'use client';

/**
 * Elevación a admin de área (DIS-019, F-USR-03, F-AREA-02; contrato
 * `areas-y-roles.md` 2.1). Solo el superadmin la ve: `UsersList` no monta
 * estos diálogos para nadie más y el servidor vuelve a validarlo.
 *
 * - `AdminAreasDialog`: "Hacer admin" (rol `usuario` → `admin_area` con
 *   `PUT /users/<id>` y luego sus áreas con `PUT /users/<id>/managed-areas`)
 *   o cambiar las áreas de quien ya es admin. Al menos un área: para dejar
 *   ninguna se usa "Quitar admin".
 * - `RemoveAdminDialog`: "Quitar admin" (`role: usuario`); el servidor borra
 *   sus áreas administradas y revoca sus accesos automáticos (FNC-055).
 * - Es una acción sensible: el diálogo es la confirmación y explica el efecto
 *   con las áreas concretas antes de enviar. Patrón de `ApproveDialog`
 *   (DIS-015): botón primario y `aria-disabled` durante el envío.
 */

import { useState } from 'react';
import { api } from '@/lib/api';
import { usersApi } from '@/lib/access/users';
import type { AreaRef, ManagedUser } from '@/lib/types';
import { Button, Modal } from '../form';
import { ErrorNote } from '../ui';
import { AreaChecklist } from './area-checklist';
import { MENSAJE_SIN_AREAS, describeRoleError } from './admin-role-errors';

const AREAS_ID = 'admin-areas';

const PERMISOS_ADMIN =
  'Podrá aprobar y rechazar solicitudes, administrar las plataformas y las cuentas de usuario ' +
  'de esas áreas, y recibirá acceso automático de admin de área en sus plataformas.';

function nombres(areas: AreaRef[], ids: number[]): string {
  return areas.filter((a) => ids.includes(a.id)).map((a) => a.name).join(', ');
}

/** Texto del efecto según el modo y las áreas elegidas. */
export function efectoAdmin(user: ManagedUser, areas: AreaRef[], ids: number[]): string[] {
  const quien = user.name || user.email;
  if (ids.length === 0) return [];
  if (user.role !== 'admin_area') {
    return [`${quien} pasará a ser admin de área de: ${nombres(areas, ids)}.`, PERMISOS_ADMIN];
  }
  const antes = user.managed_areas.map((a) => a.id);
  const agrega = ids.filter((id) => !antes.includes(id));
  const quita = user.managed_areas.filter((a) => !ids.includes(a.id));
  const lineas: string[] = [];
  if (agrega.length > 0) {
    lineas.push(`Empezará a administrar: ${nombres(areas, agrega)}. Recibirá acceso automático en sus plataformas.`);
  }
  if (quita.length > 0) {
    lineas.push(`Dejará de administrar: ${quita.map((a) => a.name).join(', ')}. Se revocarán sus accesos automáticos de esas áreas.`);
  }
  if (lineas.length === 0) lineas.push('Sin cambios en sus áreas.');
  return lineas;
}

export function AdminAreasDialog({
  user,
  areas,
  areasLoading = false,
  areasError = null,
  onClose,
  onSaved,
  onStale,
}: {
  user: ManagedUser;
  /** Todas las áreas (el superadmin asigna cualquiera). */
  areas: AreaRef[];
  areasLoading?: boolean;
  areasError?: string | null;
  onClose: () => void;
  /** Recibe el aviso que se anunciará en la pantalla. */
  onSaved: (aviso: string) => void;
  /** La cuenta cambió en el servidor: recargar la lista. */
  onStale: () => void;
}) {
  const elevar = user.role !== 'admin_area';
  const [ids, setIds] = useState<number[]>(user.managed_areas.map((a) => a.id));
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errorAreas, setErrorAreas] = useState<string | undefined>();
  const quien = user.name || user.email;

  async function guardar() {
    if (sending) return;
    if (ids.length === 0) {
      setErrorAreas(MENSAJE_SIN_AREAS);
      if (areas[0]) document.getElementById(`${AREAS_ID}-${areas[0].id}`)?.focus();
      return;
    }
    setSending(true);
    setError(null);
    setErrorAreas(undefined);
    let rolAplicado = false;
    try {
      if (elevar) {
        // Mismo rol repetido no es una asignación (el servidor lo ignora):
        // reintentar tras un fallo del segundo paso es seguro.
        await api.updateUser(user.id, { role: 'admin_area' });
        rolAplicado = true;
      }
      await usersApi.setManagedAreas(user.id, ids);
      onSaved(elevar
        ? `${quien} ahora es admin de área de: ${nombres(areas, ids)}.`
        : `Se actualizaron las áreas que administra ${quien}.`);
    } catch (err) {
      const view = describeRoleError(err);
      setError(rolAplicado
        ? `${quien} ya es admin de área, pero no se asignaron sus áreas. ${view.message}`
        : view.message);
      if (view.stale || rolAplicado) onStale();
      setSending(false);
    }
  }

  return (
    <Modal
      title={elevar ? `Hacer admin a ${quien}` : `Áreas que administra ${quien}`}
      onClose={onClose}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button onClick={guardar} aria-disabled={sending || undefined} className="aria-disabled:opacity-40">
            {sending ? 'Guardando…' : elevar ? 'Hacer admin' : 'Guardar áreas'}
          </Button>
        </>
      }
    >
      <div aria-busy={sending} className="space-y-5">
        <AreaChecklist
          id={AREAS_ID}
          legend="Áreas que administrará"
          hint="Al menos una. Para que no administre ninguna, usa Quitar admin."
          areas={areas}
          selected={ids}
          onChange={(nuevos) => { setIds(nuevos); setErrorAreas(undefined); }}
          error={errorAreas}
          loading={areasLoading}
          loadError={areasError}
          empty="No hay áreas registradas."
        />
        <div aria-live="polite" className="space-y-2">
          {efectoAdmin(user, areas, ids).map((linea) => (
            <p key={linea} className="text-sm text-body-text">{linea}</p>
          ))}
        </div>
        {error ? <ErrorNote message={error} /> : null}
      </div>
    </Modal>
  );
}

export function RemoveAdminDialog({
  user,
  onClose,
  onSaved,
  onStale,
}: {
  user: ManagedUser;
  onClose: () => void;
  onSaved: (aviso: string) => void;
  onStale: () => void;
}) {
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const quien = user.name || user.email;
  const areas = user.managed_areas.map((a) => a.name).join(', ');

  async function quitar() {
    if (sending) return;
    setSending(true);
    setError(null);
    try {
      await api.updateUser(user.id, { role: 'usuario' });
      onSaved(`${quien} ya no es admin de área.`);
    } catch (err) {
      const view = describeRoleError(err);
      setError(view.message);
      if (view.stale) onStale();
      setSending(false);
    }
  }

  return (
    <Modal
      title={`Quitar admin a ${quien}`}
      onClose={onClose}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          {/* Primario, no `danger`: el blanco sobre `--color-error` falla AA (DIS-004). */}
          <Button onClick={quitar} aria-disabled={sending || undefined} className="aria-disabled:opacity-40">
            {sending ? 'Quitando…' : 'Quitar admin'}
          </Button>
        </>
      }
    >
      <div aria-busy={sending} className="space-y-3">
        <p className="text-sm text-body-text">
          {quien} volverá a ser Usuario
          {areas ? ` y dejará de administrar: ${areas}.` : '.'}
        </p>
        <p className="text-sm text-label">
          Se revocarán sus accesos automáticos de admin de área. Sus áreas de pertenencia y sus
          accesos solicitados no cambian.
        </p>
        {error ? <ErrorNote message={error} /> : null}
      </div>
    </Modal>
  );
}
