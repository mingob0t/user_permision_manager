'use client';

/**
 * Administración de plataformas: crear, editar y eliminar, con el tipo de
 * integración y los grupos de acceso por nivel (DIS-017). Cada fila enlaza a
 * su historial en Auditoría (DIS-035).
 */

import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import { api } from '@/lib/api';
import { enlaceSeguro } from '@/lib/enlace-seguro';
import { useAsync } from '@/lib/use-async';
import type { Platform, PlatformWarning } from '@/lib/types';
import { ACCION_FILA, ACCION_FILA_PELIGRO } from './acciones-fila';
import { rutaHistorialPlataforma } from './audit/audit-routes';
import { Button, ConfirmDialog } from './form';
import { PlatformForm } from './platforms/platform-form';
import { describeDeleteError } from './platforms/platform-save-errors';
import { PlatformSaveNotice, type SaveNotice } from './platforms/platform-save-notice';
import { RequireRole } from './require-role';
import { useSession } from './session-provider';
import { Badge, Card, EmptyNote, ErrorNote, Spinner } from './ui';

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

      {missingLink.length > 0 ? (
        <Card className="border-warning/40 bg-warning/10">
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
          <Card className="p-0">
            {/* Región desplazable con nombre y foco visible para quien usa teclado (DIS-008). */}
            <div
              role="region"
              aria-label="Plataformas"
              tabIndex={0}
              className="overflow-x-auto rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-primary"
            >
            <table className="w-full min-w-[44rem] text-sm">
              <thead className="border-b border-panel-border text-left text-xs uppercase tracking-wide text-label">
                <tr>
                  <th className="px-4 py-3 font-medium">Plataforma</th>
                  <th className="px-4 py-3 font-medium">Área</th>
                  <th className="px-4 py-3 font-medium">Enlace</th>
                  <th className="px-4 py-3 font-medium">Estado</th>
                  <th className="px-4 py-3"><span className="sr-only">Acciones</span></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-panel-border">
                {(platforms.data ?? []).map((platform) => (
                  <tr key={platform.id}>
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-2">
                        <span
                          className="grid h-7 w-7 shrink-0 place-items-center rounded text-xs font-semibold"
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
                    <td className="whitespace-nowrap px-4 py-1 text-right">
                      {/* DIS-035: historial en Auditoría y acciones de 48 px (DIS-008), en una línea. */}
                      <div className="flex justify-end gap-1">
                        <Link
                          href={rutaHistorialPlataforma(platform.id)}
                          aria-label={`Historial de ${platform.name} en Auditoría`}
                          className={ACCION_FILA}
                        >
                          Historial
                        </Link>
                        {canManage ? (
                          <>
                            <button
                              type="button"
                              onClick={(e) => open(e, () => setEditing(platform))}
                              aria-label={`Editar ${platform.name}`}
                              className={ACCION_FILA}
                            >
                              Editar
                            </button>
                            <button
                              type="button"
                              onClick={(e) => open(e, () => setRemoving(platform))}
                              aria-label={`Eliminar ${platform.name}`}
                              className={ACCION_FILA_PELIGRO}
                            >
                              Eliminar
                            </button>
                          </>
                        ) : null}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
          </Card>
        )
      ) : null}

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
