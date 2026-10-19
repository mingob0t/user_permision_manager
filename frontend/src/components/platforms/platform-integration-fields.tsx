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
import { describedBy, FieldErrorNote, FieldHint } from './field-notes';

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

/** Ids de los controles (un solo formulario montado a la vez). */
export const INTEGRATION_IDS = {
  integration_type: 'platform-integration-type',
  ldap_group_user_dn: 'platform-dn-user',
  ldap_group_admin_dn: 'platform-dn-admin',
} as const;
/** Nota "con accesos vigentes": también la describe el campo Área. */
export const LOCKED_NOTE_ID = 'platform-locked-note';

export function etiquetaTipo(tipo: IntegrationType | '' | undefined | null): string {
  return TIPOS_INTEGRACION.find((t) => t.value === tipo)?.label ?? 'Sin dato';
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
  const ids = INTEGRATION_IDS;
  const nota: [string, unknown] = [LOCKED_NOTE_ID, locked];

  return (
    <section aria-labelledby="integracion-titulo" className="space-y-5 border-t border-panel-border pt-5">
      <h3
        id="integracion-titulo"
        className="text-xs font-black uppercase tracking-[0.15em] text-label"
      >
        Integración
      </h3>

      {locked ? (
        <p id={LOCKED_NOTE_ID} className="text-sm font-bold text-label">
          Tiene {activeGrants} {activeGrants === 1 ? 'acceso vigente' : 'accesos vigentes'}: no se
          puede cambiar el tipo, los grupos ni el área.
        </p>
      ) : null}

      {canChooseType ? (
        <div>
          <Field label="Tipo de integración">
            <Select
              id={ids.integration_type}
              value={value.integration_type}
              disabled={locked}
              {...describedBy([`${ids.integration_type}-error`, errors.integration_type],
                [`${ids.integration_type}-hint`, true], nota)}
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
          </Field>
          <FieldHint id={`${ids.integration_type}-hint`}>
            Cómo se da el acceso: con grupos del directorio (quien está en el grupo entra) o con un
            conector que crea la cuenta en la plataforma.
          </FieldHint>
          <FieldErrorNote id={`${ids.integration_type}-error`} message={errors.integration_type} />
        </div>
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
          <div>
            <Field label="Grupo de acceso: nivel usuario">
              <TextInput
                id={ids.ldap_group_user_dn}
                value={value.ldap_group_user_dn}
                disabled={locked}
                maxLength={LARGO_DN}
                autoComplete="off"
                spellCheck={false}
                {...describedBy([`${ids.ldap_group_user_dn}-error`, errors.ldap_group_user_dn],
                  [`${ids.ldap_group_user_dn}-hint`, true], nota)}
                onChange={(e) => onChange({ ldap_group_user_dn: e.target.value })}
                placeholder="cn=…,ou=plataformas,dc=…"
              />
            </Field>
            <FieldHint id={`${ids.ldap_group_user_dn}-hint`}>
              Quien esté en este grupo del directorio entra con nivel usuario. Escribe su DN, por
              ejemplo {EJEMPLO_DN}. {vacioDn}
            </FieldHint>
            <FieldErrorNote id={`${ids.ldap_group_user_dn}-error`} message={errors.ldap_group_user_dn} />
          </div>
          <div>
            <Field label="Grupo de acceso: nivel admin">
              <TextInput
                id={ids.ldap_group_admin_dn}
                value={value.ldap_group_admin_dn}
                disabled={locked}
                maxLength={LARGO_DN}
                autoComplete="off"
                spellCheck={false}
                {...describedBy([`${ids.ldap_group_admin_dn}-error`, errors.ldap_group_admin_dn],
                  [`${ids.ldap_group_admin_dn}-hint`, true], nota)}
                onChange={(e) => onChange({ ldap_group_admin_dn: e.target.value })}
                placeholder="cn=…,ou=plataformas,dc=…"
              />
            </Field>
            <FieldHint id={`${ids.ldap_group_admin_dn}-hint`}>
              Quien esté en este grupo entra con nivel admin. Debe ser distinto del de nivel
              usuario. {vacioDn}
            </FieldHint>
            <FieldErrorNote id={`${ids.ldap_group_admin_dn}-error`} message={errors.ldap_group_admin_dn} />
          </div>
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
