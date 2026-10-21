'use client';

/**
 * Formulario del conector de una plataforma (DIS-022, F-CON-01,
 * `PUT /platforms/<id>/connector`, contrato `conectores-y-ejecuciones.md` 1.1).
 *
 * - Tipo, host, puerto, parámetros del tipo, referencia de la credencial y
 *   activo. Los parámetros cambian con el tipo (`PARAMETROS_POR_TIPO`).
 * - Ningún campo pide ni muestra contraseñas: la credencial es la referencia
 *   del ítem en el gestor de secretos (ADR-005).
 * - Patrón de `DirectoryAccountForm` (DIS-019): `required` y `aria-required`,
 *   pistas y errores con `aria-describedby`, foco en el primer error y
 *   `aria-disabled` durante el envío para que el foco no caiga en `body`.
 */

import { useState } from 'react';
import { connectorsApi } from '@/lib/access/connectors';
import type { Connector } from '@/lib/access/types';
import { Button, Checkbox, Field, Select, TextInput } from '../form';
import { FieldErrorNote, FieldHint, describedBy, focusFirstError } from '../platforms/field-notes';
import { ErrorNote } from '../ui';
import {
  type CampoConector, type FormularioConector, HOST_MAX, PUERTO_MAX, PUERTO_MIN, REFERENCIA_MAX,
  TIPOS_CONECTOR, cuerpoConector, esTipoConocido, formularioDesde, parametrosConservados,
  parametrosDelTipo, validarConector,
} from './connector-catalog';
import { describeConnectorSaveError } from './connector-errors';

const PREFIJO = 'conector';
const IDS: Record<Exclude<CampoConector, 'params' | 'active'>, string> = {
  type: `${PREFIJO}-tipo`,
  host: `${PREFIJO}-host`,
  port: `${PREFIJO}-puerto`,
  credential_ref: `${PREFIJO}-credencial`,
};
const ORDEN: [CampoConector, string][] = [
  ['type', IDS.type], ['host', IDS.host], ['port', IDS.port], ['credential_ref', IDS.credential_ref],
];
const PARAMS_ERROR_ID = `${PREFIJO}-params-error`;

