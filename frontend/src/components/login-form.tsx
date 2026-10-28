'use client';

/**
 * Pantalla de acceso.
 *
 * La sesión la sigue emitiendo Flask: aquí solo se recogen las credenciales y
 * se llama a /api/v1/auth. Con SSO activo, Authelia ya ha identificado al
 * visitante mediante cabeceras y basta confirmar la entrada.
 */

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { AuthContext } from '@/lib/types';
import { Button, Checkbox, Field, TextInput } from './form';
import { PageHeader } from './page-header';
import { Card, ErrorNote, Spinner } from './ui';

export function LoginForm() {
  const [context, setContext] = useState<AuthContext | null>(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [useDirectory, setUseDirectory] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    api.authContext()
      .then((result) => {
        if (!active) return;
        setContext(result);
        // Con sesión válida no hay nada que pedir.
        if (result.authenticated) window.location.href = '/';
      })
      .catch(() => {
        if (active) setContext({
          sso_enabled: false, sso_user: null,
          authenticated: false, ldap_available: true,
        });
      });
    return () => { active = false; };
  }, []);

  async function submit(event?: React.FormEvent) {
    event?.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.login(email, password, useDirectory ? 'directory' : 'local');
      window.location.href = '/';
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo iniciar sesión');
    } finally {
      setBusy(false);
    }
  }

  async function enterWithSso() {
    setBusy(true);
    setError(null);
    try {
      await api.ssoLogin();
      window.location.href = '/';
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo validar el acceso');
    } finally {
      setBusy(false);
    }
  }

  if (!context) {
    return (
      <div className="grid min-h-screen place-items-center">
        <Spinner label="Comprobando acceso…" />
      </div>
    );
  }

  return (
    <div className="grid min-h-screen place-items-center p-4">
      <div className="w-full max-w-sm">
        <PageHeader
          title="Nexus"
          description="Catálogo centralizado de plataformas"
          className="mb-6 text-center sm:flex-col sm:items-center"
        />

        <Card className="space-y-4">
          {error ? <ErrorNote message={error} /> : null}

          {context.sso_user ? (
            <div className="space-y-3">
              <p className="text-sm">
                Identificado como{' '}
                <strong className="font-medium">{context.sso_user}</strong> en el
                portal corporativo.
              </p>
              <Button
                onClick={enterWithSso}
                disabled={busy}
                className="w-full py-2"
              >
                {busy ? 'Entrando…' : 'Entrar'}
              </Button>
            </div>
          ) : (
            <form onSubmit={submit} className="space-y-4">
              <Field label="Usuario">
                <TextInput
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="username"
                  autoFocus
                  required
                />
              </Field>

              <Field label="Contraseña">
                <TextInput
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                />
              </Field>

              <Checkbox
                label="Usar directorio corporativo"
                checked={useDirectory}
                onChange={(e) => setUseDirectory(e.target.checked)}
              />

              <Button
                type="submit"
                disabled={busy || !email || !password}
                className="w-full py-2"
              >
                {busy ? 'Comprobando…' : 'Iniciar sesión'}
              </Button>
            </form>
          )}

          {context.sso_enabled && !context.sso_user ? (
            <p className="border-t border-panel-border pt-3 text-xs text-label">
              El acceso único está activo pero el portal no ha enviado tu
              identidad. Usa tus credenciales o accede desde el portal
              corporativo.
            </p>
          ) : null}
        </Card>
      </div>
    </div>
  );
}
