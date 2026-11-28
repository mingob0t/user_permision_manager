'use client';

/**
 * Administración de plataformas: crear, editar y eliminar, con el tipo de
 * integración y los grupos de acceso por nivel (DIS-017). Cada fila enlaza a
 * su historial en Auditoría (DIS-035).
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { api } from '@/lib/api';
import { enlaceSeguro } from '@/lib/enlace-seguro';
import { useAsync } from '@/lib/use-async';
import { usePolling } from '@/lib/use-polling';
import { requestsApi } from '@/lib/access/requests';
import type { Area, Platform, PlatformWarning } from '@/lib/types';
import { AreaAdminsPanel } from './areas/area-admins-panel';
import { AreaForm } from './areas/area-form';
import { TarjetaArea } from './areas/tarjeta-area';
import { mensajeDeError } from './areas/area-errors';
import { CapsulePager } from './capsule-pager';
import { DataTable } from './data-table';
import { Button, ConfirmDialog } from './form';
import { Icono } from './icono';
import { PageHeader } from './page-header';
import { columnasPlataformas, sinEnlaceWeb } from './platforms/platform-columns';
import { MissingLinkNote } from './platforms/missing-link-note';
import { AreaCardDesignDrawer } from './platforms/area-card-design-drawer';
import { PlatformCardDesignDrawer } from './platforms/platform-card-design-drawer';
import {
  CLAVE_DISENO_CARDS,
  CLAVE_DISENO_CARDS_AREA,
  type AreaCardDesignVariant,
  type CardDesignVariant,
  leerForzarDisenoArea,
  guardarForzarDisenoArea,
  leerForzarDisenoPlataforma,
  guardarForzarDisenoPlataforma,
} from './platforms/user-view-settings';
import { PlatformAccessPanel } from './platforms/platform-access-panel';
import { PlatformForm } from './platforms/platform-form';
import { PlatformGhostCard } from './platforms/platform-ghost-card';
import { describeDeleteError } from './platforms/platform-save-errors';
import { RequireRole } from './require-role';
import { useSession } from './session-provider';
import { useToast } from './toast';
import { EmptyNote, ErrorNote } from './ui';
import { eliminarEnLote, mensajeLoteParcial } from '@/lib/eliminar-en-lote';

const CLASES_COLS: Record<number, string> = {
  2: 'sm:grid-cols-2 lg:grid-cols-2',
  3: 'sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-3',
};

// Filas que llenan el alto disponible sin bajar del mínimo de la tarjeta (14rem = `min-h-56`):
// si no caben, el contenedor hace scroll en vez de encimar las tarjetas (DIS-103).
const CLASES_ROWS: Record<number, string> = {
  2: 'sm:grid-rows-[repeat(2,minmax(14rem,1fr))]',
  3: 'sm:grid-rows-[repeat(3,minmax(14rem,1fr))]',
};

/** Cuadrículas que ofrece la pantalla (filas × columnas). Con 4 filas o 4 columnas la tarjeta
 *  se deformaba: el dueño dejó solo estas (DIS-103) y agregó 2×2 (DIS-111). */
export const CUADRICULAS: ReadonlyArray<{ f: number; c: number }> = [
  { f: 2, c: 2 },
  { f: 2, c: 3 },
  { f: 3, c: 2 },
  { f: 3, c: 3 },
];
const CUADRICULA_POR_OMISION = { f: 2, c: 3 };

function cuadriculaValida(f: number, c: number): boolean {
  return CUADRICULAS.some((x) => x.f === f && x.c === c);
}

export const CLAVE_GRID_FILAS = 'portal_grid_filas';
export const CLAVE_GRID_COLUMNAS = 'portal_grid_columnas';

export function leerDimGrid(clave: string, def: number): number {
  if (typeof window === 'undefined') return def;
  try {
    const val = parseInt(window.localStorage.getItem(clave) ?? '', 10);
    return !Number.isNaN(val) && val >= 2 && val <= 4 ? val : def;
  } catch {
    return def;
  }
}

export function guardarDimGrid(clave: string, valor: number): void {
  try {
    window.localStorage.setItem(clave, String(valor));
  } catch {
    /* almacenamiento bloqueado */
  }
}

export function PlatformAdmin({ initialAreaId }: { initialAreaId?: number | null } = {}) {
  return (
    <RequireRole requires="any_admin">
      <PlatformAdminContent initialAreaId={initialAreaId} />
    </RequireRole>
  );
}

