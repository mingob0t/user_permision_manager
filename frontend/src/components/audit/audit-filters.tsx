'use client';

/**
 * Filtros de la auditoría (DIS-020; contrato `auditoria.md`, "Parámetros"):
 * búsqueda en actor y destino, fechas, evento, resultado y, para quien
 * administra, área y plataforma.
 *
 * - Los selectores aplican al cambiar; la búsqueda, al enviar (Enter o "Buscar").
 * - Las fechas aplican solo si el rango es válido (`from ≤ to`, ≤ 366 días);
 *   si no, se explica junto a los campos y no se pide nada al servidor (400).
 * - La búsqueda se limpia con `limpiarBusqueda` (sin caracteres de control, ≤ 100).
 */

import { useState } from 'react';
import type { AuditParams, AuditResult } from '@/lib/access/types';
import { BUSQUEDA_MAX, limpiarBusqueda } from '../access/inventory-filters';
import { type OpcionesAlcance, ScopeSelects } from '../access/scope-filters';
import { FilterBar, FilterBarError, FilterBarGrid, FilterBarSearch } from '../filter-bar';
import { Field, Select, TextInput } from '../form';
import { ACCIONES, RESULTADOS } from './audit-actions';

export interface FiltrosAuditoria {
  q: string;
  /** Fechas `AAAA-MM-DD` del campo de fecha; '' = sin límite. */
  from: string;
  to: string;
  action: string | null;
  result: AuditResult | null;
  areaId: number | null;
  platformId: number | null;
}

export const FILTROS_INICIALES: FiltrosAuditoria = {
  q: '',
  from: '',
  to: '',
  action: null,
  result: null,
  areaId: null,
  platformId: null,
};

/** Rango máximo de fechas (contrato: ≤ 366 días; `RANGO_MAX_DIAS` del backend). */
export const RANGO_MAX_DIAS = 366;

const MS_POR_DIA = 24 * 60 * 60 * 1000;

export const MENSAJE_FECHAS_INVERTIDAS = 'La fecha inicial debe ser anterior o igual a la final.';
export const MENSAJE_RANGO_LARGO = `El rango máximo es de ${RANGO_MAX_DIAS} días.`;

/** Error del rango de fechas, o `null` si es válido (o incompleto). */
export function validarFechas(from: string, to: string): string | null {
  if (!from || !to) return null;
  const inicio = Date.parse(`${from}T00:00:00Z`);
  const fin = Date.parse(`${to}T00:00:00Z`);
  if (Number.isNaN(inicio) || Number.isNaN(fin)) return null;
  if (inicio > fin) return MENSAJE_FECHAS_INVERTIDAS;
  if ((fin - inicio) / MS_POR_DIA > RANGO_MAX_DIAS) return MENSAJE_RANGO_LARGO;
  return null;
}

/** ¿Hay algún filtro distinto del inicial? */
export function hayFiltros(filtros: FiltrosAuditoria): boolean {
  return (Object.keys(FILTROS_INICIALES) as (keyof FiltrosAuditoria)[])
    .some((clave) => filtros[clave] !== FILTROS_INICIALES[clave]);
}

/** Filtros de la pantalla → parámetros del contrato (sin los vacíos). */
export function aParametros(filtros: FiltrosAuditoria, page: number): AuditParams {
  return {
    q: filtros.q || undefined,
    from: filtros.from || undefined,
    to: filtros.to || undefined,
    action: filtros.action ?? undefined,
    result: filtros.result ?? undefined,
    area_id: filtros.areaId ?? undefined,
    platform_id: filtros.platformId ?? undefined,
    page,
  };
}

const ID_ERROR_FECHAS = 'auditoria-error-fechas';

export function AuditFilters({
  filtros,
  opciones,
  conAlcance,
  onChange,
}: {
  filtros: FiltrosAuditoria;
  opciones: OpcionesAlcance;
  /** Área y plataforma: solo para quien administra (y no en el historial de una plataforma). */
  conAlcance: boolean;
  onChange: (cambio: Partial<FiltrosAuditoria>) => void;
}) {
  const [borrador, setBorrador] = useState(filtros.q);
  const [fechas, setFechas] = useState({ from: filtros.from, to: filtros.to });
  const errorFechas = validarFechas(fechas.from, fechas.to);

  function buscar(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const q = limpiarBusqueda(borrador);
    setBorrador(q);
    onChange({ q });
  }

  function cambiarFecha(campo: 'from' | 'to', valor: string) {
    const siguientes = { ...fechas, [campo]: valor };
    setFechas(siguientes);
    if (!validarFechas(siguientes.from, siguientes.to)) onChange(siguientes);
  }

  const describe = errorFechas ? ID_ERROR_FECHAS : undefined;

  return (
    <FilterBar label="Filtros de la auditoría" layout="stack">
      <FilterBarSearch onSubmit={buscar}>
        <TextInput
          type="search"
          value={borrador}
          maxLength={BUSQUEDA_MAX}
          onChange={(event) => setBorrador(event.target.value)}
          placeholder="Quién actuó o sobre qué…"
          aria-label="Buscar en la auditoría por quién actuó o sobre qué"
        />
      </FilterBarSearch>

      <FilterBarGrid>
        <Field label="Desde">
          <TextInput
            type="date"
            value={fechas.from}
            max={fechas.to || undefined}
            aria-invalid={errorFechas ? true : undefined}
            aria-describedby={describe}
            onChange={(event) => cambiarFecha('from', event.target.value)}
          />
        </Field>
        <Field label="Hasta">
          <TextInput
            type="date"
            value={fechas.to}
            min={fechas.from || undefined}
            aria-invalid={errorFechas ? true : undefined}
            aria-describedby={describe}
            onChange={(event) => cambiarFecha('to', event.target.value)}
          />
        </Field>
        <Field label="Evento">
          <Select
            value={filtros.action ?? ''}
            onChange={(event) => onChange({ action: event.target.value || null })}
          >
            <option value="">Todos los eventos</option>
            {Object.entries(ACCIONES).map(([valor, texto]) => (
              <option key={valor} value={valor}>{texto}</option>
            ))}
          </Select>
        </Field>
        <Field label="Resultado">
          <Select
            value={filtros.result ?? ''}
            onChange={(event) =>
              onChange({ result: (event.target.value || null) as AuditResult | null })}
          >
            <option value="">Todos los resultados</option>
            {(Object.keys(RESULTADOS) as AuditResult[]).map((valor) => (
              <option key={valor} value={valor}>{RESULTADOS[valor].texto}</option>
            ))}
          </Select>
        </Field>
        {conAlcance ? (
          <ScopeSelects
            areaId={filtros.areaId}
            platformId={filtros.platformId}
            opciones={opciones}
            onChange={onChange}
          />
        ) : null}
      </FilterBarGrid>

      <FilterBarError id={ID_ERROR_FECHAS} message={errorFechas} />
    </FilterBar>
  );
}
