'use client';

/**
 * Administración de plataformas: crear, editar y eliminar, con el tipo de
 * integración y los grupos de acceso por nivel (DIS-017). Cada fila enlaza a
 * su historial en Auditoría (DIS-035).
 */

import { useEffect, useRef, useState } from 'react';
import { api } from '@/lib/api';
import { enlaceSeguro } from '@/lib/enlace-seguro';
import { useAsync } from '@/lib/use-async';
import type { Platform, PlatformWarning } from '@/lib/types';
import { DataTable } from './data-table';
import { Button, ConfirmDialog } from './form';
import { columnasPlataformas } from './platforms/platform-columns';
import { MissingLinkNote } from './platforms/missing-link-note';
import { PlatformForm } from './platforms/platform-form';
import { describeDeleteError } from './platforms/platform-save-errors';
import { PlatformSaveNotice, type SaveNotice } from './platforms/platform-save-notice';
import { RequireRole } from './require-role';
import { useSession } from './session-provider';
import { EmptyNote, ErrorNote } from './ui';

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
  // Foco: al cerrar un diálogo vuelve al disparador; tras guardar, al aviso.
  const trigger = useRef<HTMLElement | null>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const noticeRef = useRef<HTMLDivElement>(null);
  const [focusTarget, setFocusTarget] = useState<'trigger' | 'notice' | null>(null);
  const dialogOpen = creating || editing !== null || removing !== null;

  useEffect(() => {
    if (dialogOpen || !focusTarget) return;
    if (focusTarget === 'notice' && noticeRef.current) noticeRef.current.focus();
    else if (trigger.current?.isConnected) trigger.current.focus();
    else heading.current?.focus();
    setFocusTarget(null);
  }, [dialogOpen, focusTarget]);

  function open(event: React.MouseEvent<HTMLElement>, action: () => void) {
    trigger.current = event.currentTarget;
    action();
  }

  function closeDialogs() {
    setCreating(false);
    setEditing(null);
    setRemoving(null);
    setFocusTarget('trigger');
  }

  const isSuperadmin = Boolean(session?.permissions.is_admin);
  const canManage =
    session?.permissions.is_admin || session?.permissions.is_area_admin;

  // DIS-010: columnas de la tabla común (`DataTable`).
  const columnas = columnasPlataformas({
    canManage: Boolean(canManage),
    onEdit: (e, platform) => open(e, () => setEditing(platform)),
    onRemove: (e, platform) => open(e, () => setRemoving(platform)),
  });

  async function remove() {
    if (!removing) return;
    setBusy(true);
    setRemoveError(null);
    try {
      await api.deletePlatform(removing.id);
      closeDialogs();
      platforms.reload();
    } catch (err) {
      closeDialogs();
      setRemoveError(describeDeleteError(err));
    } finally {
      setBusy(false);
    }
  }

  function handleSaved(result: { platform: Platform; warnings: PlatformWarning[] }) {
    setCreating(false);
    setEditing(null);
    setNotice({ name: result.platform.name, warnings: result.warnings });
    setFocusTarget('notice');
    platforms.reload();
  }

  const missingLink = (platforms.data ?? []).filter((p) => !enlaceSeguro(p.direct_link));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 ref={heading} tabIndex={-1} className="text-2xl font-semibold">Administrar plataformas</h1>
          <p className="mt-1 text-sm text-label">
            Los enlaces del catálogo y a qué área pertenecen.
          </p>
        </div>
        {canManage ? (
          <Button
            onClick={(e) => open(e, () => setCreating(true))}
            disabled={areas.loading || (areas.data ?? []).length === 0}
          >
            Nueva plataforma
          </Button>
        ) : null}
      </div>

      {/* Región de estado siempre montada: el aviso se anuncia al aparecer. */}
      <div role="status">
        {notice ? (
          <PlatformSaveNotice
            ref={noticeRef}
            notice={notice}
            onDismiss={() => {
              setNotice(null);
              heading.current?.focus();
            }}
          />
        ) : null}
      </div>
      {removeError ? <ErrorNote message={removeError} /> : null}
      {areas.error ? <ErrorNote message={areas.error} /> : null}
      {canManage && !areas.loading && !areas.error && (areas.data ?? []).length === 0 ? (
        <EmptyNote message="No hay áreas en tu alcance: da de alta un área antes de crear plataformas." />
      ) : null}

      <MissingLinkNote count={missingLink.length} />

      <DataTable
        label="Plataformas"
        columns={columnas}
        rows={platforms.data ?? []}
        rowKey={(platform) => platform.id}
        loading={platforms.loading || areas.loading}
        error={platforms.error}
        emptyMessage="No hay plataformas en tu alcance."
      />

      {creating ? (
        <PlatformForm
          areas={areas.data ?? []}
          platform={null}
          isSuperadmin={isSuperadmin}
          onClose={closeDialogs}
          onSaved={handleSaved}
        />
      ) : null}

      {editing ? (
        <PlatformForm
          areas={areas.data ?? []}
          platform={editing}
          isSuperadmin={isSuperadmin}
          onClose={closeDialogs}
          onSaved={handleSaved}
        />
      ) : null}

      {removing ? (
        <ConfirmDialog
          title="Eliminar plataforma"
          message={`Se eliminará "${removing.name}". Esta acción no se puede deshacer.`}
          onConfirm={remove}
          onCancel={closeDialogs}
          busy={busy}
        />
      ) : null}
    </div>
  );
}
