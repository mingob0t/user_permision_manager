'use client';

/** Centro de notificaciones in-app. */

import { useState } from 'react';
import { api } from '@/lib/api';
import { useAsync } from '@/lib/use-async';
import { Button, ConfirmDialog } from './form';
import { Card, EmptyNote, ErrorNote, Spinner } from './ui';

const ICONS: Record<string, string> = {
  success: '✓', error: '✕', warning: '!', info: 'i',
};

const TONES: Record<string, string> = {
  success: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-300',
  error: 'bg-red-500/15 text-red-600 dark:text-red-300',
  warning: 'bg-amber-500/15 text-amber-600 dark:text-amber-300',
  info: 'bg-primary/15 text-primary-text',
};

export function NotificationsList() {
  const { data, loading, error, reload } = useAsync(() => api.notifications(), []);
  const [clearing, setClearing] = useState(false);
  const [busy, setBusy] = useState(false);

  const unread = (data ?? []).filter((n) => !n.is_read).length;

  async function markAll() {
    setBusy(true);
    try {
      await api.markNotificationsRead();
      reload();
    } finally {
      setBusy(false);
    }
  }

  async function clearAll() {
    setBusy(true);
    try {
      await api.clearNotifications();
      setClearing(false);
      reload();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Notificaciones</h1>
          <p className="mt-1 text-sm text-label">
            {unread > 0 ? `${unread} sin leer.` : 'Todo al día.'}
          </p>
        </div>
        <div className="flex gap-2">
          {unread > 0 ? (
            <Button variant="secondary" onClick={markAll} disabled={busy}>
              Marcar todas como leídas
            </Button>
          ) : null}
          {(data ?? []).length > 0 ? (
            <Button variant="danger" onClick={() => setClearing(true)}>
              Vaciar
            </Button>
          ) : null}
        </div>
      </div>

      {loading ? <Spinner /> : null}
      {error ? <ErrorNote message={error} /> : null}

      {!loading && !error ? (
        (data ?? []).length === 0 ? (
          <EmptyNote message="No tienes notificaciones." />
        ) : (
          <div className="space-y-2">
            {(data ?? []).map((item) => (
              <Card
                key={item.id}
                className={item.is_read ? 'opacity-70' : 'border-primary/40'}
              >
                <div className="flex gap-3">
                  <span
                    className={`grid h-7 w-7 shrink-0 place-items-center rounded-full text-xs font-bold ${TONES[item.type] ?? TONES.info}`}
                    aria-hidden
                  >
                    {ICONS[item.type] ?? 'i'}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-baseline justify-between gap-2">
                      <p className="font-medium">{item.title}</p>
                      <span className="text-xs text-label">{item.time}</span>
                    </div>
                    <p className="mt-0.5 text-sm text-label">{item.message}</p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )
      ) : null}

      {clearing ? (
        <ConfirmDialog
          title="Vaciar notificaciones"
          message="Se eliminarán tus notificaciones. Las globales del sistema no se ven afectadas."
          confirmLabel="Vaciar"
          onConfirm={clearAll}
          onCancel={() => setClearing(false)}
          busy={busy}
        />
      ) : null}
    </div>
  );
}
