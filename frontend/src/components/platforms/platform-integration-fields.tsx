'use client';

/**
 * Sección "Integración" del formulario de plataforma (DIS-017).
 *
 * Contrato `docs/contratos/plataformas-integracion.md`:
 * - `integration_type` obligatorio en el alta; en la edición solo lo cambia el
 *   superadmin.
 * - Los DN de grupo por nivel solo los ve y los envía el superadmin.
 * - Con accesos vigentes no se cambian el tipo ni los grupos (`409`).
 */

import Link from 'next/link';
import type { IntegrationType } from '@/lib/types';
import { Field, Select, TextInput } from '../form';
import { ErrorNote } from '../ui';

/** Valores de la sección; `''` = sin elegir (alta) o sin cambiar (edición). */
export interface IntegrationValue {
  integration_type: IntegrationType | '';
  ldap_group_user_dn: string;
  ldap_group_admin_dn: string;
}

export const TIPOS_INTEGRACION: { value: IntegrationType; label: string }[] = [
  { value: 'ldap', label: 'Grupos del directorio' },
  { value: 'conector', label: 'Conector' },
];

/** Ejemplo de formato del contrato (sin datos reales). */
const EJEMPLO_DN = 'cn=contabilidad-usuario,ou=finanzas,ou=plataformas,dc=ejemplo,dc=local';
const RUTA_CONECTORES = '/admin/connectors';
/** Largo máximo de un DN (columna del backend, `LARGO_DN`). */
const LARGO_DN = 512;

export function etiquetaTipo(tipo: IntegrationType | '' | undefined | null): string {
  return TIPOS_INTEGRACION.find((t) => t.value === tipo)?.label ?? 'Sin dato';
}

function FieldErrorNote({ message }: { message?: string }) {
  return message ? <ErrorNote message={message} /> : null;
}

export function PlatformIntegrationFields({
  value,
  onChange,
  isSuperadmin,
  isEdit,
  currentType,
  activeGrants,
  errors,
}: {
  value: IntegrationValue;
  onChange: (patch: Partial<IntegrationValue>) => void;
  isSuperadmin: boolean;
  isEdit: boolean;
  /** Tipo guardado, si la respuesta lo trae (`GET /platforms` aún no lo expone). */
  currentType?: IntegrationType | null;
  /** Accesos vigentes, si se conocen. */
  activeGrants?: number;
  errors: Record<string, string>;
}) {
  const locked = isEdit && (activeGrants ?? 0) > 0;
  const canChooseType = !isEdit || isSuperadmin;
  const tipo = value.integration_type || currentType || '';
  const vacioDn = isEdit
    ? 'Vacío: se conserva el grupo actual.'
    : 'Vacío: se genera con la convención del directorio.';

  return (
    <section aria-labelledby="integracion-titulo" className="space-y-5 border-t border-panel-border pt-5">
      <h3
        id="integracion-titulo"
        className="text-xs font-black uppercase tracking-[0.15em] text-label"
      >
        Integración
      </h3>

      {locked ? (
        <p className="text-sm font-bold text-label" role="note">
          Tiene {activeGrants} {activeGrants === 1 ? 'acceso vigente' : 'accesos vigentes'}: no se
          puede cambiar el tipo, los grupos ni el área.
        </p>
      ) : null}

      {canChooseType ? (
        <Field
          label="Tipo de integración"
          hint="Cómo se da el acceso: con grupos del directorio (quien está en el grupo entra) o con un conector que crea la cuenta en la plataforma."
        >
          <Select
            value={value.integration_type}
            disabled={locked}
            aria-invalid={errors.integration_type ? true : undefined}
            onChange={(e) =>
              onChange({ integration_type: e.target.value as IntegrationType | '' })}
          >
            <option value="">
              {isEdit ? `Sin cambiar (${etiquetaTipo(currentType)})` : 'Selecciona un tipo'}
            </option>
            {TIPOS_INTEGRACION.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </Select>
          <FieldErrorNote message={errors.integration_type} />
        </Field>
      ) : (
        <div>
          <p className="text-sm font-bold text-body-text">
            Tipo de integración: {etiquetaTipo(currentType)}
          </p>
          <p className="mt-1.5 text-xs text-label">
            Solo el superadmin cambia el tipo de integración.
          </p>
        </div>
      )}

      {tipo === 'ldap' && isSuperadmin ? (
        <>
          <Field
            label="Grupo de acceso: nivel usuario"
            hint={`Quien esté en este grupo del directorio entra con nivel usuario. Escribe su DN, por ejemplo ${EJEMPLO_DN}. ${vacioDn}`}
          >
            <TextInput
              value={value.ldap_group_user_dn}
              disabled={locked}
              maxLength={LARGO_DN}
              autoComplete="off"
              spellCheck={false}
              aria-invalid={errors.ldap_group_user_dn ? true : undefined}
              onChange={(e) => onChange({ ldap_group_user_dn: e.target.value })}
              placeholder="cn=…,ou=plataformas,dc=…"
            />
            <FieldErrorNote message={errors.ldap_group_user_dn} />
          </Field>
          <Field
            label="Grupo de acceso: nivel admin"
            hint={`Quien esté en este grupo entra con nivel admin. Debe ser distinto del de nivel usuario. ${vacioDn}`}
          >
            <TextInput
              value={value.ldap_group_admin_dn}
              disabled={locked}
              maxLength={LARGO_DN}
              autoComplete="off"
              spellCheck={false}
              aria-invalid={errors.ldap_group_admin_dn ? true : undefined}
              onChange={(e) => onChange({ ldap_group_admin_dn: e.target.value })}
              placeholder="cn=…,ou=plataformas,dc=…"
            />
            <FieldErrorNote message={errors.ldap_group_admin_dn} />
          </Field>
        </>
      ) : null}

      {tipo === 'ldap' && !isSuperadmin ? (
        <p className="text-xs text-label">
          Los grupos de acceso se generan con la convención del directorio. Solo el superadmin
          puede definirlos.
        </p>
      ) : null}

      {tipo === 'conector' ? (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-xs text-label">
            El acceso lo da un conector, que se configura aparte.
          </p>
          {isSuperadmin ? (
            <Link href={RUTA_CONECTORES} className="nexus-btn nexus-btn-secondary">
              Configurar conectores
            </Link>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
