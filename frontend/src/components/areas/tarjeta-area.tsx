'use client';

/**
 * Tarjeta de área del catálogo de administración (DIS-102).
 *
 * Encabezado: icono del área (degradado de su color) + nombre y descripción. Cuerpo: dos
 * recuadros con los usuarios y las plataformas del área. Pie: logos de las primeras 3
 * plataformas, «+N» y «Ver plataformas». Ocupa toda la celda de la rejilla: el cuerpo se
 * reparte el alto sobrante (las cifras quedan centradas, sin hueco vacío). El color del área es un dato: viaja como `--area-color` y `.nx-area-card*`
 * (components.css) lo consume; el texto sale de tokens.
 */

import Link from 'next/link';
import type { ReactNode } from 'react';
import { atributoTexto, textoLegible, variablesChipPlataforma } from '@/lib/color-legible';
import { enlaceSeguro } from '@/lib/enlace-seguro';
import type { Area, Platform } from '@/lib/types';
import { variablesCss } from '@/lib/variables-css';
import { obtenerImagenFondoArea } from '@/lib/card-backgrounds';
import { Icono, type NombreIcono } from '../icono';
import { EstadoBadgeBoton } from '../estado-badge-boton';
import { rutaConFiltro } from '../access/filtro-url';

/** Ruta de Solicitudes (`RUTA_SOLICITUDES` de approvals-resumen; aquí sin importar sus gráficas). */
const RUTA_SOLICITUDES = '/approvals';

/** Historial de solicitudes filtrado por pendientes del área (DIS-137, DIS-162). */
export function rutaPendientesArea(areaId: number): string {
  return rutaConFiltro(RUTA_SOLICITUDES, { status: 'pendiente', area_id: String(areaId) });
}

/** Logos que se muestran en el pie; el resto va como «+N». */
export const LOGOS_VISIBLES = 3;

/** El backend solo devuelve `logo_url` `https://` (url_segura); aquí se repite la defensa (SEG-24). */
const logoSeguro = enlaceSeguro;

