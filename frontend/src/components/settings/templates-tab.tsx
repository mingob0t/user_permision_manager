'use client';

/** Ajustes › Plantillas: correos editables por slug. */

import { useState } from 'react';
import { api } from '@/lib/api';
import { useAsync } from '@/lib/use-async';
import type { EmailTemplate } from '@/lib/types';
import { Button, Checkbox, Field, TextArea, TextInput } from '../form';
import { Card, EmptyNote, ErrorNote, Spinner } from '../ui';

export function TemplatesTab() {
  const { data, loading, error, reload } = useAsync(() => api.templates(), []);
  const [open, setOpen] = useState<EmailTemplate | null>(null);
  const [draft, setDraft] = useState<Partial<EmailTemplate>>({});
  const [saving, setSaving] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  if (loading) return <Spinner />;
  if (error) return <ErrorNote message={error} />;
  if ((data ?? []).length === 0) {
    return <EmptyNote message="No hay plantillas configuradas." />;
  }

  async function save() {
    if (!open) return;
    setSaving(true);
    setProblem(null);
    try {
      await api.saveTemplate(open.slug, draft);
      setOpen(null);
      reload();
    } catch (err) {
      setProblem(err instanceof Error ? err.message : 'No se pudo guardar');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-3">
      {(data ?? []).map((template) => {
        const isOpen = open?.slug === template.slug;
        return (
          <Card key={template.slug}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="min-w-0">
                <p className="truncate font-medium">{template.name}</p>
                <p className="truncate text-xs text-label">
                  {template.slug} · {template.subject}
                </p>
              </div>
              <Button
                variant="secondary"
                onClick={() => {
                  if (isOpen) {
                    setOpen(null);
                  } else {
                    setOpen(template);
                    setDraft({
                      name: template.name,
                      subject: template.subject,
                      body: template.body,
                      is_html: template.is_html,
                    });
                  }
                }}
              >
                {isOpen ? 'Cerrar' : 'Editar'}
              </Button>
            </div>

            {isOpen ? (
              <div className="mt-4 space-y-4 border-t border-panel-border pt-4">
                {problem ? <ErrorNote message={problem} /> : null}
                <Field label="Asunto">
                  <TextInput
                    value={draft.subject ?? ''}
                    onChange={(e) => setDraft({ ...draft, subject: e.target.value })}
                  />
                </Field>
                <Field label="Cuerpo" hint="Admite variables Jinja, p. ej. {{ nombre }}.">
                  <TextArea
                    rows={8} className="font-mono text-xs"
                    value={draft.body ?? ''}
                    onChange={(e) => setDraft({ ...draft, body: e.target.value })}
                  />
                </Field>
                <Checkbox
                  label="El cuerpo es HTML"
                  checked={Boolean(draft.is_html)}
                  onChange={(e) => setDraft({ ...draft, is_html: e.target.checked })}
                />
                <Button onClick={save} disabled={saving}>
                  {saving ? 'Guardando…' : 'Guardar plantilla'}
                </Button>
              </div>
            ) : null}
          </Card>
        );
      })}
    </div>
  );
}