function PlatformAdminContent({ initialAreaId }: { initialAreaId?: number | null }) {
  const { session } = useSession();
  const isSuperadmin = Boolean(session?.permissions.is_admin);
  const managedAreaIds = useMemo(
    () => new Set((session?.managed_areas ?? []).map((a) => a.id)),
    [session?.managed_areas],
  );
  const { avisar } = useToast();
  const areas = useAsync(() => api.areas(), [], 'admin-areas');
  const platforms = useAsync(() => api.platforms(), [], 'admin-platforms');
  const [selectedAreaId, setSelectedAreaId] = useState<number | null>(initialAreaId ?? null);
  const [editing, setEditing] = useState<Platform | null>(null);
  const [creating, setCreating] = useState(false);
  const [removing, setRemoving] = useState<Platform[] | null>(null);
  const [managingAccess, setManagingAccess] = useState<Platform | null>(null);
  const [busy, setBusy] = useState(false);

  // Estados para gestión del área activa (Accesos, Editar, Eliminar)
  const [editingArea, setEditingArea] = useState<Area | null>(null);
  const [assigningArea, setAssigningArea] = useState<Area | null>(null);
  const [removingArea, setRemovingArea] = useState<Area | null>(null);
  const [busyRemovingArea, setBusyRemovingArea] = useState(false);

  // Sincronizar con el location bar y navegación del navegador manteniendo la URL limpia
  function handleSelectArea(area: Area) {
    setSelectedAreaId(area.id);
    setBusquedaPlataformas('');
    setPagePlataformas(1);
    setSelectedPlatformIds(new Set());
    if (typeof window !== 'undefined') {
      try {
        sessionStorage.setItem('portal_selected_area_id', String(area.id));
        sessionStorage.setItem('portal_selected_area_name', area.name);
      } catch {}
      // Mantener la barra de direcciones limpia sin query params (?area=...&area_name=...)
      window.history.pushState({ areaId: area.id, areaName: area.name }, '', window.location.pathname);
      window.dispatchEvent(new Event('popstate'));
    }
  }

  function handleBackToAreas() {
    setSelectedAreaId(null);
    setBusquedaPlataformas('');
    setPagePlataformas(1);
    setSelectedPlatformIds(new Set());
    if (typeof window !== 'undefined') {
      try {
        sessionStorage.removeItem('portal_selected_area_id');
        sessionStorage.removeItem('portal_selected_area_name');
      } catch {}
      // Mantener la barra de direcciones limpia sin query params
      window.history.pushState({ areaId: null, areaName: null }, '', window.location.pathname);
      window.dispatchEvent(new Event('popstate'));
    }
  }

  useEffect(() => {
    if (typeof window === 'undefined') return;

    // Si la URL venía con parámetros de consulta residuales (?area=...&area_name=...), capturar y limpiar
    const sp = new URLSearchParams(window.location.search);
    const aId = sp.get('area');
    if (aId) {
      const parsedId = Number(aId);
      if (initialAreaId === undefined && selectedAreaId === null) {
        setSelectedAreaId(parsedId);
      }
      try {
        sessionStorage.setItem('portal_selected_area_id', String(parsedId));
        if (sp.get('area_name')) {
          sessionStorage.setItem('portal_selected_area_name', sp.get('area_name') || '');
        }
      } catch {}
      // Limpiar inmediatamente la barra de direcciones para ocultar el query string
      window.history.replaceState(
        { areaId: parsedId, areaName: sp.get('area_name') || '' },
        '',
        window.location.pathname,
      );
    } else if (initialAreaId === undefined && selectedAreaId === null) {
      const stateId = (window.history.state as { areaId?: number | null })?.areaId;
      if (typeof stateId === 'number') {
        setSelectedAreaId(stateId);
      }
    }

    function onPopState(e: PopStateEvent) {
      const stateId = (e.state as { areaId?: number | null })?.areaId ?? (window.history.state as { areaId?: number | null })?.areaId;
      if (typeof stateId === 'number' || stateId === null) {
        setSelectedAreaId(stateId);
      } else {
        setSelectedAreaId(null);
      }
    }
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  // Intencional: `selectedAreaId` solo se lee como «aún sin área» al montar o cambiar
  // `initialAreaId`. Agregarlo reejecutaría la lectura de la URL/historial al volver a la lista
  // (`null`) y restauraría el área recién cerrada.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialAreaId]);

  // Búsqueda y paginación para Áreas (Sección 1)
  const [busquedaAreas, setBusquedaAreas] = useState('');
  const [pageAreas, setPageAreas] = useState(1);

  // Filtro de estado para Áreas (Sección 1): todos | activo | inactivo
  const [filtroEstado, setFiltroEstado] = useState<'todos' | 'activo' | 'inactivo'>('todos');
  const [menuEstadoAbierto, setMenuEstadoAbierto] = useState(false);
  const estadoRef = useRef<HTMLDivElement>(null);

  // Configuración de dimensiones de Cuadrícula (Sección 1): 2..4 filas x 2..4 columnas (persistido en navegador)
  // Una combinación guardada que ya no se ofrece (p. ej. 2×4) vuelve a la de por omisión.
  const [cuadricula, setCuadricula] = useState(() => {
    const f = leerDimGrid(CLAVE_GRID_FILAS, CUADRICULA_POR_OMISION.f);
    const c = leerDimGrid(CLAVE_GRID_COLUMNAS, CUADRICULA_POR_OMISION.c);
    return cuadriculaValida(f, c) ? { f, c } : CUADRICULA_POR_OMISION;
  });
  const gridFilas = cuadricula.f;
  const gridColumnas = cuadricula.c;
  const [menuGridAbierto, setMenuGridAbierto] = useState(false);
  const gridRef = useRef<HTMLDivElement>(null);

  const actualizarGridPreset = useCallback((f: number, c: number) => {
    setCuadricula({ f, c });
    setPageAreas(1);
    guardarDimGrid(CLAVE_GRID_FILAS, f);
    guardarDimGrid(CLAVE_GRID_COLUMNAS, c);
  }, []);

  // Configuración de diseño de tarjetas de área (Drawer lateral)
  const [disenoCardsArea, setDisenoCardsArea] = useState<AreaCardDesignVariant>(() => {
    if (typeof window !== 'undefined') {
      try {
        const val = window.localStorage.getItem(CLAVE_DISENO_CARDS_AREA) as AreaCardDesignVariant;
        if (
          val === 'split' ||
          val === 'onda' ||
          val === 'directorio' ||
          val === 'bento' ||
          val === 'medallon' ||
          val === 'estandar' ||
          val === 'portada' ||
          val === 'banner' ||
          val === 'glass' ||
          val === 'flotante'
        ) {
          return val;
        }
      } catch {}
    }
    return 'estandar';
  });
  const [drawerDisenoAbierto, setDrawerDisenoAbierto] = useState(false);
  const botonDisenoRef = useRef<HTMLButtonElement>(null);
  const [forzarDisenoArea, setForzarDisenoArea] = useState<boolean>(() => leerForzarDisenoArea());

  const handleDisenoCardsAreaChange = useCallback((nuevo: AreaCardDesignVariant) => {
    setDisenoCardsArea(nuevo);
    if (typeof window !== 'undefined') {
      try {
        window.localStorage.setItem(CLAVE_DISENO_CARDS_AREA, nuevo);
      } catch {}
    }
  }, []);

  const handleForzarDisenoAreaChange = useCallback((forzar: boolean) => {
    setForzarDisenoArea(forzar);
    guardarForzarDisenoArea(forzar);
  }, []);

  // Configuración de diseño de tarjetas de plataforma (Drawer lateral en Sección 2)
  const [disenoCardsPlataforma, setDisenoCardsPlataforma] = useState<CardDesignVariant>(() => {
    if (typeof window !== 'undefined') {
      try {
        const val = window.localStorage.getItem(CLAVE_DISENO_CARDS) as CardDesignVariant;
        if (
          val === 'duotono' ||
          val === 'enmarcada' ||
          val === 'split' ||
          val === 'glass' ||
          val === 'editorial' ||
          val === 'estandar' ||
          val === 'compacta' ||
          val === 'horizontal' ||
          val === 'banner' ||
          val === 'flotante'
        ) {
          return val;
        }
      } catch {}
    }
    return 'estandar';
  });
  const [drawerDisenoPlataformaAbierto, setDrawerDisenoPlataformaAbierto] = useState(false);
  const botonDisenoPlataformaRef = useRef<HTMLButtonElement>(null);
  const [forzarDisenoPlataforma, setForzarDisenoPlataforma] = useState<boolean>(() => leerForzarDisenoPlataforma());

  const handleDisenoCardsPlataformaChange = useCallback((nuevo: CardDesignVariant) => {
    setDisenoCardsPlataforma(nuevo);
    if (typeof window !== 'undefined') {
      try {
        window.localStorage.setItem(CLAVE_DISENO_CARDS, nuevo);
      } catch {}
    }
  }, []);

  const handleForzarDisenoPlataformaChange = useCallback((forzar: boolean) => {
    setForzarDisenoPlataforma(forzar);
    guardarForzarDisenoPlataforma(forzar);
  }, []);

  // Cerrar menús con click fuera o Escape
  useEffect(() => {
    if (!menuEstadoAbierto && !menuGridAbierto) return;
    function handleClickOutside(e: MouseEvent) {
      const target = e.target as Node;
      if (menuEstadoAbierto && estadoRef.current && !estadoRef.current.contains(target)) {
        setMenuEstadoAbierto(false);
      }
      if (menuGridAbierto && gridRef.current && !gridRef.current.contains(target)) {
        setMenuGridAbierto(false);
      }
    }
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        setMenuEstadoAbierto(false);
        setMenuGridAbierto(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [menuEstadoAbierto, menuGridAbierto]);

  const AREAS_PER_PAGE = gridFilas * gridColumnas;

  // Búsqueda y paginación para Plataformas (Sección 2)
  const [busquedaPlataformas, setBusquedaPlataformas] = useState('');
  const [pagePlataformas, setPagePlataformas] = useState(1);
  const PLATFORMS_PER_PAGE = 8;

  const selectedArea = useMemo(
    () => (areas.data ?? []).find((a) => a.id === selectedAreaId) ?? null,
    [areas.data, selectedAreaId],
  );

  const hasManagedAreasExplicit = Boolean(session?.managed_areas && session.managed_areas.length > 0);

  // Conteo reactivo de plataformas por área
  const conteoPorArea = useMemo(() => {
    const mapa: Record<number, number> = {};
    for (const p of platforms.data ?? []) {
      if (isSuperadmin || !hasManagedAreasExplicit || managedAreaIds.has(p.area_id)) {
        mapa[p.area_id] = (mapa[p.area_id] ?? 0) + 1;
      }
    }
    return mapa;
  }, [platforms.data, isSuperadmin, hasManagedAreasExplicit, managedAreaIds]);

  // DIS-102: plataformas del área (mismo alcance que el conteo) para los logos del pie de la tarjeta
  const plataformasPorArea = useMemo(() => {
    const mapa: Record<number, Platform[]> = {};
    for (const p of platforms.data ?? []) {
      if (isSuperadmin || !hasManagedAreasExplicit || managedAreaIds.has(p.area_id)) {
        (mapa[p.area_id] ??= []).push(p);
      }
    }
    return mapa;
  }, [platforms.data, isSuperadmin, hasManagedAreasExplicit, managedAreaIds]);

  // DIS-137: solicitudes por aprobar en cada área (FNC-212, mismo alcance que la bandeja). Si la
  // consulta falla, las tarjetas simplemente no muestran la cifra.
  const resumenSolicitudes = usePolling(() => requestsApi.inboxStats(), {
    intervalSeconds: session?.preferences?.refresh_interval,
  });
  const pendientesPorArea = useMemo(() => {
    const mapa: Record<number, number> = {};
    for (const fila of resumenSolicitudes.data?.pending_by_area ?? []) mapa[fila.area_id] = fila.count;
    return mapa;
  }, [resumenSolicitudes.data]);

  // Áreas gestionables según el rol (superadmin ve todas; admin de área solo las suyas)
  const assignableAreas = useMemo(() => {
    if (isSuperadmin || !hasManagedAreasExplicit) return areas.data ?? [];
    return (areas.data ?? []).filter((a) => managedAreaIds.has(a.id));
  }, [isSuperadmin, areas.data, hasManagedAreasExplicit, managedAreaIds]);

  // Áreas filtradas por estado y búsqueda de texto
  const areasFiltradas = useMemo(() => {
    let list = assignableAreas;
    if (filtroEstado === 'activo') {
      list = list.filter((a) => a.status === 'Activo');
    } else if (filtroEstado === 'inactivo') {
      list = list.filter((a) => a.status === 'Inactivo');
    }
    const q = busquedaAreas.trim().toLowerCase();
    if (q) {
      list = list.filter(
        (a) =>
          a.name.toLowerCase().includes(q) ||
          (a.description ?? '').toLowerCase().includes(q),
      );
    }
    return list;
  }, [assignableAreas, busquedaAreas, filtroEstado]);

  const totalAreasFiltradas = areasFiltradas.length;
  const totalPaginasAreas = Math.max(1, Math.ceil(totalAreasFiltradas / AREAS_PER_PAGE));
  const displayAreas = useMemo(() => {
    const start = (pageAreas - 1) * AREAS_PER_PAGE;
    return areasFiltradas.slice(start, start + AREAS_PER_PAGE);
  }, [areasFiltradas, pageAreas, AREAS_PER_PAGE]);
  // La rejilla ocupa todo el alto con filas fijas; los huecos completan la página (DIS-102, pedido del dueño).
  const ghostCountAreas = Math.max(0, AREAS_PER_PAGE - displayAreas.length);

  // Plataformas filtradas del área seleccionada (admin de área solo ve donde es admin)
  const plataformasFiltradas = useMemo(() => {
    if (!selectedArea) return [];
    if (!isSuperadmin && hasManagedAreasExplicit && !managedAreaIds.has(selectedArea.id)) return [];
    const list = (platforms.data ?? []).filter((p) => p.area_id === selectedArea.id);
    if (!busquedaPlataformas.trim()) return list;
    const q = busquedaPlataformas.toLowerCase().trim();
    return list.filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        (p.description ?? '').toLowerCase().includes(q),
    );
  }, [platforms.data, selectedArea, busquedaPlataformas, isSuperadmin, hasManagedAreasExplicit, managedAreaIds]);

  const totalPlataformas = plataformasFiltradas.length;
  const totalPaginasPlataformas = Math.max(1, Math.ceil(totalPlataformas / PLATFORMS_PER_PAGE));
  const displayPlataformas = useMemo(() => {
    const start = (pagePlataformas - 1) * PLATFORMS_PER_PAGE;
    return plataformasFiltradas.slice(start, start + PLATFORMS_PER_PAGE);
  }, [plataformasFiltradas, pagePlataformas]);

  // Selección de plataformas en tabla
  const [selectedPlatformIds, setSelectedPlatformIds] = useState<Set<number>>(new Set());

  const allDisplayPlatformIds = useMemo(() => displayPlataformas.map((p) => p.id), [displayPlataformas]);
  const activeSelectedPlatformIds = useMemo(
    () => new Set(Array.from(selectedPlatformIds).filter((id) => allDisplayPlatformIds.includes(id))),
    [selectedPlatformIds, allDisplayPlatformIds],
  );

  const allSelected =
    allDisplayPlatformIds.length > 0 &&
    allDisplayPlatformIds.every((id) => activeSelectedPlatformIds.has(id));
  const someSelected =
    allDisplayPlatformIds.some((id) => activeSelectedPlatformIds.has(id)) && !allSelected;

  function toggleSelectAllPlatforms() {
    if (allSelected) {
      setSelectedPlatformIds((prev) => {
        const next = new Set(prev);
        allDisplayPlatformIds.forEach((id) => next.delete(id));
        return next;
      });
    } else {
      setSelectedPlatformIds((prev) => {
        const next = new Set(prev);
        allDisplayPlatformIds.forEach((id) => next.add(id));
        return next;
      });
    }
  }

  function togglePlatform(id: number) {
    setSelectedPlatformIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  const isSinglePlatformSelected = activeSelectedPlatformIds.size === 1;
  const singleSelectedPlatformId = isSinglePlatformSelected
    ? Array.from(activeSelectedPlatformIds)[0]
    : null;
  const effectiveSelectedPlatform = singleSelectedPlatformId
    ? displayPlataformas.find((p) => p.id === singleSelectedPlatformId) ?? null
    : null;

  const selectedPlatforms = useMemo(() => {
    if (!platforms.data || activeSelectedPlatformIds.size === 0) return [];
    return platforms.data.filter((p) => activeSelectedPlatformIds.has(p.id));
  }, [platforms.data, activeSelectedPlatformIds]);

  // Foco: al cerrar un diálogo vuelve al disparador.
  const trigger = useRef<HTMLElement | null>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const [focusTarget, setFocusTarget] = useState<'trigger' | null>(null);
  const dialogOpen =
    creating ||
    editing !== null ||
    removing !== null ||
    managingAccess !== null ||
    editingArea !== null ||
    assigningArea !== null ||
    removingArea !== null;

  useEffect(() => {
    if (dialogOpen || !focusTarget) return;
    if (trigger.current?.isConnected) trigger.current.focus();
    else heading.current?.focus();
    setFocusTarget(null);
  }, [dialogOpen, focusTarget]);

  function open(event: React.MouseEvent<HTMLElement>, action: () => void) {
    trigger.current = event.currentTarget;
    action();
  }

  function closeDialogs() {
    setCreating(false);
    setEditing(null);
    setRemoving(null);
    setManagingAccess(null);
    setEditingArea(null);
    setAssigningArea(null);
    setRemovingArea(null);
    setFocusTarget('trigger');
  }

  // DIS-114: cambiar el estado de un área mueve el de sus plataformas (backend): se recargan ambas.
  function recargarTrasEstado() {
    areas.reload();
    platforms.reload();
  }

  async function handleDeleteArea() {
    if (!removingArea) return;
    const nombre = removingArea.name;
    setBusyRemovingArea(true);
    try {
      await api.deleteArea(removingArea.id);
      avisar('success', `"${nombre}" fue retirada.`, 'Área eliminada');
      setRemovingArea(null);
      handleBackToAreas();
      areas.reload();
      platforms.reload();
    } catch (err) {
      setRemovingArea(null);
      const msg = mensajeDeError(err, 'No se pudo eliminar el área');
      avisar('error', msg, 'Error');
    } finally {
      setBusyRemovingArea(false);
    }
  }

  const canManage =
    session?.permissions.is_admin || session?.permissions.is_area_admin;

  // `reload` cambia en cada render: las columnas (memoizadas) lo leen por referencia.
  const recargarPlataformas = useRef(platforms.reload);
  recargarPlataformas.current = platforms.reload;

  // Columnas de la tabla común (`DataTable`) con selección por checkbox inicial.
  const columnas = useMemo(
    () =>
      columnasPlataformas({
        selectedPlatformIds: activeSelectedPlatformIds,
        allSelected,
        someSelected,
        toggleSelectAll: toggleSelectAllPlatforms,
        togglePlatform,
        puedeEditarEstado: Boolean(session?.permissions.is_admin || session?.permissions.is_area_admin),
        actualizarEstado: (platform, status) => api.updatePlatform(platform.id, { status }),
        onEstadoCambiado: () => recargarPlataformas.current(),
      }),
    // `toggleSelectAllPlatforms` solo lee `allSelected` y `allDisplayPlatformIds` (ya en las
    // dependencias) y usa el setter funcional: no hay dato viejo; agregarla recrearía las
    // columnas en cada render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [activeSelectedPlatformIds, allSelected, someSelected, allDisplayPlatformIds, session?.permissions.is_admin, session?.permissions.is_area_admin],
  );

  async function remove() {
    if (!removing || removing.length === 0) return;
    setBusy(true);
    const count = removing.length;
    try {
      const { eliminados, error } = await eliminarEnLote(removing, (p) => api.deletePlatform(p.id));
      setSelectedPlatformIds((prev) => {
        const next = new Set(prev);
        eliminados.forEach((p) => next.delete(p.id));
        return next;
      });
      closeDialogs();
      if (error) {
        avisar('error', mensajeLoteParcial(eliminados.length, count, describeDeleteError(error)), 'Error');
      } else {
        avisar(
          'success',
          count === 1
            ? `"${removing[0].name}" fue retirada.`
            : `${count} plataformas fueron retiradas.`,
          count === 1 ? 'Plataforma eliminada' : 'Plataformas eliminadas',
        );
      }
      platforms.reload();
    } finally {
      setBusy(false);
    }
  }

  function handleSaved(result: { platform: Platform; warnings: PlatformWarning[] }) {
    setCreating(false);
    setEditing(null);
    setSelectedPlatformIds(new Set());
    const hasWarnings = (result.warnings ?? []).length > 0;
    const tone = hasWarnings ? 'warning' : 'success';
    const title = hasWarnings ? 'Guardada con avisos' : 'Guardada';
    const message = hasWarnings
      ? `Se guardó «${result.platform.name}» con avisos: ${result.warnings.map((w) => w.message).join(' ')}`
      : `Se guardó «${result.platform.name}».`;
    avisar(tone, message, title);
    setFocusTarget('trigger');
    platforms.reload();
  }

  // DIS-138: solo los enlaces escritos pero no válidos; sin enlace es «Omitir enlace».
  const missingLink = (platforms.data ?? []).filter((p) => !sinEnlaceWeb(p) && !enlaceSeguro(p.direct_link));

  return (
    <div className="flex h-full w-full flex-col gap-4 min-h-0">
      <PageHeader
        h1Ref={heading}
        title={selectedArea ? `Plataformas: ${selectedArea.name}` : 'Plataformas'}
      />
      {areas.error ? <ErrorNote message={areas.error} /> : null}
      {canManage && !areas.loading && !areas.error && (areas.data ?? []).length === 0 ? (
        <EmptyNote message="No hay áreas en tu alcance: da de alta un área antes de crear plataformas." />
      ) : null}

      <MissingLinkNote count={missingLink.length} />

      {/* SECCIÓN 1: VISTA PRINCIPAL DE ÁREAS (Grid 2 filas x 4 columnas) */}
      {!selectedArea ? (
        <div className="grid w-full flex-1 min-h-0 grid-cols-1 grid-rows-[auto_1fr] gap-4">
          {/* Fila 1: Barra de herramientas con Buscador de áreas y Botón Nuevo */}
          <div className="flex shrink-0 flex-wrap items-center justify-between gap-3 p-3.5 rounded-xl border border-panel-border/80 bg-gradient-to-r from-superficie via-superficie to-superficie-hundida shadow-1">
            {/* Buscador de áreas */}
            <div className="flex items-center gap-3 flex-1 min-w-0 max-w-xl">
              <div className="relative w-full">
                <label htmlFor="buscar-areas" className="sr-only">Buscar áreas</label>
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-label">
                  <Icono nombre="buscar" tamano="md" ariaHidden={true} />
                </div>
                <input
                  id="buscar-areas"
                  type="search"
                  placeholder="Buscar áreas…"
                  value={busquedaAreas}
                  onChange={(e) => {
                    setBusquedaAreas(e.target.value);
                    setPageAreas(1);
                  }}
                  aria-label="Buscar áreas"
                  className="nx-buscador-toolbar h-12 w-full rounded-xl border border-panel-border bg-fondo pl-11 pr-10 py-3 text-sm text-body-text placeholder:text-placeholder transition-all focus:border-primary focus:bg-superficie focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
                {busquedaAreas ? (
                  <button
                    type="button"
                    onClick={() => {
                      setBusquedaAreas('');
                      setPageAreas(1);
                    }}
                    className="absolute inset-y-0 right-0 flex items-center justify-center min-h-12 min-w-12 pr-3 text-label hover:text-body-text transition-colors"
                    aria-label="Limpiar búsqueda de áreas"
                  >
                    <Icono nombre="cerrar" tamano="sm" ariaHidden={true} />
                  </button>
                ) : null}
              </div>
            </div>

            {/* A la derecha: Botones de Diseño, Filtrar por estado y Configurar cuadrícula */}
            <div className="flex flex-wrap items-center gap-2.5">
              {/* Botón: Configurar diseño de tarjetas de área (a la izquierda de Filtrar por estado, simétrico w-48) */}
              <button
                ref={botonDisenoRef}
                type="button"
                onClick={() => setDrawerDisenoAbierto(true)}
                aria-label="Diseño: Configurar estilo de tarjetas de área"
                aria-haspopup="dialog"
                aria-expanded={drawerDisenoAbierto}
                className={`inline-flex h-12 min-h-12 w-48 min-w-48 items-center justify-between gap-2 rounded-xl border px-3.5 text-xs font-semibold shadow-xs transition-all duration-rapida cursor-pointer select-none focus:outline-none focus-visible:ring-2 focus-visible:ring-primary ${
                  drawerDisenoAbierto
                    ? 'border-primary bg-primary/10 text-primary-text ring-2 ring-primary/20 shadow-1'
                    : 'border-panel-border bg-fondo text-body-text hover:border-primary/50 hover:bg-superficie hover:shadow-1'
                }`}
              >
                <div className="flex items-center gap-2 min-w-0">
                  <Icono nombre="diseno" tamano="sm" ariaHidden={true} className="text-primary-text shrink-0" />
                  <span className="font-bold text-body-text">Diseño</span>
                </div>
                <Icono
                  nombre="chevron-der"
                  tamano="xs"
                  ariaHidden={true}
                  className={`shrink-0 transition-transform duration-rapida ${
                    drawerDisenoAbierto ? 'translate-x-0.5 text-primary-text' : 'text-label'
                  }`}
                />
              </button>

              {/* Botón 1: Filtrar por estado */}
              <div ref={estadoRef} className="relative">
                <button
                  type="button"
                  onClick={() => {
                    setMenuEstadoAbierto((prev) => !prev);
                    setMenuGridAbierto(false);
                  }}
                  aria-haspopup="listbox"
                  aria-expanded={menuEstadoAbierto}
                  aria-label={`Filtrar por estado: actual ${filtroEstado}`}
                  className={`inline-flex h-12 min-h-12 w-48 min-w-48 items-center justify-between gap-2 rounded-xl border px-3.5 text-xs font-semibold shadow-xs transition-all duration-rapida cursor-pointer select-none focus:outline-none focus-visible:ring-2 focus-visible:ring-primary ${
                    menuEstadoAbierto
                      ? 'border-primary bg-primary/10 text-primary-text ring-2 ring-primary/20 shadow-1'
                      : filtroEstado !== 'todos'
                      ? 'border-primary/60 bg-superficie text-primary-text hover:border-primary hover:bg-superficie/80 hover:shadow-1'
                      : 'border-panel-border bg-fondo text-body-text hover:border-primary/50 hover:bg-superficie hover:shadow-1'
                  }`}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <Icono nombre="inventario" tamano="sm" ariaHidden={true} className="text-primary-text shrink-0" />
                    <span className="flex items-center gap-1.5 whitespace-nowrap">
                      <span className="text-label font-medium">Estado:</span>
                      <span className="font-bold text-body-text">
                        {filtroEstado === 'todos'
                          ? 'Todos'
                          : filtroEstado === 'activo'
                          ? 'Activas'
                          : 'Inactivas'}
                      </span>
                      {filtroEstado === 'activo' ? (
                        <span className="size-1.5 rounded-full bg-success shrink-0" />
                      ) : filtroEstado === 'inactivo' ? (
                        <span className="size-1.5 rounded-full bg-warning shrink-0" />
                      ) : null}
                    </span>
                  </div>
                  <Icono
                    nombre="chevron-abajo"
                    tamano="xs"
                    ariaHidden={true}
                    className={`shrink-0 transition-transform duration-rapida ${
                      menuEstadoAbierto ? 'rotate-180 text-primary-text' : 'text-label'
                    }`}
                  />
                </button>

                {menuEstadoAbierto ? (
                  <div
                    role="listbox"
                    aria-label="Opciones de estado"
                    className="absolute right-0 top-full mt-1.5 z-50 w-48 rounded-xl border border-panel-border bg-panel-fill p-1.5 shadow-2 backdrop-blur-md"
                  >
                    <button
                      type="button"
                      role="option"
                      aria-selected={filtroEstado === 'todos'}
                      onClick={() => {
                        setFiltroEstado('todos');
                        setPageAreas(1);
                        setMenuEstadoAbierto(false);
                      }}
                      className={`flex w-full min-h-12 items-center justify-between rounded-lg px-3 py-2 text-xs font-semibold transition-colors ${
                        filtroEstado === 'todos'
                          ? 'bg-primary/15 text-primary-text font-bold'
                          : 'text-body-text hover:bg-surface-container'
                      }`}
                    >
                      <span>Todos</span>
                      {filtroEstado === 'todos' ? <Icono nombre="aprobar" tamano="sm" /> : null}
                    </button>
                    <button
                      type="button"
                      role="option"
                      aria-selected={filtroEstado === 'activo'}
                      onClick={() => {
                        setFiltroEstado('activo');
                        setPageAreas(1);
                        setMenuEstadoAbierto(false);
                      }}
                      className={`flex w-full min-h-12 items-center justify-between rounded-lg px-3 py-2 text-xs font-semibold transition-colors ${
                        filtroEstado === 'activo'
                          ? 'bg-primary/15 text-primary-text font-bold'
                          : 'text-body-text hover:bg-surface-container'
                      }`}
                    >
                      <span className="flex items-center gap-1.5">
                        <span className="size-2 rounded-full bg-success" />
                        <span>Activas</span>
                      </span>
                      {filtroEstado === 'activo' ? <Icono nombre="aprobar" tamano="sm" /> : null}
                    </button>
                    <button
                      type="button"
                      role="option"
                      aria-selected={filtroEstado === 'inactivo'}
                      onClick={() => {
                        setFiltroEstado('inactivo');
                        setPageAreas(1);
                        setMenuEstadoAbierto(false);
                      }}
                      className={`flex w-full min-h-12 items-center justify-between rounded-lg px-3 py-2 text-xs font-semibold transition-colors ${
                        filtroEstado === 'inactivo'
                          ? 'bg-primary/15 text-primary-text font-bold'
                          : 'text-body-text hover:bg-surface-container'
                      }`}
                    >
                      <span className="flex items-center gap-1.5">
                        <span className="size-2 rounded-full bg-warning" />
                        <span>Inactivas</span>
                      </span>
                      {filtroEstado === 'inactivo' ? <Icono nombre="aprobar" tamano="sm" /> : null}
                    </button>
                  </div>
                ) : null}
              </div>

              {/* Botón 2: Configurar cuadrícula (2..4 filas x 2..4 columnas) */}
              <div ref={gridRef} className="relative">
                <button
                  type="button"
                  onClick={() => {
                    setMenuGridAbierto((prev) => !prev);
                    setMenuEstadoAbierto(false);
                  }}
                  aria-haspopup="true"
                  aria-expanded={menuGridAbierto}
                  aria-label={`Configurar cuadrícula: ${gridFilas} filas por ${gridColumnas} columnas`}
                  title="Configurar cuadrícula"
                  className={`inline-flex h-12 min-h-12 w-48 min-w-48 items-center justify-between gap-2 rounded-xl border px-3.5 text-xs font-semibold shadow-xs transition-all duration-rapida cursor-pointer select-none focus:outline-none focus-visible:ring-2 focus-visible:ring-primary ${
                    menuGridAbierto
                      ? 'border-primary bg-primary/10 text-primary-text ring-2 ring-primary/20 shadow-1'
                      : 'border-panel-border bg-fondo text-body-text hover:border-primary/50 hover:bg-superficie hover:shadow-1'
                  }`}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <Icono nombre="panel" tamano="sm" ariaHidden={true} className="text-primary-text shrink-0" />
                    <span className="flex items-center gap-1.5 whitespace-nowrap">
                      <span className="text-label font-medium">Cuadrícula:</span>
                      <span className="font-bold text-body-text tabular-nums">{gridFilas}×{gridColumnas}</span>
                    </span>
                  </div>
                  <Icono
                    nombre="chevron-abajo"
                    tamano="xs"
                    ariaHidden={true}
                    className={`shrink-0 transition-transform duration-rapida ${
                      menuGridAbierto ? 'rotate-180 text-primary-text' : 'text-label'
                    }`}
                  />
                </button>

                {menuGridAbierto ? (
                  <div
                    role="region"
                    aria-label="Configurar cuadrícula"
                    className="absolute right-0 top-full mt-1.5 z-50 w-72 rounded-xl border border-panel-border bg-panel-fill p-3 shadow-2 backdrop-blur-md space-y-3"
                  >
                    <div className="flex items-center justify-between border-b border-panel-border/50 pb-2">
                      <span className="text-xs font-bold uppercase tracking-wider text-label">
                        Cuadrícula
                      </span>
                      <span className="text-xs font-bold text-primary-text tabular-nums">
                        {gridFilas * gridColumnas} slots ({gridFilas}×{gridColumnas})
                      </span>
                    </div>

                    {/* Combinaciones (filas × columnas) */}
                    <div>
                      <div className="grid grid-cols-2 gap-1.5">
                        {CUADRICULAS.map((x) => ({ ...x, l: `${x.f}×${x.c}` })).map((p) => (
                          <button
                            key={p.l}
                            type="button"
                            onClick={() => actualizarGridPreset(p.f, p.c)}
                            className={`flex min-h-12 items-center justify-center px-3 text-xs font-semibold rounded-lg transition-colors ${
                              gridFilas === p.f && gridColumnas === p.c
                                ? 'bg-primary/20 text-primary-text font-bold'
                                : 'text-label hover:text-body-text hover:bg-superficie-hundida'
                            }`}
                          >
                            {p.l}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : null}
              </div>
            </div>
          </div>

          {/* Fila 2: Body con Grid configurable */}
          <div className="flex flex-1 min-h-0 flex-col w-full overflow-y-auto p-1">
            {areas.loading && !areas.data ? (
              <div
                className={`grid grid-cols-1 ${CLASES_COLS[gridColumnas] ?? 'lg:grid-cols-3'} ${
                  CLASES_ROWS[gridFilas] ?? 'lg:grid-rows-2'
                } gap-4 flex-1`}
              >
                {Array.from({ length: AREAS_PER_PAGE }).map((_, i) => (
                  <div key={i} className="min-h-56 h-full rounded-xl border border-panel-border/60 bg-panel-fill p-5 animate-pulse" />
                ))}
              </div>
            ) : null}

            {areas.data && displayAreas.length === 0 ? (
              <div className="flex-1 flex items-center justify-center h-full">
                <EmptyNote
                  icono="areas"
                  message={
                    busquedaAreas.trim() || filtroEstado !== 'todos'
                      ? 'No hay áreas que coincidan con los filtros aplicados.'
                      : 'No hay áreas en tu alcance.'
                  }
                  action={
                    busquedaAreas.trim() || filtroEstado !== 'todos' ? (
                      <Button
                        variant="secondary"
                        onClick={() => {
                          setBusquedaAreas('');
                          setFiltroEstado('todos');
                          setPageAreas(1);
                        }}
                      >
                        Limpiar filtros
                      </Button>
                    ) : null
                  }
                />
              </div>
            ) : null}

            {displayAreas.length > 0 ? (
              <div className="flex flex-col flex-1 w-full justify-between gap-4 h-full">
                {/* Grid configurable: filas fijas que ocupan todo el alto; la tarjeta se reparte (DIS-102) */}
                <div
                  role="region"
                  aria-label="Catálogo de áreas"
                  className={`grid grid-cols-1 ${CLASES_COLS[gridColumnas] ?? 'lg:grid-cols-3'} ${
                    CLASES_ROWS[gridFilas] ?? 'sm:grid-rows-[repeat(2,minmax(14rem,1fr))]'
                  } gap-4 flex-1 h-full`}
                >
                  {displayAreas.map((area) => (
                    <TarjetaArea
                      key={area.id}
                      area={area}
                      conteo={conteoPorArea[area.id] ?? 0}
                      plataformas={plataformasPorArea[area.id] ?? []}
                      pendientes={resumenSolicitudes.data ? (pendientesPorArea[area.id] ?? 0) : undefined}
                      mostrarAdministradores
                      onSelect={handleSelectArea}
                      puedeEditar={isSuperadmin || managedAreaIds.has(area.id)}
                      actualizarEstado={(status) => api.updateArea(area.id, { status })}
                      onEstadoCambiado={recargarTrasEstado}
                      variante={disenoCardsArea}
                    />
                  ))}

                  {/* Huecos que completan solo la última fila (en escritorio); las filas vacías ya no se dibujan */}
                  {Array.from({ length: ghostCountAreas }).map((_, idx) => (
                    <PlatformGhostCard
                      key={`ghost-area-${idx}`}
                      icono="areas"
                      texto="Espacio disponible"
                    />
                  ))}
                </div>

                {/* Paginación si hay más de 8 áreas (2x4) */}
                {totalPaginasAreas > 1 ? (
                  <div className="flex shrink-0 items-center justify-between border border-panel-border/80 bg-superficie/90 px-4 py-2.5 rounded-xl shadow-xs text-xs">
                    <span className="font-semibold tabular-nums text-label">
                      {areasFiltradas.length} áreas registradas
                    </span>
                    <CapsulePager
                      page={pageAreas}
                      totalPages={totalPaginasAreas}
                      onChange={setPageAreas}
                      label="Paginación de áreas"
                      ariaLabelAnterior="Página anterior de áreas"
                      ariaLabelSiguiente="Página siguiente de áreas"
                    />
                  </div>
                ) : null}
              </div>
            ) : null}
          </div>
        </div>
      ) : (
        /* SECCIÓN 2: VISTA DE PLATAFORMAS DEL ÁREA SELECCIONADA */
        <div className="grid w-full flex-1 min-h-0 grid-cols-1 grid-rows-[auto_1fr] gap-4">
          {/* Fila 1: Barra de herramientas con Botón Volver, Buscador, Texto del área, y Botones de acción */}
          <div className="flex shrink-0 flex-wrap items-center justify-between gap-3 p-3.5 rounded-xl border border-panel-border/80 bg-gradient-to-r from-superficie via-superficie to-superficie-hundida shadow-1">
            <div className="flex items-center gap-3 flex-1 min-w-0 max-w-3xl">
              {/* Botón Volver a áreas */}
              <Button
                variant="fila"
                onClick={handleBackToAreas}
                aria-label="Volver a áreas"
                title="Volver a áreas"
                className="nx-btn-toolbar !px-3 inline-flex items-center gap-1.5 text-xs font-bold whitespace-nowrap shadow-xs"
              >
                <Icono nombre="chevron-izq" tamano="sm" ariaHidden={true} />
                <span>Áreas</span>
              </Button>

              {/* Buscador de plataformas dentro del área */}
              <div className="relative w-full max-w-md">
                <label htmlFor="buscar-plataformas" className="sr-only">
                  Buscar plataformas en {selectedArea.name}
                </label>
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-label">
                  <Icono nombre="buscar" tamano="md" ariaHidden={true} />
                </div>
                <input
                  id="buscar-plataformas"
                  type="search"
                  placeholder={`Buscar plataformas en ${selectedArea.name}…`}
                  value={busquedaPlataformas}
                  onChange={(e) => {
                    setBusquedaPlataformas(e.target.value);
                    setPagePlataformas(1);
                  }}
                  aria-label={`Buscar plataformas en ${selectedArea.name}`}
                  className="nx-buscador-toolbar h-12 w-full rounded-xl border border-panel-border bg-fondo pl-11 pr-10 py-3 text-sm text-body-text placeholder:text-placeholder transition-all focus:border-primary focus:bg-superficie focus:outline-none focus:ring-2 focus:ring-primary/20"
                />
                {busquedaPlataformas ? (
                  <button
                    type="button"
                    onClick={() => {
                      setBusquedaPlataformas('');
                      setPagePlataformas(1);
                    }}
                    className="absolute inset-y-0 right-0 flex items-center justify-center min-h-12 min-w-12 pr-3 text-label hover:text-body-text transition-colors"
                    aria-label="Limpiar búsqueda"
                  >
                    <Icono nombre="cerrar" tamano="sm" ariaHidden={true} />
                  </button>
                ) : null}
              </div>

              {activeSelectedPlatformIds.size > 1 ? (
                <span className="text-xs font-bold text-body-text whitespace-nowrap bg-panel-border/30 px-2.5 py-1 rounded-lg border border-panel-border/60">
                  {activeSelectedPlatformIds.size} plataformas seleccionadas
                </span>
              ) : null}
            </div>

            {/* A la derecha: Botones de Diseño, Accesos, Editar, Eliminar y Nueva plataforma */}
            <div className="flex flex-wrap items-center gap-2">
              {/* Botón Diseño de plataformas (Drawer lateral con vista previa en vivo) */}
              {canManage ? (
                <Button
                  ref={botonDisenoPlataformaRef}
                  variant="fila"
                  type="button"
                  onClick={() => setDrawerDisenoPlataformaAbierto(true)}
                  aria-label="Diseño"
                  title="Configurar diseño de tarjetas de plataforma"
                  className={`nx-btn-toolbar !px-2.5 inline-flex items-center justify-center gap-1.5 text-xs font-bold whitespace-nowrap shadow-xs ${
                    drawerDisenoPlataformaAbierto
                      ? 'border-primary bg-primary/10 text-primary-text ring-2 ring-primary/20'
                      : ''
                  }`}
                >
                  <Icono nombre="diseno" tamano="sm" ariaHidden={true} />
                  <span>Diseño</span>
                </Button>
              ) : null}

              {/* Botón Accesos (Gestionar accesos a la plataforma seleccionada) */}
              {canManage ? (
                <Button
                  variant="fila"
                  disabled={!isSinglePlatformSelected}
                  motivoDeshabilitado={
                    activeSelectedPlatformIds.size > 1
                      ? 'Solo se pueden gestionar accesos de 1 plataforma a la vez'
                      : 'Selecciona 1 plataforma para gestionar accesos'
                  }
                  onClick={(e) => {
                    if (effectiveSelectedPlatform) {
                      open(e, () => setManagingAccess(effectiveSelectedPlatform));
                    }
                  }}
                  aria-label={
                    effectiveSelectedPlatform
                      ? `Accesos de ${effectiveSelectedPlatform.name}`
                      : 'Accesos'
                  }
                  title={
                    isSinglePlatformSelected
                      ? `Accesos de ${effectiveSelectedPlatform?.name}`
                      : activeSelectedPlatformIds.size > 1
                      ? 'Solo se pueden gestionar accesos de 1 plataforma a la vez'
                      : 'Selecciona 1 plataforma para gestionar accesos'
                  }
                  className="nx-btn-toolbar !px-2.5 inline-flex items-center justify-center gap-1.5 text-xs font-bold whitespace-nowrap shadow-xs"
                >
                  <Icono nombre="solicitudes" tamano="sm" ariaHidden={true} />
                  <span>Accesos</span>
                </Button>
              ) : null}

              {/* Botón Editar plataforma */}
              {canManage ? (
                <Button
                  variant="fila"
                  disabled={!isSinglePlatformSelected}
                  motivoDeshabilitado={
                    activeSelectedPlatformIds.size > 1
                      ? 'Solo se puede editar 1 plataforma a la vez'
                      : 'Selecciona 1 plataforma para editar'
                  }
                  onClick={(e) => {
                    if (effectiveSelectedPlatform) {
                      open(e, () => setEditing(effectiveSelectedPlatform));
                    }
                  }}
                  aria-label={
                    effectiveSelectedPlatform
                      ? `Editar ${effectiveSelectedPlatform.name}`
                      : 'Editar'
                  }
                  title={
                    isSinglePlatformSelected
                      ? `Editar ${effectiveSelectedPlatform?.name}`
                      : activeSelectedPlatformIds.size > 1
                      ? 'Solo se puede editar 1 plataforma a la vez'
                      : 'Selecciona 1 plataforma para editar'
                  }
                  className="nx-btn-toolbar !px-2.5 inline-flex items-center justify-center gap-1.5 text-xs font-bold whitespace-nowrap shadow-xs"
                >
                  <Icono nombre="editar" tamano="sm" ariaHidden={true} />
                  <span>Editar</span>
                </Button>
              ) : null}

              {/* Botón Eliminar plataforma */}
              {canManage ? (
                <Button
                  variant="fila-peligro"
                  disabled={activeSelectedPlatformIds.size === 0}
                  motivoDeshabilitado="Selecciona al menos 1 plataforma para eliminar"
                  onClick={(e) => {
                    if (selectedPlatforms.length > 0) {
                      open(e, () => setRemoving(selectedPlatforms));
                    }
                  }}
                  aria-label={
                    activeSelectedPlatformIds.size === 1
                      ? `Eliminar ${selectedPlatforms[0]?.name}`
                      : activeSelectedPlatformIds.size > 1
                      ? `Eliminar ${activeSelectedPlatformIds.size} plataformas seleccionadas`
                      : 'Eliminar'
                  }
                  title={
                    activeSelectedPlatformIds.size === 1
                      ? `Eliminar ${selectedPlatforms[0]?.name}`
                      : activeSelectedPlatformIds.size > 1
                      ? `Eliminar ${activeSelectedPlatformIds.size} plataformas seleccionadas`
                      : 'Selecciona al menos 1 plataforma para eliminar'
                  }
                  className="nx-btn-toolbar !px-2.5 inline-flex items-center justify-center gap-1.5 text-xs font-bold whitespace-nowrap shadow-xs"
                >
                  <Icono nombre="eliminar" tamano="sm" ariaHidden={true} />
                  <span>Eliminar</span>
                </Button>
              ) : null}

              {/* Separador vertical antes del botón Nuevo */}
              {canManage ? (
                <div className="h-6 w-px bg-panel-border/80 self-center mx-1 shrink-0" aria-hidden="true" />
              ) : null}

              {/* Botón Nueva plataforma */}
              {canManage ? (
                <Button
                  variant="fila-primario"
                  onClick={(e) => open(e, () => setCreating(true))}
                  disabled={areas.loading || (areas.data ?? []).length === 0}
                  aria-label="Nuevo"
                  title="Nuevo"
                  className="nx-btn-toolbar !px-2.5 inline-flex items-center justify-center gap-1.5 text-xs font-bold whitespace-nowrap shadow-xs"
                >
                  <Icono nombre="mas" tamano="sm" ariaHidden={true} />
                  <span>Nuevo</span>
                </Button>
              ) : null}
            </div>
          </div>

          {/* Fila 2: Tabla de plataformas del área seleccionada */}
          <div className="flex flex-1 min-h-0 flex-col h-full w-full overflow-hidden">
            <DataTable
              label={`Plataformas de ${selectedArea.name}`}
              columns={columnas}
              rows={displayPlataformas}
              rowKey={(platform) => platform.id}
              loading={platforms.loading || areas.loading}
              error={platforms.error}
              emptyTitle={
                busquedaPlataformas.trim()
                  ? 'No se encontraron plataformas'
                  : `Sin plataformas en ${selectedArea.name}`
              }
              emptyMessage={
                busquedaPlataformas.trim()
                  ? `No hay plataformas que coincidan con «${busquedaPlataformas.trim()}» en esta área.`
                  : `No hay plataformas registradas en el área «${selectedArea.name}».`
              }
              emptyIcon="plataformas"
              emptyAction={
                busquedaPlataformas.trim() ? (
                  <Button
                    variant="fila"
                    onClick={() => {
                      setBusquedaPlataformas('');
                      setPagePlataformas(1);
                    }}
                    className="nx-btn-toolbar !w-auto !px-4"
                  >
                    <Icono nombre="cerrar" tamano="sm" ariaHidden={true} />
                    <span>Limpiar búsqueda</span>
                  </Button>
                ) : canManage ? (
                  <Button
                    variant="fila-primario"
                    onClick={(e) => open(e, () => setCreating(true))}
                    className="nx-btn-toolbar !w-auto !px-4"
                  >
                    <Icono nombre="mas" tamano="sm" ariaHidden={true} />
                    <span>Crear primera plataforma</span>
                  </Button>
                ) : null
              }
              page={pagePlataformas}
              totalPages={totalPaginasPlataformas}
              totalRecords={totalPlataformas}
              onPageChange={(p) => setPagePlataformas(p)}
              selectedKeys={activeSelectedPlatformIds}
              onRowClick={(platform) => togglePlatform(platform.id)}
              ghostRows
            />
          </div>
        </div>
      )}

      {creating ? (
        <PlatformForm
          areas={assignableAreas}
          platform={null}
          defaultAreaId={selectedArea?.id}
          isSuperadmin={isSuperadmin}
          onClose={closeDialogs}
          onSaved={handleSaved}
        />
      ) : null}

      {editing ? (
        <PlatformForm
          areas={assignableAreas}
          platform={editing}
          isSuperadmin={isSuperadmin}
          onClose={closeDialogs}
          onSaved={handleSaved}
        />
      ) : null}

      {removing ? (
        <ConfirmDialog
          title={removing.length === 1 ? 'Eliminar plataforma' : 'Eliminar plataformas'}
          message={
            removing.length === 1
              ? `Se eliminará "${removing[0].name}". Esta acción no se puede deshacer.`
              : `Se eliminarán las ${removing.length} plataformas seleccionadas. Esta acción no se puede deshacer.`
          }
          onConfirm={remove}
          onCancel={closeDialogs}
          busy={busy}
        />
      ) : null}

      {editingArea ? (
        <AreaForm
          area={editingArea}
          onClose={() => setEditingArea(null)}
          onSaved={(saved) => {
            setEditingArea(null);
            areas.reload();
            avisar('success', `"${saved.name}" actualizada.`, 'Área actualizada');
          }}
        />
      ) : null}

      {assigningArea ? (
        <AreaAdminsPanel
          area={assigningArea}
          onClose={() => setAssigningArea(null)}
        />
      ) : null}

      {managingAccess && selectedArea ? (
        <PlatformAccessPanel
          platform={managingAccess}
          area={selectedArea}
          onClose={closeDialogs}
        />
      ) : null}

      {removingArea ? (
        <ConfirmDialog
          title="Eliminar área"
          message={`¿Deseas eliminar el área «${removingArea.name}»?`}
          confirmLabel="Eliminar"
          busy={busyRemovingArea}
          onConfirm={handleDeleteArea}
          onCancel={() => setRemovingArea(null)}
        />
      ) : null}

      <AreaCardDesignDrawer
        open={drawerDisenoAbierto}
        onClose={() => setDrawerDisenoAbierto(false)}
        disenoCardsArea={disenoCardsArea}
        onDisenoCardsAreaChange={handleDisenoCardsAreaChange}
        forzarDisenoArea={forzarDisenoArea}
        onForzarDisenoAreaChange={handleForzarDisenoAreaChange}
        devolverA={botonDisenoRef}
      />

      <PlatformCardDesignDrawer
        open={drawerDisenoPlataformaAbierto}
        onClose={() => setDrawerDisenoPlataformaAbierto(false)}
        disenoCards={disenoCardsPlataforma}
        onDisenoCardsChange={handleDisenoCardsPlataformaChange}
        forzarDisenoPlataforma={forzarDisenoPlataforma}
        onForzarDisenoPlataformaChange={handleForzarDisenoPlataformaChange}
        devolverA={botonDisenoPlataformaRef}
      />
    </div>
  );
}
