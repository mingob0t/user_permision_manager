'use client';

/**
 * Lista de áreas con casillas (DIS-019): alta en el directorio y áreas que
 * administra un admin de área. `fieldset` con `legend` visible (mismo estilo
 * que la etiqueta de `Field`), pista y error ligados con `aria-describedby`,
 * filas de 48 px y foco visible en la fila (`.nexus-checkbox` solo trae un
 * halo tenue y `Checkbox` no acepta clases).
 *
 * Estados: carga, error y vacío. No llama a la API: recibe las áreas.
 */

import type { AreaRef } from '@/lib/types';
import { Checkbox } from '../form';
import { FieldErrorNote, FieldHint, describedBy } from '../platforms/field-notes';
import { ErrorNote, Spinner } from '../ui';

export function AreaChecklist({
  id,
  legend,
  hint,
  areas,
  selected,
  onChange,
  error,
  loading = false,
  loadError = null,
  empty,
}: {
  /** Prefijo de los ids de la pista, el error y cada casilla. */
  id: string;
  legend: string;
  hint?: string;
  areas: AreaRef[];
  selected: number[];
  onChange: (ids: number[]) => void;
  error?: string;
  loading?: boolean;
  loadError?: string | null;
  empty: string;
}) {
  const hintId = `${id}-pista`;
  const errorId = `${id}-error`;

  function alternar(areaId: number, marcado: boolean) {
    onChange(marcado ? [...selected, areaId] : selected.filter((x) => x !== areaId));
  }

  return (
    <fieldset {...describedBy([errorId, error], [hintId, hint])}>
      <legend className="mb-2 block text-xs font-black uppercase tracking-[0.1em] text-label">
        {legend}
      </legend>
      {loading ? <Spinner /> : null}
      {loadError ? <ErrorNote message={loadError} /> : null}
      {!loading && !loadError && areas.length === 0 ? (
        <p className="text-sm text-label">{empty}</p>
      ) : null}
      {!loading && !loadError && areas.length > 0 ? (
        <ul className="grid gap-1 sm:grid-cols-2">
          {areas.map((area) => (
            <li
              key={area.id}
              className="flex min-h-12 items-center rounded-lg px-2 has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-primary"
            >
              <Checkbox
                id={`${id}-${area.id}`}
                label={area.name}
                checked={selected.includes(area.id)}
                onChange={(event) => alternar(area.id, event.target.checked)}
              />
            </li>
          ))}
        </ul>
      ) : null}
      {hint ? <FieldHint id={hintId}>{hint}</FieldHint> : null}
      <div role="alert">
        <FieldErrorNote id={errorId} message={error} />
      </div>
    </fieldset>
  );
}
