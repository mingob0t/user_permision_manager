import { AppShell } from '@/components/app-shell';
import { idDeRuta } from '@/components/audit/audit-routes';
import { UserAuditHistory } from '@/components/audit/user-audit-history';
import { ErrorNote } from '@/components/ui';

/** Historial de un usuario (DIS-020). El alcance lo decide el backend. */
export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const userId = idDeRuta((await params).id);
  return (
    <AppShell>
      {userId === null
        ? <ErrorNote message="El usuario indicado no es válido." />
        : <UserAuditHistory userId={userId} />}
    </AppShell>
  );
}