export function ConnectorForm({
  platformId,
  guardado,
  onSaved,
  onStale,
}: {
  platformId: number;
  /** Configuración guardada; `null` si la plataforma aún no tiene. */
  guardado: Connector | null;
  onSaved: (connector: Connector) => void;
  /** La plataforma o la configuración cambió en el servidor: recargar. */
  onStale: () => void;
}) {
  const [form, setForm] = useState<FormularioConector>(() => formularioDesde(guardado));
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fields, setFields] = useState<Partial<Record<CampoConector, string>>>({});

  const campos = parametrosDelTipo(form.type);
  const conservados = Object.keys(parametrosConservados(guardado, form.type));
  const tipoCambio = guardado !== null && guardado.type !== form.type;

  function cambiar<K extends keyof FormularioConector>(campo: K, valor: FormularioConector[K]) {
    setForm((prev) => ({ ...prev, [campo]: valor }));
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (sending) return;
    const errores = validarConector(form);
    if (Object.keys(errores).length > 0) {
      setError(null);
      setFields(errores);
      focusFirstError(ORDEN, errores as Record<string, string>);
      return;
    }
    setSending(true);
    setError(null);
    setFields({});
    try {
      const result = await connectorsApi.save(platformId, cuerpoConector(form, guardado));
      setSending(false);
      onSaved(result.connector);
    } catch (err) {
      const view = describeConnectorSaveError(err);
      setError(view.message);
      setFields(view.fields);
      setSending(false);
      if (view.stale) onStale();
      focusFirstError(ORDEN, view.fields as Record<string, string>);
    }
  }

  function campoTexto(
    campo: 'host' | 'port' | 'credential_ref',
    label: string,
    pista: string,
    extra: React.InputHTMLAttributes<HTMLInputElement> = {},
  ) {
    const pistaId = `${IDS[campo]}-pista`;
    const errorId = `${IDS[campo]}-error`;
    return (
      <div>
        <Field label={`${label} *`}>
          <TextInput
            id={IDS[campo]}
            value={form[campo]}
            onChange={(event) => cambiar(campo, event.target.value)}
            required
            aria-required="true"
            autoComplete="off"
            spellCheck={false}
            {...extra}
            {...describedBy([errorId, fields[campo]], [pistaId, true])}
          />
        </Field>
        <FieldHint id={pistaId}>{pista}</FieldHint>
        <div role="alert">
          <FieldErrorNote id={errorId} message={fields[campo]} />
        </div>
      </div>
    );
  }

  const tipoPista = `${IDS.type}-pista`;
  const tipoError = `${IDS.type}-error`;

  return (
    <form onSubmit={submit} noValidate aria-busy={sending} className="space-y-5" aria-label="Configuración del conector">
      <p className="text-sm text-label">Los campos con * son obligatorios.</p>

      <div className="grid gap-5 sm:grid-cols-2">
        <div>
          <Field label="Tipo de conector *">
            <Select
              id={IDS.type}
              value={form.type}
              onChange={(event) => cambiar('type', event.target.value)}
              required
              aria-required="true"
              {...describedBy([tipoError, fields.type], [tipoPista, true])}
            >
              {(Object.keys(TIPOS_CONECTOR) as (keyof typeof TIPOS_CONECTOR)[]).map((tipo) => (
                <option key={tipo} value={tipo}>{TIPOS_CONECTOR[tipo]}</option>
              ))}
              {/* Un tipo guardado sin editor aquí (p. ej. `noop` en dev) se conserva. */}
              {guardado && !esTipoConocido(guardado.type)
                ? <option value={guardado.type}>{guardado.type}</option> : null}
            </Select>
          </Field>
          <FieldHint id={tipoPista}>
            {tipoCambio
              ? 'Cambiaste el tipo: se descartan los parámetros del tipo anterior.'
              : 'Cómo se conecta el portal con la plataforma.'}
          </FieldHint>
          <div role="alert">
            <FieldErrorNote id={tipoError} message={fields.type} />
          </div>
        </div>
        {campoTexto('port', 'Puerto', `Número entre ${PUERTO_MIN} y ${PUERTO_MAX}.`, {
          inputMode: 'numeric', pattern: '[0-9]*',
        })}
      </div>

      {campoTexto('host', 'Host', 'Nombre de host autorizado por el despliegue, sin protocolo ni dirección IP.', {
        maxLength: HOST_MAX, autoCapitalize: 'none',
      })}

      {campoTexto('credential_ref', 'Referencia de la credencial',
        `Nombre del ítem en el gestor de secretos, por ejemplo equipo/plataforma-api. Hasta ${REFERENCIA_MAX} caracteres. Nunca escribas aquí la contraseña.`,
        { maxLength: REFERENCIA_MAX, autoCapitalize: 'none' })}

      <fieldset className="space-y-3" aria-describedby={fields.params ? PARAMS_ERROR_ID : undefined}>
        <legend className="mb-2 block text-xs font-black uppercase tracking-[0.1em] text-label">
          Parámetros del tipo
        </legend>
        {campos.length === 0 ? (
          <p className="text-sm text-label">Este tipo no tiene parámetros editables por ahora.</p>
        ) : campos.map((campo) => {
          const id = `${PREFIJO}-param-${campo.clave}`;
          const pistaId = `${id}-pista`;
          return (
            <div key={campo.clave}>
              <Field label={campo.etiqueta}>
                <TextInput
                  id={id}
                  value={form.params[campo.clave] ?? ''}
                  onChange={(event) => cambiar('params', { ...form.params, [campo.clave]: event.target.value })}
                  autoComplete="off"
                  spellCheck={false}
                  aria-describedby={pistaId}
                />
              </Field>
              <FieldHint id={pistaId}>{campo.pista}</FieldHint>
            </div>
          );
        })}
        {conservados.length > 0 ? (
          <p className="break-words text-sm text-label">
            Se conservan sin cambios: {conservados.join(', ')}.
          </p>
        ) : null}
        <div role="alert">
          <FieldErrorNote id={PARAMS_ERROR_ID} message={fields.params} />
        </div>
      </fieldset>

      <Checkbox
        label="Conector activo"
        checked={form.active}
        onChange={(event) => cambiar('active', event.target.checked)}
      />

      {error ? <ErrorNote message={error} /> : null}

      <div className="flex flex-wrap justify-end gap-3">
        <Button
          type="submit"
          aria-disabled={sending || undefined}
          className="aria-disabled:opacity-40 focus-visible:ring-2 focus-visible:ring-primary"
        >
          {sending ? 'Guardando…' : 'Guardar conector'}
        </Button>
      </div>
    </form>
  );
}