function LogoPlataforma({ plataforma }: { plataforma: Platform }) {
  const logo = logoSeguro(plataforma.logo_url);
  const base =
    'grid size-8 shrink-0 place-items-center overflow-hidden rounded-lg border-2 border-panel-fill text-xs font-bold shadow-1 -ml-2 first:ml-0';
  if (logo) {
    return (
      <span className={`${base} bg-superficie-hundida`} title={plataforma.name}>
        {/* logo externo https: next/image no lo optimiza (mismo motivo que portal-tab.tsx) */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={logo} alt="" className="size-full object-contain" />
      </span>
    );
  }
  return (
    <span
      className={`${base} nx-chip-solid`}
      data-texto={atributoTexto(plataforma.bg_color)}
      style={variablesCss(variablesChipPlataforma(plataforma.bg_color))}
      title={plataforma.name}
    >
      {plataforma.name.slice(0, 2).toUpperCase()}
    </span>
  );
}

/** Nombre accesible del enlace a las solicitudes pendientes del área (DIS-162, DIS-164). */
function nombrePendientes(area: Area, pendientes: number): string {
  return `${pendientes} ${pendientes === 1 ? 'solicitud pendiente' : 'solicitudes pendientes'} en ${area.name}. Abrir Historial.`;
}

/** Texto de los administradores del área (DIS-162): nombres separados por coma o «Sin administrador». */
function textoAdministradores(area: Area): string {
  const nombres = (area.admins ?? []).map((admin) => admin.name);
  return nombres.length > 0 ? nombres.join(', ') : 'Sin administrador';
}

/**
 * Enlace al Historial con las pendientes del área, común a todas las variantes (DIS-164).
 * Detiene el clic para que la tarjeta (que abre las plataformas) no lo reciba.
 */
function EnlacePendientes({ area, pendientes, className, children }: { area: Area; pendientes: number; className: string; children: ReactNode }) {
  return (
    <Link
      href={rutaPendientesArea(area.id)}
      onClick={(evento) => evento.stopPropagation()}
      aria-label={nombrePendientes(area, pendientes)}
      title="Ver solicitudes pendientes"
      className={`${className} foco-visible min-h-12 min-w-12`}
    >
      {children}
    </Link>
  );
}

function Cifra({
  icono,
  valor,
  etiqueta,
  compacta = false,
  enlace,
}: {
  icono: NombreIcono;
  valor: number;
  etiqueta: string;
  compacta?: boolean;
  /** Si viene, la cifra es un enlace (DIS-162): detiene el clic para no abrir las plataformas. */
  enlace?: { area: Area; pendientes: number };
}) {
  const clases = `nx-area-card__cifra flex min-w-0 items-center ${compacta ? 'gap-2 rounded-lg p-2' : 'gap-3 rounded-xl p-3'} border`;
  const contenido = (
    <>
      <span className={`nx-area-card__mini grid ${compacta ? 'size-6 rounded-md' : 'size-8 rounded-lg'} shrink-0 place-items-center`} aria-hidden="true">
        <Icono nombre={icono} tamano={compacta ? 'xs' : 'sm'} />
      </span>
      <div className="min-w-0">
        <p className={`nx-area-card__valor ${compacta ? 'text-base' : 'text-xl'} font-extrabold leading-none tabular-nums`}>{valor}</p>
        <p className="mt-0.5 truncate text-xs font-semibold uppercase tracking-wide text-label" title={etiqueta}>{etiqueta}</p>
      </div>
    </>
  );
  if (!enlace) return <div className={clases}>{contenido}</div>;
  return (
    <EnlacePendientes area={enlace.area} pendientes={enlace.pendientes} className={clases}>
      {contenido}
    </EnlacePendientes>
  );
}

/**
 * Fila de ancho completo con los administradores del área (DIS-162). El recuadro es el de
 * `Cifra`; los nombres se truncan y el texto completo va en `title`.
 */
function AdministradoresArea({ area, compacta }: { area: Area; compacta: boolean }) {
  const texto = textoAdministradores(area);
  return (
    <div className={`nx-area-card__cifra col-span-full flex min-w-0 items-center ${compacta ? 'gap-2 rounded-lg p-2' : 'gap-3 rounded-xl p-3'} border`}>
      <span className={`nx-area-card__mini grid ${compacta ? 'size-6 rounded-md' : 'size-8 rounded-lg'} shrink-0 place-items-center`} aria-hidden="true">
        <Icono nombre="escudo" tamano={compacta ? 'xs' : 'sm'} />
      </span>
      <div className="min-w-0">
        <p className="truncate text-xs font-semibold uppercase tracking-wide text-label">Administradores de área</p>
        <p className="mt-0.5 truncate text-sm font-semibold text-body-text" title={texto}>{texto}</p>
      </div>
    </div>
  );
}

/** Clases de los recuadros de «Solicitudes pendientes» y «Administradores» según el estilo de cifra de cada variante (DIS-164). */
interface EstiloKpi { caja: string; mini: string; valor: string; etiqueta: string; texto: string }

function estiloKpi(tipo: 'glass' | 'oscuro' | 'claro', alturaEstandar: boolean): EstiloKpi {
  const valor = `${alturaEstandar ? 'text-xs' : 'text-sm'} font-black leading-none tabular-nums`;
  const etiqueta = 'mt-0.5 truncate text-xs font-bold uppercase tracking-wider';
  const base = `flex min-w-0 items-center gap-2 rounded-xl border ${alturaEstandar ? 'p-1.5' : 'p-2'}`;
  if (tipo === 'glass') {
    return { caja: `${base} bg-superficie/60 backdrop-blur-md border-primary/20`, mini: 'bg-primary/20 text-primary-text', valor: `${valor} text-body-text`, etiqueta: `${etiqueta} text-label`, texto: 'text-body-text' };
  }
  if (tipo === 'oscuro') {
    return { caja: `${base} bg-arte-luz/10 backdrop-blur-md border-arte-luz/15 text-arte-luz`, mini: 'bg-arte-luz/15 text-arte-luz', valor: `${valor} text-arte-luz`, etiqueta: `${etiqueta} text-arte-pizarra-300`, texto: 'text-arte-luz' };
  }
  return { caja: `${base} bg-superficie-hundida/70 border-panel-border/80`, mini: 'bg-superficie text-primary-text shadow-xs', valor: `${valor} text-body-text`, etiqueta: `${etiqueta} text-label`, texto: 'text-body-text' };
}

/** Cifra «Solicitudes pendientes» con el estilo de la variante (DIS-164). Sin dato no se pinta. */
function KpiPendientes({ area, pendientes, estilo }: { area: Area; pendientes?: number; estilo: EstiloKpi }) {
  if (pendientes === undefined) return null;
  return (
    <EnlacePendientes area={area} pendientes={pendientes} className={estilo.caja}>
      <span className={`grid size-6 shrink-0 place-items-center rounded-lg ${estilo.mini}`} aria-hidden="true">
        <Icono nombre="reloj" tamano="xs" />
      </span>
      <div className="min-w-0">
        <p className={estilo.valor}>{pendientes}</p>
        <p className={estilo.etiqueta} title="Solicitudes pendientes">Solicitudes pendientes</p>
      </div>
    </EnlacePendientes>
  );
}

/** Fila de ancho completo con los administradores, con el estilo de la variante (DIS-164). */
function FilaAdministradores({ area, estilo, mostrar }: { area: Area; estilo: EstiloKpi; mostrar: boolean }) {
  if (!mostrar) return null;
  const texto = textoAdministradores(area);
  return (
    <div className={`col-span-full ${estilo.caja}`}>
      <span className={`grid size-6 shrink-0 place-items-center rounded-lg ${estilo.mini}`} aria-hidden="true">
        <Icono nombre="escudo" tamano="xs" />
      </span>
      <div className="min-w-0">
        <p className={estilo.etiqueta}>Administradores de área</p>
        <p className={`mt-0.5 truncate text-sm font-semibold ${estilo.texto}`} title={texto}>{texto}</p>
      </div>
    </div>
  );
}

export function TarjetaArea({
  area,
  conteo,
  plataformas,
  pendientes,
  mostrarAdministradores = false,
  onSelect,
  puedeEditar = false,
  actualizarEstado,
  onEstadoCambiado,
  variante = 'estandar',
  alturaEstandar = false,
}: {
  area: Area;
  /** Plataformas del área dentro del alcance de quien mira (ya calculado por la pantalla). */
  conteo: number;
  /** Plataformas del área en el mismo alcance; de aquí salen los logos del pie. */
  plataformas: Platform[];
  /** Solicitudes pendientes del área (DIS-162); sin dato (consulta fallida) no se muestra la cifra. Aplica a todas las variantes (DIS-164). */
  pendientes?: number;
  /** Fila de administradores del área (DIS-162, DIS-164): todas las variantes; solo la pide Gestión > Plataformas > Áreas. */
  mostrarAdministradores?: boolean;
  onSelect: (area: Area) => void;
  /** Quien puede editar el área (mismo permiso que «Editar»): su badge de estado conmuta (DIS-114). */
  puedeEditar?: boolean;
  /** `PUT` del área con el estado nuevo. */
  actualizarEstado?: (status: 'Activo' | 'Inactivo') => Promise<unknown>;
  onEstadoCambiado?: () => void;
  variante?: 'estandar' | 'split' | 'onda' | 'directorio' | 'bento' | 'medallon' | 'portada' | 'banner' | 'glass' | 'flotante';
  /** Fija una altura uniforme de 240px (h-60) con dimensiones compactas para previsualización sin layout shift. */
  alturaEstandar?: boolean;
}) {
  const inactiva = area.status === 'Inactivo';
  const personas = area.users_count ?? 0;
  const color = !inactiva && textoLegible(area.color) ? area.color.trim() : undefined;
  const restantes = conteo - LOGOS_VISIBLES;
  const claseAltura = alturaEstandar ? 'h-60 min-h-60 max-h-60' : 'min-h-75';

  if (variante === 'glass') {
    return (
      <div
        onClick={() => onSelect(area)}
        data-state={inactiva ? 'inactiva' : 'activa'}
        style={variablesCss({ '--area-color': color })}
        className={`group relative flex h-full ${claseAltura} w-full flex-col justify-between overflow-hidden rounded-3xl border border-primary/40 bg-gradient-to-br from-primary/10 via-superficie/80 to-accent/10 backdrop-blur-xl ${alturaEstandar ? 'p-3.5' : 'p-5'} text-left shadow-lg cursor-pointer transition-all hover:border-primary hover:shadow-xl hover:shadow-primary/25`}
      >
        <div className="absolute -top-12 -right-12 size-32 rounded-full bg-primary/20 blur-2xl pointer-events-none" />

        <div className={`relative z-10 flex items-center justify-between ${alturaEstandar ? 'gap-2' : 'gap-3'}`}>
          <div className="flex items-center gap-2">
            <span
              aria-hidden="true"
              className={`grid ${alturaEstandar ? 'size-8 rounded-xl' : 'size-11 rounded-2xl'} place-items-center bg-primary/20 border border-primary/30 text-primary-text shadow-md shadow-primary/20`}
            >
              <Icono nombre={(area.icon as NombreIcono) || 'areas'} tamano={alturaEstandar ? 'sm' : 'lg'} />
            </span>
            <span className="px-2 py-0.5 rounded-full text-xs font-black uppercase tracking-wider bg-primary/15 text-primary-text border border-primary/30">
              Área Neón
            </span>
          </div>

          <EstadoBadgeBoton
            tipo="area"
            nombre={area.name}
            activo={!inactiva}
            editable={puedeEditar && Boolean(actualizarEstado)}
            actualizar={(status) => actualizarEstado!(status)}
            onCambiado={onEstadoCambiado}
          />
        </div>

        <div className={`relative z-10 ${alturaEstandar ? 'my-1' : 'my-2'}`}>
          <h3 className={`truncate ${alturaEstandar ? 'text-sm' : 'text-lg'} font-bold tracking-tight text-body-text group-hover:text-primary-text transition-colors`} title={area.name}>
            {area.name}
          </h3>
          <p className="mt-0.5 line-clamp-1 text-xs leading-relaxed text-texto-secundario" title={area.description ?? ''}>
            {area.description || 'Área organizativa del sistema corporativo.'}
          </p>
        </div>

        <div className={`relative z-10 grid ${pendientes === undefined ? 'grid-cols-2' : 'grid-cols-3'} gap-2 ${alturaEstandar ? 'my-1' : 'my-2'}`}>
          <div className={`flex items-center gap-2 rounded-xl bg-superficie/60 backdrop-blur-md border border-primary/20 ${alturaEstandar ? 'p-2' : 'p-2.5'}`}>
            <span className="grid size-6 place-items-center rounded-lg bg-primary/20 text-primary-text">
              <Icono nombre="usuarios" tamano="xs" />
            </span>
            <div className="min-w-0">
              <p className={`${alturaEstandar ? 'text-xs' : 'text-sm'} font-black leading-none tabular-nums text-body-text`}>{personas}</p>
              <p className="mt-0.5 truncate text-xs font-bold uppercase tracking-wider text-label">
                {personas === 1 ? 'Usuario' : 'Usuarios'}
              </p>
            </div>
          </div>

          <div className={`flex items-center gap-2 rounded-xl bg-superficie/60 backdrop-blur-md border border-primary/20 ${alturaEstandar ? 'p-2' : 'p-2.5'}`}>
            <span className="grid size-6 place-items-center rounded-lg bg-primary/20 text-primary-text">
              <Icono nombre="plataformas" tamano="xs" />
            </span>
            <div className="min-w-0">
              <p className={`${alturaEstandar ? 'text-xs' : 'text-sm'} font-black leading-none tabular-nums text-body-text`}>{conteo}</p>
              <p className="mt-0.5 truncate text-xs font-bold uppercase tracking-wider text-label">
                {conteo === 1 ? 'Plataforma' : 'Plataformas'}
              </p>
            </div>
          </div>
          <KpiPendientes area={area} pendientes={pendientes} estilo={estiloKpi('glass', alturaEstandar)} />
          <FilaAdministradores area={area} estilo={estiloKpi('glass', alturaEstandar)} mostrar={mostrarAdministradores} />
        </div>

        <div className={`relative z-10 mt-auto ${alturaEstandar ? 'pt-1.5' : 'pt-2.5'} border-t border-primary/20 flex items-center justify-between gap-3`}>
          <div className="flex items-center">
            {plataformas.slice(0, LOGOS_VISIBLES).map((p) => (
              <LogoPlataforma key={p.id} plataforma={p} />
            ))}
            {restantes > 0 ? (
              <span className="-ml-2 grid size-7 shrink-0 place-items-center rounded-lg border-2 border-panel-border bg-superficie-hundida text-xs font-bold text-label shadow-1">
                +{restantes}
              </span>
            ) : null}
          </div>

          <button
            type="button"
            aria-label={`Área ${area.name}, ver plataformas.`}
            className={`inline-flex ${alturaEstandar ? 'min-h-8 px-2.5' : 'min-h-9 px-3.5'} items-center gap-1 rounded-xl bg-gradient-to-r from-primary to-accent hover:opacity-90 text-texto-sobre-accion font-bold text-xs transition-all shadow-md`}
          >
            <span>Ver área</span>
            <Icono nombre="chevron-der" tamano="xs" ariaHidden={true} />
          </button>
        </div>
      </div>
    );
  }

  if (variante === 'flotante') {
    const imagenFondo = obtenerImagenFondoArea(area.name);
    return (
      <div
        onClick={() => onSelect(area)}
        data-state={inactiva ? 'inactiva' : 'activa'}
        className={`group relative flex h-full ${claseAltura} w-full flex-col justify-between overflow-hidden rounded-3xl border border-arte-luz/10 bg-arte-pizarra-950 ${alturaEstandar ? 'p-2.5' : 'p-3.5'} text-left shadow-2 cursor-pointer transition-all hover:border-primary/60 hover:shadow-xl`}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={imagenFondo}
          alt=""
          loading="lazy"
          decoding="async"
          className="absolute inset-0 size-full object-cover group-hover:scale-105 transition-transform duration-700 ease-out pointer-events-none"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-arte-sombra/90 via-arte-sombra/50 to-arte-sombra/30 pointer-events-none" />

        <div className="relative z-10 flex items-center justify-between p-1">
          <span className="px-2 py-0.5 rounded-full text-xs font-black uppercase tracking-wider bg-arte-sombra/60 text-arte-luz/90 backdrop-blur-md border border-arte-luz/20">
            {conteo} herramientas
          </span>

          <EstadoBadgeBoton
            tipo="area"
            nombre={area.name}
            activo={!inactiva}
            editable={puedeEditar && Boolean(actualizarEstado)}
            actualizar={(status) => actualizarEstado!(status)}
            onCambiado={onEstadoCambiado}
          />
        </div>

        <div className={`relative z-10 mt-auto rounded-2xl bg-arte-sombra/65 backdrop-blur-xl border border-arte-luz/20 ${alturaEstandar ? 'p-2.5 gap-1.5' : 'p-3.5 gap-2.5'} text-arte-luz shadow-2xl flex flex-col`}>
          <div className={`flex items-center ${alturaEstandar ? 'gap-2' : 'gap-2.5'}`}>
            <span className={`grid ${alturaEstandar ? 'size-7 text-xs rounded-lg' : 'size-9 text-sm rounded-xl'} place-items-center bg-primary text-arte-luz font-bold shadow-md shrink-0`}>
              <Icono nombre={(area.icon as NombreIcono) || 'areas'} tamano={alturaEstandar ? 'sm' : 'md'} />
            </span>
            <div className="min-w-0 flex-1">
              <h3 className={`truncate ${alturaEstandar ? 'text-sm' : 'text-base'} font-bold tracking-tight text-arte-luz group-hover:text-primary-text transition-colors`} title={area.name}>
                {area.name}
              </h3>
              <p className="truncate text-xs text-arte-pizarra-300">
                {personas} colaboradores activos
              </p>
            </div>
          </div>

          {pendientes === undefined && !mostrarAdministradores ? null : (
          <div className="grid gap-2 pt-1">
            <KpiPendientes area={area} pendientes={pendientes} estilo={estiloKpi('oscuro', alturaEstandar)} />
            <FilaAdministradores area={area} estilo={estiloKpi('oscuro', alturaEstandar)} mostrar={mostrarAdministradores} />
          </div>
          )}
          <div className={`${alturaEstandar ? 'pt-1.5' : 'pt-2'} border-t border-arte-luz/15 flex items-center justify-between gap-2`}>
            <div className="flex items-center">
              {plataformas.slice(0, LOGOS_VISIBLES).map((p) => (
                <LogoPlataforma key={p.id} plataforma={p} />
              ))}
              {restantes > 0 ? (
                <span className="-ml-1.5 grid size-6 shrink-0 place-items-center rounded-md border border-arte-luz/20 bg-arte-sombra/70 text-xs font-bold text-arte-luz">
                  +{restantes}
                </span>
              ) : null}
            </div>

            <button
              type="button"
              aria-label={`Área ${area.name}, ver plataformas.`}
              className={`inline-flex ${alturaEstandar ? 'min-h-7 px-2.5 text-xs' : 'min-h-8 px-3 text-xs'} items-center gap-1 rounded-lg bg-arte-luz/25 hover:bg-primary text-arte-luz font-bold transition-all border border-arte-luz/30`}
            >
              <span>Explorar</span>
              <Icono nombre="chevron-der" tamano="xs" ariaHidden={true} />
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (variante === 'portada') {
    const imagenFondo = obtenerImagenFondoArea(area.name);
    return (
      <div
        onClick={() => onSelect(area)}
        data-state={inactiva ? 'inactiva' : 'activa'}
        className={`group relative flex h-full ${claseAltura} w-full flex-col justify-between overflow-hidden rounded-3xl border border-arte-luz/10 bg-arte-pizarra-950 ${alturaEstandar ? 'p-3' : 'p-4 sm:p-5'} text-left shadow-2 cursor-pointer transition-all hover:border-primary/60 hover:shadow-xl`}
      >
        {/* Imagen de fondo inmersiva con gradiente protector de legibilidad */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={imagenFondo}
          alt=""
          loading="lazy"
          decoding="async"
          className="absolute inset-0 size-full object-cover group-hover:scale-105 transition-transform duration-700 ease-out pointer-events-none"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-arte-sombra/95 via-arte-sombra/70 to-arte-sombra/35 pointer-events-none" />
        <div className="absolute inset-0 ring-1 ring-inset ring-arte-luz/10 rounded-3xl pointer-events-none" />

        {/* Cabecera: Icono con vidrio esmerilado + Badge de estado */}
        <div className={`relative z-10 flex items-center justify-between ${alturaEstandar ? 'gap-2' : 'gap-3'}`}>
          <div className="flex items-center gap-2">
            <span
              aria-hidden="true"
              className={`grid ${alturaEstandar ? 'size-8 rounded-lg' : 'size-11 rounded-xl'} place-items-center bg-arte-luz/20 backdrop-blur-md border border-arte-luz/25 text-arte-luz shadow-md`}
            >
              <Icono nombre={(area.icon as NombreIcono) || 'areas'} tamano={alturaEstandar ? 'sm' : 'lg'} />
            </span>
            <span className="px-2 py-0.5 rounded-full text-xs font-black uppercase tracking-wider bg-arte-sombra/50 text-arte-luz/90 backdrop-blur-md border border-arte-luz/15">
              DEPARTAMENTO
            </span>
          </div>

          <EstadoBadgeBoton
            tipo="area"
            nombre={area.name}
            activo={!inactiva}
            editable={puedeEditar && Boolean(actualizarEstado)}
            actualizar={(status) => actualizarEstado!(status)}
            onCambiado={onEstadoCambiado}
          />
        </div>

        {/* Cuerpo central: Nombre y descripción */}
        <div className={`relative z-10 ${alturaEstandar ? 'my-1' : 'my-2'}`}>
          <h3 className={`truncate ${alturaEstandar ? 'text-sm' : 'text-lg'} font-black tracking-tight text-arte-luz drop-shadow-sm group-hover:text-primary-text transition-colors`} title={area.name}>
            {area.name}
          </h3>
          <p className="mt-0.5 line-clamp-1 text-xs leading-relaxed text-arte-pizarra-300 drop-shadow-xs" title={area.description ?? ''}>
            {area.description || 'Área organizativa del sistema corporativo.'}
          </p>
        </div>

        {/* Métricas con diseño glassmórfico de alta fidelidad */}
        <div className={`relative z-10 grid ${pendientes === undefined ? 'grid-cols-2' : 'grid-cols-3'} gap-2 ${alturaEstandar ? 'my-1' : 'my-2'}`}>
          <div className={`flex items-center gap-2 rounded-xl bg-arte-luz/10 backdrop-blur-md border border-arte-luz/15 ${alturaEstandar ? 'p-1.5' : 'p-2'} text-arte-luz`}>
            <span className="grid size-6 place-items-center rounded-lg bg-arte-luz/15 text-arte-luz">
              <Icono nombre="usuarios" tamano="xs" />
            </span>
            <div className="min-w-0">
              <p className={`${alturaEstandar ? 'text-xs' : 'text-sm'} font-black leading-none tabular-nums text-arte-luz`}>{personas}</p>
              <p className="mt-0.5 truncate text-xs font-bold uppercase tracking-wider text-arte-pizarra-300">
                {personas === 1 ? 'Usuario' : 'Usuarios'}
              </p>
            </div>
          </div>

          <div className={`flex items-center gap-2 rounded-xl bg-arte-luz/10 backdrop-blur-md border border-arte-luz/15 ${alturaEstandar ? 'p-1.5' : 'p-2'} text-arte-luz`}>
            <span className="grid size-6 place-items-center rounded-lg bg-arte-luz/15 text-arte-luz">
              <Icono nombre="plataformas" tamano="xs" />
            </span>
            <div className="min-w-0">
              <p className={`${alturaEstandar ? 'text-xs' : 'text-sm'} font-black leading-none tabular-nums text-arte-luz`}>{conteo}</p>
              <p className="mt-0.5 truncate text-xs font-bold uppercase tracking-wider text-arte-pizarra-300">
                {conteo === 1 ? 'Plataforma' : 'Plataformas'}
              </p>
            </div>
          </div>
          <KpiPendientes area={area} pendientes={pendientes} estilo={estiloKpi('oscuro', alturaEstandar)} />
          <FilaAdministradores area={area} estilo={estiloKpi('oscuro', alturaEstandar)} mostrar={mostrarAdministradores} />
        </div>

        {/* Pie: Logos apilados + Botón Explorar */}
        <div className={`relative z-10 mt-auto ${alturaEstandar ? 'pt-1.5' : 'pt-2.5'} border-t border-arte-luz/15 flex items-center justify-between gap-3`}>
          <div className="flex items-center">
            {plataformas.slice(0, LOGOS_VISIBLES).map((p) => (
              <LogoPlataforma key={p.id} plataforma={p} />
            ))}
            {restantes > 0 ? (
              <span className="-ml-2 grid size-7 shrink-0 place-items-center rounded-lg border-2 border-arte-luz/20 bg-arte-sombra/60 backdrop-blur-sm text-xs font-bold text-arte-luz shadow-1">
                +{restantes}
              </span>
            ) : null}
          </div>

          <button
            type="button"
            aria-label={`Área ${area.name}, ver plataformas.`}
            className={`inline-flex ${alturaEstandar ? 'min-h-8 px-2.5 text-xs' : 'min-h-9 px-3.5 text-xs'} items-center gap-1.5 rounded-xl bg-arte-luz/20 hover:bg-arte-luz/30 backdrop-blur-md border border-arte-luz/30 text-arte-luz font-bold transition-all shadow-md group-hover:bg-primary group-hover:border-primary group-hover:text-arte-luz`}
          >
            <span>Ver plataformas</span>
            <Icono nombre="chevron-der" tamano="xs" ariaHidden={true} />
          </button>
        </div>
      </div>
    );
  }

  if (variante === 'banner') {
    const imagenFondo = obtenerImagenFondoArea(area.name);
    return (
      <div
        onClick={() => onSelect(area)}
        data-state={inactiva ? 'inactiva' : 'activa'}
        className={`group relative flex h-full ${claseAltura} w-full flex-col justify-between overflow-hidden rounded-3xl border border-panel-border bg-panel-fill text-left shadow-1 cursor-pointer transition-all hover:border-primary/50 hover:shadow-2`}
      >
        {/* Cabecera Panorámica / Hero Banner con imagen fotográfica de fondo */}
        <div className={`relative ${alturaEstandar ? 'h-20' : 'h-28'} w-full overflow-hidden shrink-0 bg-arte-pizarra-900`}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={imagenFondo}
            alt=""
            loading="lazy"
            decoding="async"
            className="absolute inset-0 size-full object-cover group-hover:scale-105 transition-transform duration-700 ease-out pointer-events-none"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-arte-sombra/85 via-arte-sombra/45 to-arte-sombra/25 pointer-events-none" />

          {/* Badges superiores sobre el banner */}
          <div className={`relative z-10 flex items-center justify-between ${alturaEstandar ? 'p-2' : 'p-3'}`}>
            <span className="px-2 py-0.5 rounded-full text-xs font-black uppercase tracking-wider bg-arte-sombra/60 text-arte-luz/95 backdrop-blur-md border border-arte-luz/20">
              DEPARTAMENTO
            </span>

            <EstadoBadgeBoton
              tipo="area"
              nombre={area.name}
              activo={!inactiva}
              editable={puedeEditar && Boolean(actualizarEstado)}
              actualizar={(status) => actualizarEstado!(status)}
              onCambiado={onEstadoCambiado}
            />
          </div>

          {/* Chip de icono de área superpuesto en el banner */}
          <div className="absolute bottom-2 left-3 z-10 flex items-center gap-1.5">
            <span
              className={`flex ${alturaEstandar ? 'size-8 text-xs' : 'size-10 text-sm'} items-center justify-center rounded-xl bg-primary text-arte-luz font-black shadow-lg border-2 border-panel-fill`}
              aria-hidden="true"
            >
              <Icono nombre={(area.icon as NombreIcono) || 'areas'} tamano={alturaEstandar ? 'sm' : 'md'} />
            </span>
            <span className="px-2 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-arte-sombra/60 text-arte-luz/90 backdrop-blur-md border border-arte-luz/15">
              {conteo} apps
            </span>
          </div>
        </div>

        {/* Contenido estructurado inferior */}
        <div className={`flex flex-1 flex-col justify-between ${alturaEstandar ? 'p-3 pt-2 space-y-1.5' : 'p-4 pt-3 space-y-2.5'}`}>
          <div>
            <h3 className={`truncate ${alturaEstandar ? 'text-sm' : 'text-base'} font-bold tracking-tight text-body-text group-hover:text-primary-text transition-colors`} title={area.name}>
              {area.name}
            </h3>
            <p className="line-clamp-1 text-xs leading-relaxed text-texto-secundario mt-0.5" title={area.description ?? ''}>
              {area.description || 'Área organizativa del sistema corporativo.'}
            </p>
          </div>

          {/* Métricas compactas */}
          <div className={`grid ${pendientes === undefined ? 'grid-cols-2' : 'grid-cols-3'} gap-2 pt-0.5`}>
            <div className={`flex items-center gap-1.5 rounded-xl bg-superficie-hundida/70 border border-panel-border/80 ${alturaEstandar ? 'p-1.5' : 'p-2'}`}>
              <span className="grid size-5 place-items-center rounded-lg bg-superficie text-primary-text shadow-xs">
                <Icono nombre="usuarios" tamano="xs" />
              </span>
              <div className="min-w-0">
                <p className="text-xs font-black tabular-nums text-body-text leading-none">{personas}</p>
                <p className="text-xs font-bold uppercase tracking-wider text-label mt-0.5">Usuarios</p>
              </div>
            </div>

            <div className={`flex items-center gap-1.5 rounded-xl bg-superficie-hundida/70 border border-panel-border/80 ${alturaEstandar ? 'p-1.5' : 'p-2'}`}>
              <span className="grid size-5 place-items-center rounded-lg bg-superficie text-primary-text shadow-xs">
                <Icono nombre="plataformas" tamano="xs" />
              </span>
              <div className="min-w-0">
                <p className="text-xs font-black tabular-nums text-body-text leading-none">{conteo}</p>
                <p className="text-xs font-bold uppercase tracking-wider text-label mt-0.5">Plataformas</p>
              </div>
            </div>

            <KpiPendientes area={area} pendientes={pendientes} estilo={estiloKpi('claro', alturaEstandar)} />
            <FilaAdministradores area={area} estilo={estiloKpi('claro', alturaEstandar)} mostrar={mostrarAdministradores} />
          </div>

          {/* Pie: botón de acción */}
          <div className={`pt-1.5 border-t border-panel-border/80 flex items-center justify-between gap-2 mt-auto`}>
            <div className="flex items-center">
              {plataformas.slice(0, LOGOS_VISIBLES).map((p) => (
                <LogoPlataforma key={p.id} plataforma={p} />
              ))}
              {restantes > 0 ? (
                <span className="-ml-1.5 grid size-6 shrink-0 place-items-center rounded-lg border border-panel-border bg-superficie-hundida text-xs font-bold text-label shadow-xs">
                  +{restantes}
                </span>
              ) : null}
            </div>

            <button
              type="button"
              aria-label={`Área ${area.name}, ver plataformas.`}
              className={`inline-flex ${alturaEstandar ? 'min-h-8 px-2.5 text-xs' : 'min-h-9 px-3.5 text-xs'} items-center gap-1 rounded-xl bg-primary hover:bg-primary/90 text-texto-sobre-accion font-bold transition-all shadow-xs`}
            >
              <span>Ver área</span>
              <Icono nombre="chevron-der" tamano="xs" ariaHidden={true} />
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (variante === 'split') {
    return (
      <div
        onClick={() => onSelect(area)}
        data-state={inactiva ? 'inactiva' : 'activa'}
        style={variablesCss({ '--area-color': color })}
        className={`group relative flex h-full ${claseAltura} w-full flex-col justify-between overflow-hidden rounded-3xl border border-panel-border bg-panel-fill text-left shadow-1 cursor-pointer transition-all hover:border-primary/50 hover:shadow-2`}
      >
        <div className={`bg-success/15 ${alturaEstandar ? 'p-2.5 h-20' : 'p-4 h-28'} flex flex-col justify-between shrink-0`}>
          <div className="flex items-center justify-between">
            <span className="text-xs font-black uppercase tracking-wider bg-success-fondo text-success-text px-2 py-0.5 rounded-md">
              ÁREA CORPORATIVA
            </span>
            <EstadoBadgeBoton
              tipo="area"
              nombre={area.name}
              activo={!inactiva}
              editable={puedeEditar && Boolean(actualizarEstado)}
              actualizar={(status) => actualizarEstado!(status)}
              onCambiado={onEstadoCambiado}
            />
          </div>
          <div className="flex items-center gap-2.5">
            <span className={`${alturaEstandar ? 'size-8 text-xs' : 'size-10 text-sm'} rounded-xl flex items-center justify-center font-black text-arte-luz shadow-md border-2 border-arte-luz/30 bg-arte-esmeralda-700`}>
              {area.name.slice(0, 2).toUpperCase()}
            </span>
            <div className="min-w-0 flex-1">
              <span className="text-xs font-bold text-success-text block truncate">{area.name}</span>
              <span className="text-xs font-semibold text-label">{conteo} plataformas activas</span>
            </div>
          </div>
        </div>

        <div className={`${alturaEstandar ? 'p-3 space-y-1.5' : 'p-4 space-y-2.5'} flex flex-1 flex-col justify-between`}>
          <div>
            <h3 className={`${alturaEstandar ? 'text-sm' : 'text-base'} font-bold tracking-tight text-body-text truncate`} title={area.name}>{area.name}</h3>
            <p className="text-xs text-label mt-0.5 line-clamp-1">{area.description || 'Área organizativa del sistema.'}</p>
          </div>
          {pendientes === undefined && !mostrarAdministradores ? null : (
          <div className="grid gap-2 pt-1">
            <KpiPendientes area={area} pendientes={pendientes} estilo={estiloKpi('claro', alturaEstandar)} />
            <FilaAdministradores area={area} estilo={estiloKpi('claro', alturaEstandar)} mostrar={mostrarAdministradores} />
          </div>
          )}
          <div className={`${alturaEstandar ? 'pt-1.5' : 'pt-2'} border-t border-panel-border/80 flex items-center justify-between gap-3 mt-auto`}>
            <div>
              <span className={`${alturaEstandar ? 'text-lg' : 'text-xl'} font-black text-body-text tabular-nums`}>{personas}</span>
              <span className="text-xs font-bold text-label block -mt-0.5">{personas === 1 ? 'colaborador' : 'colaboradores'}</span>
            </div>
            <button
              type="button"
              aria-label={`Área ${area.name}, ver plataformas.`}
              className={`${alturaEstandar ? 'px-3 py-1.5 text-xs' : 'px-4 py-2 text-xs'} rounded-xl bg-primary hover:bg-primary/90 text-texto-sobre-accion font-bold transition-all shadow-xs`}
            >
              Ver área →
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (variante === 'onda') {
    return (
      <div
        onClick={() => onSelect(area)}
        data-state={inactiva ? 'inactiva' : 'activa'}
        style={variablesCss({ '--area-color': color })}
        className={`group relative flex h-full ${claseAltura} w-full flex-col justify-between overflow-hidden rounded-3xl border border-panel-border bg-panel-fill text-left shadow-1 cursor-pointer transition-all hover:border-primary/50 hover:shadow-2`}
      >
        <div>
          <div className={`relative ${alturaEstandar ? 'h-20 p-2.5' : 'h-28 p-3.5'} w-full flex flex-col justify-between text-arte-luz overflow-hidden bg-gradient-to-r from-arte-ambar-700 to-arte-naranja-700 shrink-0`}>
            <div className="flex items-center justify-between">
              <span className="text-xs font-black uppercase tracking-wider text-arte-luz">{area.name}</span>
              <EstadoBadgeBoton
                tipo="area"
                nombre={area.name}
                activo={!inactiva}
                editable={puedeEditar && Boolean(actualizarEstado)}
                actualizar={(status) => actualizarEstado!(status)}
                onCambiado={onEstadoCambiado}
              />
            </div>
            <div className={`text-center ${alturaEstandar ? 'text-xl' : 'text-2xl'} font-black drop-shadow-xs`}>
              <Icono nombre={(area.icon as NombreIcono) || 'areas'} tamano={alturaEstandar ? 'md' : 'lg'} />
            </div>
            <svg viewBox="0 0 500 150" preserveAspectRatio="none" className="absolute -bottom-1 inset-x-0 w-full h-8 text-panel-fill fill-current">
              <path d="M0.00,49.98 C150.00,150.00 349.81,-49.98 500.00,49.98 L500.00,150.00 L0.00,150.00 Z" />
            </svg>
          </div>
          <div className={`${alturaEstandar ? 'p-3 space-y-1' : 'p-4 space-y-1.5'} text-center`}>
            <h3 className={`${alturaEstandar ? 'text-sm' : 'text-base'} font-bold text-body-text`}>{area.name}</h3>
            <p className="text-xs text-label line-clamp-1">{area.description || 'Área organizativa del sistema.'}</p>
            <div className="text-xs font-bold text-label pt-0.5">
              {personas} {personas === 1 ? 'usuario' : 'usuarios'} • {conteo} plataformas
            </div>
            {pendientes === undefined && !mostrarAdministradores ? null : (
            <div className="grid gap-2 pt-1 text-left">
              <KpiPendientes area={area} pendientes={pendientes} estilo={estiloKpi('claro', alturaEstandar)} />
              <FilaAdministradores area={area} estilo={estiloKpi('claro', alturaEstandar)} mostrar={mostrarAdministradores} />
            </div>
            )}
          </div>
        </div>
        <div className={`${alturaEstandar ? 'p-3 pt-0' : 'p-4 pt-0'} text-center mt-auto`}>
          <button
            type="button"
            className={`w-full max-w-40 mx-auto ${alturaEstandar ? 'py-1.5 text-xs' : 'py-2 text-xs'} rounded-full bg-primary hover:bg-primary/90 text-texto-sobre-accion font-bold transition-all shadow-xs`}
          >
            Explorar área
          </button>
        </div>
      </div>
    );
  }

  if (variante === 'directorio') {
    return (
      <div
        onClick={() => onSelect(area)}
        data-state={inactiva ? 'inactiva' : 'activa'}
        style={variablesCss({ '--area-color': color })}
        className={`group relative flex h-full ${claseAltura} w-full flex-col justify-between overflow-hidden rounded-3xl border border-panel-border bg-panel-fill text-left shadow-1 cursor-pointer transition-all hover:border-primary/50 hover:shadow-2`}
      >
        <div>
          <div className={`relative ${alturaEstandar ? 'h-20 p-2.5' : 'h-28 p-3.5'} w-full bg-gradient-to-tr from-arte-purpura-950 via-arte-pizarra-900 to-arte-indigo-950 flex flex-col justify-between text-arte-luz shrink-0`}>
            <div className="flex items-center justify-between">
              <span className="text-xs font-black uppercase tracking-wider bg-arte-sombra/40 text-arte-purpura-200 px-2 py-0.5 rounded-md self-start">
                {area.name}
              </span>
              <EstadoBadgeBoton
                tipo="area"
                nombre={area.name}
                activo={!inactiva}
                editable={puedeEditar && Boolean(actualizarEstado)}
                actualizar={(status) => actualizarEstado!(status)}
                onCambiado={onEstadoCambiado}
              />
            </div>
            <div className="flex items-center gap-1.5 bg-arte-sombra/50 backdrop-blur-xs px-2.5 py-0.5 rounded-xl text-arte-luz self-start">
              <span className="text-xs font-bold text-arte-purpura-200">{personas} integrantes</span>
            </div>
          </div>
          <div className={`${alturaEstandar ? 'p-3 space-y-1' : 'p-4 space-y-1.5'}`}>
            <h3 className={`${alturaEstandar ? 'text-sm' : 'text-base'} font-bold text-body-text`}>{area.name}</h3>
            <p className="text-xs text-label line-clamp-1">{area.description || 'Área organizativa del sistema.'}</p>
            <div className="flex items-center gap-1 flex-wrap pt-0.5">
              {plataformas.slice(0, 3).map((p) => (
                <span key={p.id} className="px-1.5 py-0.5 rounded text-xs font-semibold bg-superficie-hundida text-label">
                  {p.name}
                </span>
              ))}
              {restantes > 0 ? <span className="text-xs font-bold text-label">+{restantes}</span> : null}
            </div>
            {pendientes === undefined && !mostrarAdministradores ? null : (
            <div className="grid gap-2 pt-1">
              <KpiPendientes area={area} pendientes={pendientes} estilo={estiloKpi('claro', alturaEstandar)} />
              <FilaAdministradores area={area} estilo={estiloKpi('claro', alturaEstandar)} mostrar={mostrarAdministradores} />
            </div>
            )}
          </div>
        </div>
        <div className={`${alturaEstandar ? 'p-3 pt-0' : 'p-4 pt-0'} flex gap-2 mt-auto`}>
          <button type="button" className={`flex-1 ${alturaEstandar ? 'py-1.5 text-xs' : 'py-2 text-xs'} rounded-xl bg-primary hover:bg-primary/90 text-texto-sobre-accion font-bold transition-all`}>
            Ver área →
          </button>
        </div>
      </div>
    );
  }

  if (variante === 'bento') {
    return (
      <div
        onClick={() => onSelect(area)}
        data-state={inactiva ? 'inactiva' : 'activa'}
        style={variablesCss({ '--area-color': color })}
        className={`group relative flex h-full ${claseAltura} w-full flex-col justify-between overflow-hidden rounded-3xl border border-panel-border bg-panel-fill ${alturaEstandar ? 'p-3' : 'p-4 sm:p-5'} text-left shadow-1 cursor-pointer transition-all hover:border-primary/50 hover:shadow-2`}
      >
        <div>
          <div className="flex items-center justify-between gap-3 mb-1.5">
            <span className="px-2 py-0.5 rounded-md text-xs font-black uppercase tracking-wider text-arte-luz bg-primary">
              Área
            </span>
            <EstadoBadgeBoton
              tipo="area"
              nombre={area.name}
              activo={!inactiva}
              editable={puedeEditar && Boolean(actualizarEstado)}
              actualizar={(status) => actualizarEstado!(status)}
              onCambiado={onEstadoCambiado}
            />
          </div>

          <h3 className={`${alturaEstandar ? 'text-sm' : 'text-lg'} font-bold tracking-tight text-body-text`}>{area.name}</h3>
          <p className="mt-0.5 line-clamp-1 text-xs text-label">{area.description || 'Área organizativa del sistema.'}</p>

          <div className={`grid grid-cols-2 ${alturaEstandar ? 'gap-1.5 mt-2' : 'gap-2 mt-3'}`}>
            <div className={`${alturaEstandar ? 'p-2' : 'p-2.5'} rounded-2xl bg-superficie-hundida/70 border border-panel-border/80 flex flex-col justify-between`}>
              <span className="text-xs font-bold text-label uppercase">Equipo</span>
              <span className={`${alturaEstandar ? 'text-base' : 'text-xl'} font-black text-body-text tabular-nums`}>{personas}</span>
              <span className="text-xs text-label">{personas === 1 ? 'colaborador' : 'colaboradores'}</span>
            </div>

            <div className={`${alturaEstandar ? 'p-2' : 'p-2.5'} rounded-2xl bg-superficie-hundida/70 border border-panel-border/80 flex flex-col justify-between`}>
              <span className="text-xs font-bold text-label uppercase">Herramientas</span>
              <div className="flex items-center gap-1 my-0.5">
                {plataformas.slice(0, 2).map((p) => (
                  <span key={p.id} className="size-4 rounded bg-superficie border border-panel-border text-xs font-bold flex items-center justify-center text-body-text">
                    {p.name.slice(0, 2).toUpperCase()}
                  </span>
                ))}
                {restantes > 0 ? <span className="text-xs font-bold text-label">+{restantes}</span> : null}
              </div>
              <span className="text-xs font-bold text-primary-text">{conteo} activas</span>
            </div>
          </div>
          {pendientes === undefined && !mostrarAdministradores ? null : (
          <div className="grid gap-2 mt-2">
            <KpiPendientes area={area} pendientes={pendientes} estilo={estiloKpi('claro', alturaEstandar)} />
            <FilaAdministradores area={area} estilo={estiloKpi('claro', alturaEstandar)} mostrar={mostrarAdministradores} />
          </div>
          )}
        </div>

        <div className={`mt-auto ${alturaEstandar ? 'pt-2' : 'pt-3'} border-t border-panel-border/80`}>
          <button
            type="button"
            className={`w-full ${alturaEstandar ? 'py-1.5 text-xs' : 'py-2.5 text-xs'} rounded-xl bg-superficie-hundida hover:bg-superficie border border-panel-border text-body-text font-bold transition-colors flex items-center justify-center gap-1.5`}
          >
            <span>Ver catálogo del área</span>
            <Icono nombre="chevron-der" tamano="xs" ariaHidden={true} />
          </button>
        </div>
      </div>
    );
  }

  if (variante === 'medallon') {
    return (
      <div
        onClick={() => onSelect(area)}
        data-state={inactiva ? 'inactiva' : 'activa'}
        style={variablesCss({ '--area-color': color })}
        className={`group relative flex h-full ${claseAltura} w-full flex-col justify-between overflow-hidden rounded-3xl border border-panel-border bg-panel-fill text-center shadow-1 cursor-pointer transition-all hover:border-primary/50 hover:shadow-2`}
      >
        <div>
          <div className={`${alturaEstandar ? 'h-14 px-3' : 'h-18 px-4'} w-full relative flex items-center justify-between bg-gradient-to-r from-primary to-accent`}>
            <span className="text-xs font-bold text-arte-luz/90 uppercase tracking-widest bg-arte-sombra/30 px-2 py-0.5 rounded-full">
              Corporativo
            </span>
            <EstadoBadgeBoton
              tipo="area"
              nombre={area.name}
              activo={!inactiva}
              editable={puedeEditar && Boolean(actualizarEstado)}
              actualizar={(status) => actualizarEstado!(status)}
              onCambiado={onEstadoCambiado}
            />
          </div>

          <div className={`${alturaEstandar ? '-mt-5 mb-0.5' : '-mt-7 mb-1'} flex justify-center`}>
            <span className={`${alturaEstandar ? 'size-10 text-base' : 'size-14 text-xl'} rounded-full flex items-center justify-center text-arte-luz font-black shadow-xl border-4 border-panel-fill bg-primary`}>
              <Icono nombre={(area.icon as NombreIcono) || 'areas'} tamano={alturaEstandar ? 'sm' : 'md'} />
            </span>
          </div>

          <div className={`${alturaEstandar ? 'px-3 space-y-0.5' : 'px-4 space-y-1'}`}>
            <h3 className={`${alturaEstandar ? 'text-sm' : 'text-base'} font-bold text-body-text tracking-tight`}>{area.name}</h3>
            <p className="text-xs text-label line-clamp-1">{area.description || 'Área organizativa del sistema.'}</p>
            <div className="inline-flex items-center gap-1.5 pt-0.5 px-2.5 py-0.5 rounded-full bg-superficie-hundida text-xs font-bold text-label">
              <span className="inline-flex items-center gap-1">
                <Icono nombre="usuarios" tamano="xs" ariaHidden={true} className="text-primary-text shrink-0" />
                <span>{personas} miembros</span>
              </span>
              <span>•</span>
              <span className="inline-flex items-center gap-1">
                <Icono nombre="plataformas" tamano="xs" ariaHidden={true} className="text-primary-text shrink-0" />
                <span>{conteo} plataformas</span>
              </span>
            </div>
            {pendientes === undefined && !mostrarAdministradores ? null : (
            <div className="grid gap-2 pt-1 text-left">
              <KpiPendientes area={area} pendientes={pendientes} estilo={estiloKpi('claro', alturaEstandar)} />
              <FilaAdministradores area={area} estilo={estiloKpi('claro', alturaEstandar)} mostrar={mostrarAdministradores} />
            </div>
            )}
          </div>
        </div>

        <div className={`${alturaEstandar ? 'p-2.5 pt-1' : 'p-4 pt-2'} mt-auto`}>
          <button
            type="button"
            className={`w-full max-w-42.5 mx-auto ${alturaEstandar ? 'py-1.5 text-xs' : 'py-2 text-xs'} px-3 rounded-full bg-primary hover:bg-primary/90 text-texto-sobre-accion font-bold transition-all shadow-xs flex items-center justify-center gap-1.5`}
          >
            <span>Explorar Área</span>
            <Icono nombre="chevron-der" tamano="xs" ariaHidden={true} />
          </button>
        </div>
      </div>
    );
  }

  return (
    // La tarjeta completa abre las plataformas con el ratón; el control accesible (teclado y
    // lector de pantalla) es «Ver plataformas», un botón propio. El badge de estado es otro
    // botón y no queda anidado en ninguno (DIS-114).
    <div
      onClick={() => onSelect(area)}
      data-state={inactiva ? 'inactiva' : 'activa'}
      style={variablesCss({ '--area-color': color })}
      className={`nx-area-card group relative flex h-full ${claseAltura} w-full min-w-12 cursor-pointer select-none flex-col justify-between overflow-hidden rounded-xl border border-panel-border bg-panel-fill text-left shadow-1`}
    >
      <div>
        <div className={`nx-area-card__cabecera relative flex items-center ${alturaEstandar ? 'gap-2.5 p-3 pb-2' : 'gap-3 p-4 pb-3'}`}>
          <span
            aria-hidden="true"
            data-texto={color ? atributoTexto(color) : undefined}
            className={`nx-area-card__icono relative grid ${alturaEstandar ? 'size-9 rounded-lg' : 'size-11 rounded-xl'} shrink-0 place-items-center shadow-1`}
          >
            <Icono nombre={(area.icon as NombreIcono) || 'areas'} tamano={alturaEstandar ? 'md' : 'lg'} />
          </span>
          <div className="relative min-w-0 flex-1">
            <h3 className={`truncate ${alturaEstandar ? 'text-sm' : 'text-base'} font-bold tracking-tight text-body-text`} title={area.name}>
              {area.name}
            </h3>
            <p className="mt-0.5 line-clamp-1 text-xs leading-snug text-label" title={area.description ?? ''}>
              {area.description || 'Área organizativa del sistema.'}
            </p>
          </div>
        </div>

        <div className={`grid flex-1 grid-cols-3 content-center ${alturaEstandar ? 'gap-2 px-3 pb-2' : 'gap-2.5 px-4 pb-3'}`}>
          <Cifra icono="usuarios" valor={personas} etiqueta={personas === 1 ? 'Usuario' : 'Usuarios'} compacta={alturaEstandar} />
          <Cifra icono="plataformas" valor={conteo} etiqueta={conteo === 1 ? 'Plataforma' : 'Plataformas'} compacta={alturaEstandar} />
          {pendientes === undefined ? null : (
            <Cifra
              icono="reloj"
              valor={pendientes}
              etiqueta="Solicitudes pendientes"
              compacta={alturaEstandar}
              enlace={{ area, pendientes }}
            />
          )}
          {mostrarAdministradores ? <AdministradoresArea area={area} compacta={alturaEstandar} /> : null}
        </div>
      </div>

      <div className={`nx-area-card__pie mt-auto flex items-center justify-between gap-2 border-t ${alturaEstandar ? 'px-3 py-2' : 'px-4 py-3'}`}>
        <div className="flex min-w-0 items-center gap-1.5">
          <EstadoBadgeBoton
            tipo="area"
            nombre={area.name}
            activo={!inactiva}
            editable={puedeEditar && Boolean(actualizarEstado)}
            actualizar={(status) => actualizarEstado!(status)}
            onCambiado={onEstadoCambiado}
          />
          {plataformas.length > 0 ? (
            <div className="nx-area-card__logos flex items-center" aria-hidden="true">
              {plataformas.slice(0, LOGOS_VISIBLES).map((p) => (
                <LogoPlataforma key={p.id} plataforma={p} />
              ))}
              {restantes > 0 ? (
                <span className={`-ml-2 grid ${alturaEstandar ? 'size-6 text-xs' : 'size-7 text-xs'} shrink-0 place-items-center rounded-lg border-2 border-panel-fill bg-superficie-hundida font-bold text-label shadow-1`}>
                  +{restantes}
                </span>
              ) : null}
            </div>
          ) : inactiva ? null : (
            <span className="text-xs text-label">Sin plataformas</span>
          )}
        </div>
        <button
          type="button"
          aria-label={`Área ${area.name}${inactiva ? ' (Inactiva)' : ''}, ${conteo} ${conteo === 1 ? 'plataforma' : 'plataformas'}. Ver plataformas.`}
          className={`nx-area-card__ir inline-flex ${alturaEstandar ? 'min-h-7 px-2.5 text-xs' : 'min-h-8 px-3 text-xs'} shrink-0 cursor-pointer items-center gap-1 whitespace-nowrap rounded-full font-bold`}
        >
          Ver plataformas
          <Icono nombre="chevron-der" tamano="xs" ariaHidden={true} className="nx-area-card__flecha" />
        </button>
      </div>
    </div>
  );
}
