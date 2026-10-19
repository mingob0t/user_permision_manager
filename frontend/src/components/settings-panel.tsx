'use client';

/** Configuración del sistema: portal, SMTP, plantillas y directorio. */

import { useState } from 'react';
import { api } from '@/lib/api';
import { useAsync } from '@/lib/use-async';
import type { EmailTemplate } from '@/lib/types';
import { Button, Checkbox, Field, Select, TextArea, TextInput } from './form';
import { useSession } from './session-provider';
import { Card, EmptyNote, ErrorNote, Spinner } from './ui';

type Tab = 'portal' | 'smtp' | 'templates' | 'ldap' | 'backup' | 'preferences';

function Saved({ show }: { show: boolean }) {
  if (!show) return null;
  return <span className="text-sm text-emerald-600 dark:text-emerald-300">Guardado.</span>;
}

/** Identidad visual del portal. */
function PortalTab() {
  const { data, loading, error, reload } = useAsync(() => api.settings(), []);
  const [form, setForm] = useState<Record<string, string> | null>(null);
  const [state, setState] = useState<{ saving: boolean; saved: boolean; error: string | null }>(
    { saving: false, saved: false, error: null },
  );

  if (loading) return <Spinner />;
  if (error) return <ErrorNote message={error} />;
  if (!data) return null;

  const value = form ?? {
    portal_name: data.portal_name ?? '',
    bg_color: data.bg_color ?? '#0f172a',
    text_color: data.text_color ?? '#ffffff',
    portal_identity_type: data.portal_identity_type ?? 'icon',
    portal_icon: data.portal_icon ?? '',
  };

  /** Convierte la imagen elegida en data URI: el logo se guarda en la base de
   *  datos, no como archivo en el servidor. */
  function pickLogo(file: File) {
    if (file.size > 512 * 1024) {
      setState({ ...state, error: 'La imagen supera 512 KB.' });
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      setForm({
        ...value,
        portal_identity_type: 'image',
        portal_icon: String(reader.result),
      });
    };
    reader.readAsDataURL(file);
  }

  async function save() {
    setState({ saving: true, saved: false, error: null });
    try {
      await api.saveSettings(value);
      setState({ saving: false, saved: true, error: null });
      reload();
    } catch (err) {
      setState({
        saving: false, saved: false,
        error: err instanceof Error ? err.message : 'No se pudo guardar',
      });
    }
  }

  return (
    <Card className="space-y-4">
      {state.error ? <ErrorNote message={state.error} /> : null}

      <Field label="Nombre del portal">
        <TextInput
          value={value.portal_name}
          onChange={(e) => setForm({ ...value, portal_name: e.target.value })}
        />
      </Field>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Color de fondo">
          <TextInput
            type="color" className="h-10 p-1"
            value={value.bg_color}
            onChange={(e) => setForm({ ...value, bg_color: e.target.value })}
          />
        </Field>
        <Field label="Color de texto">
          <TextInput
            type="color" className="h-10 p-1"
            value={value.text_color}
            onChange={(e) => setForm({ ...value, text_color: e.target.value })}
          />
        </Field>
      </div>

      <Field
        label="Logo del portal"
        hint="PNG, JPEG, GIF, WebP o SVG, hasta 512 KB. Se guarda en la base de datos."
      >
        <div className="flex flex-wrap items-center gap-3">
          {value.portal_identity_type === 'image' && value.portal_icon ? (
            // El logo es un data URI guardado en la BD: next/image no lo optimiza.
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={value.portal_icon}
              alt="Logo actual"
              className="h-10 w-10 rounded border border-panel-border object-contain"
            />
          ) : null}
          <input
            type="file"
            accept="image/png,image/jpeg,image/gif,image/webp,image/svg+xml"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) pickLogo(file);
            }}
            className="text-sm text-label"
          />
          {value.portal_identity_type === 'image' ? (
            <Button
              variant="secondary"
              onClick={() =>
                setForm({ ...value, portal_identity_type: 'icon', portal_icon: '' })
              }
            >
              Quitar
            </Button>
          ) : null}
        </div>
      </Field>

      <div className="flex items-center gap-3">
        <Button onClick={save} disabled={state.saving}>
          {state.saving ? 'Guardando…' : 'Guardar'}
        </Button>
        <Saved show={state.saved} />
      </div>
    </Card>
  );
}

/** Respaldo y restauración de la configuración. */
function BackupTab() {
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function download() {
    setBusy(true);
    setError(null);
    setDone(null);
    try {
      const blob = await api.downloadBackup();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const stamp = new Date().toISOString().slice(0, 10);
      link.download = `nexus_backup_${stamp}.zip`;
      link.click();
      URL.revokeObjectURL(url);
      setDone('Respaldo descargado.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo descargar');
    } finally {
      setBusy(false);
    }
  }

  async function restore(file: File) {
    setBusy(true);
    setError(null);
    setDone(null);
    try {
      const result = await api.uploadBackup(file);
      setDone(`Restaurado: ${result.restored.join(', ') || 'nada'}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo restaurar');
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="space-y-5">
      {error ? <ErrorNote message={error} /> : null}
      {done ? (
        <p className="text-sm text-emerald-600 dark:text-emerald-300">{done}</p>
      ) : null}

      <div>
        <h2 className="text-sm font-medium">Descargar respaldo</h2>
        <p className="mt-1 text-sm text-label">
          Incluye la identidad del portal, el directorio, el correo, las
          plantillas y las cuentas locales.
        </p>
        <Button onClick={download} disabled={busy} className="mt-3">
          {busy ? 'Preparando…' : 'Descargar ZIP'}
        </Button>
      </div>

      <div className="border-t border-panel-border pt-5">
        <h2 className="text-sm font-medium">Restaurar</h2>
        <p className="mt-1 text-sm text-label">
          Sobrescribe la configuración con la del paquete. Las cuentas que ya
          existan no se modifican.
        </p>
        <input
          type="file"
          accept=".zip,application/zip"
          disabled={busy}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) restore(file);
          }}
          className="mt-3 block text-sm text-label"
        />
      </div>
    </Card>
  );
}

/** Servidor de correo saliente. */
function SmtpTab() {
  const { data, loading, error, reload } = useAsync(() => api.smtp(), []);
  const [form, setForm] = useState<Record<string, unknown> | null>(null);
  const [password, setPassword] = useState('');
  const [target, setTarget] = useState('');
  const [state, setState] = useState<{ saving: boolean; saved: boolean; error: string | null; tested: string | null }>(
    { saving: false, saved: false, error: null, tested: null },
  );

  if (loading) return <Spinner />;
  if (error) return <ErrorNote message={error} />;
  if (!data) return null;

  // Con SMTP_FORCE_ENV el servidor ignora lo que se guarde aquí, así que los
  // campos se muestran en solo lectura en lugar de fingir que se pueden editar.
  const locked = data.editable === false;

  const value = form ?? {
    server: data.server ?? '',
    port: data.port ?? 587,
    encryption: data.encryption ?? 'starttls',
    username: data.username ?? '',
    sender_name: data.sender_name ?? '',
    auth_enabled: data.auth_enabled ?? true,
  };

  async function save() {
    setState({ ...state, saving: true, saved: false, error: null });
    try {
      // Una contraseña vacía deja la guardada intacta.
      await api.saveSmtp({ ...value, ...(password ? { password } : {}) });
      setPassword('');
      setState({ saving: false, saved: true, error: null, tested: null });
      reload();
    } catch (err) {
      setState({
        saving: false, saved: false, tested: null,
        error: err instanceof Error ? err.message : 'No se pudo guardar',
      });
    }
  }

  async function test() {
    setState({ ...state, tested: null, error: null });
    try {
      await api.testSmtp(target);
      setState({ ...state, tested: `Correo enviado a ${target}.`, error: null });
    } catch (err) {
      setState({
        ...state, tested: null,
        error: err instanceof Error ? err.message : 'No se pudo enviar',
      });
    }
  }

  return (
    <Card className="space-y-4">
      {state.error ? <ErrorNote message={state.error} /> : null}
      {data.warning ? <ErrorNote message={data.warning} /> : null}

      {locked ? (
        <div className="rounded-xl border border-primary/40 bg-primary/10 p-3 text-sm">
          Estos valores vienen del <code>.env</code> del servidor
          (<code>SMTP_FORCE_ENV</code>) y no se pueden cambiar desde aquí. Para
          modificarlos, edita el archivo y reinicia el servicio.
        </div>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Servidor">
          <TextInput
            disabled={locked}
            value={String(value.server)}
            onChange={(e) => setForm({ ...value, server: e.target.value })}
          />
        </Field>
        <Field label="Puerto">
          <TextInput
            type="number"
            disabled={locked}
            value={String(value.port)}
            onChange={(e) => setForm({ ...value, port: Number(e.target.value) })}
          />
        </Field>
      </div>

      <Field label="Cifrado">
        <Select
          disabled={locked}
          value={String(value.encryption)}
          onChange={(e) => setForm({ ...value, encryption: e.target.value })}
        >
          <option value="starttls">STARTTLS</option>
          <option value="ssl">SSL/TLS</option>
          <option value="none">Ninguno</option>
        </Select>
      </Field>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Usuario">
          <TextInput
            disabled={locked}
            value={String(value.username ?? '')}
            onChange={(e) => setForm({ ...value, username: e.target.value })}
          />
        </Field>
        <Field label="Contraseña" hint="Vacío conserva la actual.">
          <TextInput
            type="password" value={password} autoComplete="new-password"
            disabled={locked}
            onChange={(e) => setPassword(e.target.value)}
          />
        </Field>
      </div>

      <Field label="Nombre del remitente">
        <TextInput
          disabled={locked}
          value={String(value.sender_name ?? '')}
          onChange={(e) => setForm({ ...value, sender_name: e.target.value })}
        />
      </Field>

      <Checkbox
        label="Requiere autenticación"
        disabled={locked}
        checked={Boolean(value.auth_enabled)}
        onChange={(e) => setForm({ ...value, auth_enabled: e.target.checked })}
      />

      {!locked ? (
        <div className="flex items-center gap-3">
          <Button onClick={save} disabled={state.saving}>
            {state.saving ? 'Guardando…' : 'Guardar'}
          </Button>
          <Saved show={state.saved} />
        </div>
      ) : null}

      <div className="border-t border-panel-border pt-4">
        <Field label="Enviar correo de prueba">
          <div className="flex gap-2">
            <TextInput
              type="email" placeholder="destino@ejemplo.com" value={target}
              onChange={(e) => setTarget(e.target.value)}
            />
            <Button variant="secondary" onClick={test} disabled={!target}>
              Enviar
            </Button>
          </div>
        </Field>
        {state.tested ? (
          <p className="mt-2 text-sm text-emerald-600 dark:text-emerald-300">
            {state.tested}
          </p>
        ) : null}
      </div>
    </Card>
  );
}

/** Plantillas de correo, editables por slug. */
function TemplatesTab() {
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

/** Directorio corporativo (LDAP). */
function LdapTab() {
  const { data, loading, error, reload } = useAsync(() => api.authConfig(), []);
  const [form, setForm] = useState<Record<string, unknown> | null>(null);
  const [password, setPassword] = useState('');
  const [state, setState] = useState<{ saving: boolean; saved: boolean; error: string | null; probe: string | null }>(
    { saving: false, saved: false, error: null, probe: null },
  );

  if (loading) return <Spinner />;
  if (error) return <ErrorNote message={error} />;
  if (!data) return null;

  const value = form ?? {
    ldap_host: data.ldap_host ?? '',
    ldap_port: data.ldap_port ?? 389,
    ldap_ssl: data.ldap_ssl ?? false,
    ldap_base_dn: data.ldap_base_dn ?? '',
    ldap_user: data.ldap_user ?? '',
    ldap_user_attr: data.ldap_user_attr ?? 'sAMAccountName',
    ldap_group_admin: data.ldap_group_admin ?? '',
    ldap_group_user: data.ldap_group_user ?? '',
  };

  async function save() {
    setState({ ...state, saving: true, saved: false, error: null });
    try {
      await api.saveAuthConfig({ ...value, ...(password ? { ldap_pass: password } : {}) });
      setPassword('');
      setState({ saving: false, saved: true, error: null, probe: null });
      reload();
    } catch (err) {
      setState({
        saving: false, saved: false, probe: null,
        error: err instanceof Error ? err.message : 'No se pudo guardar',
      });
    }
  }

  async function probe() {
    setState({ ...state, probe: null, error: null });
    try {
      // Prueba los valores del formulario, así se valida antes de guardar.
      const result = await api.testAuthConfig({
        ...value, ...(password ? { ldap_pass: password } : {}),
      });
      setState({ ...state, probe: result.message ?? 'Conexión correcta.', error: null });
    } catch (err) {
      setState({
        ...state, probe: null,
        error: err instanceof Error ? err.message : 'No se pudo conectar',
      });
    }
  }

  return (
    <Card className="space-y-4">
      {state.error ? <ErrorNote message={state.error} /> : null}

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Servidor">
          <TextInput
            value={String(value.ldap_host ?? '')}
            onChange={(e) => setForm({ ...value, ldap_host: e.target.value })}
          />
        </Field>
        <Field label="Puerto">
          <TextInput
            type="number" value={String(value.ldap_port)}
            onChange={(e) => setForm({ ...value, ldap_port: Number(e.target.value) })}
          />
        </Field>
      </div>

      <Checkbox
        label="Usar SSL"
        checked={Boolean(value.ldap_ssl)}
        onChange={(e) => setForm({ ...value, ldap_ssl: e.target.checked })}
      />

      <Field label="Base DN">
        <TextInput
          value={String(value.ldap_base_dn ?? '')}
          onChange={(e) => setForm({ ...value, ldap_base_dn: e.target.value })}
          placeholder="dc=empresa,dc=com"
        />
      </Field>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Usuario de enlace">
          <TextInput
            value={String(value.ldap_user ?? '')}
            onChange={(e) => setForm({ ...value, ldap_user: e.target.value })}
          />
        </Field>
        <Field label="Contraseña" hint="Vacío conserva la actual.">
          <TextInput
            type="password" value={password} autoComplete="new-password"
            onChange={(e) => setPassword(e.target.value)}
          />
        </Field>
      </div>

      <Field label="Atributo de usuario">
        <TextInput
          value={String(value.ldap_user_attr ?? '')}
          onChange={(e) => setForm({ ...value, ldap_user_attr: e.target.value })}
        />
      </Field>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Grupo de administradores">
          <TextInput
            value={String(value.ldap_group_admin ?? '')}
            onChange={(e) => setForm({ ...value, ldap_group_admin: e.target.value })}
          />
        </Field>
        <Field label="Grupo de usuarios">
          <TextInput
            value={String(value.ldap_group_user ?? '')}
            onChange={(e) => setForm({ ...value, ldap_group_user: e.target.value })}
          />
        </Field>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <Button onClick={save} disabled={state.saving}>
          {state.saving ? 'Guardando…' : 'Guardar'}
        </Button>
        <Button variant="secondary" onClick={probe}>
          Probar conexión
        </Button>
        <Saved show={state.saved} />
      </div>

      {state.probe ? (
        <p className="text-sm text-emerald-600 dark:text-emerald-300">{state.probe}</p>
      ) : null}
    </Card>
  );
}

/** Preferencias propias, disponibles para cualquier usuario. */
function PreferencesTab() {
  const { session } = useSession();
  const [prefs, setPrefs] = useState(session?.preferences ?? null);
  const [state, setState] = useState<{ saving: boolean; saved: boolean; error: string | null }>(
    { saving: false, saved: false, error: null },
  );

  if (!prefs) return null;

  async function save() {
    setState({ saving: true, saved: false, error: null });
    try {
      const result = await api.savePreferences(prefs!);
      setPrefs(result.preferences);
      setState({ saving: false, saved: true, error: null });
    } catch (err) {
      setState({
        saving: false, saved: false,
        error: err instanceof Error ? err.message : 'No se pudo guardar',
      });
    }
  }

  return (
    <Card className="space-y-4">
      {state.error ? <ErrorNote message={state.error} /> : null}

      <Checkbox
        label="Recibir notificaciones en la aplicación"
        checked={prefs.notifications}
        onChange={(e) => setPrefs({ ...prefs, notifications: e.target.checked })}
      />
      <Checkbox
        label="Recibir notificaciones por correo"
        checked={prefs.email_notifications}
        onChange={(e) => setPrefs({ ...prefs, email_notifications: e.target.checked })}
      />
      <Checkbox
        label="Mostrar los tours de ayuda"
        checked={prefs.tour_enabled}
        onChange={(e) => setPrefs({ ...prefs, tour_enabled: e.target.checked })}
      />

      <Field label="Intervalo de refresco (segundos)" hint="Entre 15 y 3600.">
        <TextInput
          type="number" min={15} max={3600}
          value={String(prefs.refresh_interval)}
          onChange={(e) =>
            setPrefs({ ...prefs, refresh_interval: Number(e.target.value) })
          }
        />
      </Field>

      <div className="flex items-center gap-3">
        <Button onClick={save} disabled={state.saving}>
          {state.saving ? 'Guardando…' : 'Guardar'}
        </Button>
        <Saved show={state.saved} />
      </div>
    </Card>
  );
}

export function SettingsPanel() {
  const { session } = useSession();
  const isAdmin = session?.permissions.is_admin ?? false;
  const [tab, setTab] = useState<Tab>(isAdmin ? 'portal' : 'preferences');

  // La configuración del sistema es solo del superadmin; las preferencias, de
  // cada usuario.
  const tabs: { id: Tab; label: string }[] = [
    ...(isAdmin
      ? ([
          { id: 'portal', label: 'Portal' },
          { id: 'smtp', label: 'Correo' },
          { id: 'templates', label: 'Plantillas' },
          { id: 'ldap', label: 'Directorio' },
          { id: 'backup', label: 'Respaldo' },
        ] as { id: Tab; label: string }[])
      : []),
    { id: 'preferences', label: 'Mis preferencias' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Ajustes</h1>
        <p className="mt-1 text-sm text-label">
          {isAdmin
            ? 'Configuración del sistema y preferencias personales.'
            : 'Tus preferencias personales.'}
        </p>
      </div>

      <div className="flex flex-wrap gap-1 border-b border-panel-border" role="tablist">
        {tabs.map((item) => (
          <button
            key={item.id}
            type="button"
            role="tab"
            aria-selected={tab === item.id}
            onClick={() => setTab(item.id)}
            className={`-mb-px border-b-2 px-3 py-2 text-sm transition-colors ${
              tab === item.id
                ? 'border-primary font-medium text-primary-text'
                : 'border-transparent text-label hover:text-body-text'
            }`}
          >
            {item.label}
          </button>
        ))}
      </div>

      {tab === 'portal' ? <PortalTab /> : null}
      {tab === 'smtp' ? <SmtpTab /> : null}
      {tab === 'templates' ? <TemplatesTab /> : null}
      {tab === 'ldap' ? <LdapTab /> : null}
      {tab === 'backup' ? <BackupTab /> : null}
      {tab === 'preferences' ? <PreferencesTab /> : null}
    </div>
  );
}
