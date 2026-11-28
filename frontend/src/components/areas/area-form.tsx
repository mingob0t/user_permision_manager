'use client';

/**
 * Alta y edición de un área en 3 pasos:
 * - Paso 1: Descripción (Nombre obligatorio, Descripción opcional).
 * - Paso 2: Estilo visual (Color personalizado o por omisión, icono, vista previa dinámica).
 * - Paso 3: Accesos (Dual Picklist para asignar usuarios y marcar administradores de área con casilla).
 *
 * En un alta el color no se envía hasta que se elige: el servidor aplica su
 * color por omisión (el mismo que antes fijaba aquí la pantalla), y así no
 * hay un color literal en el componente.
 */

import { useCallback, useMemo, useState } from 'react';
import { api } from '@/lib/api';
import { usersApi } from '@/lib/access/users';
import type { Area, AreaInput, ManagedUser } from '@/lib/types';
import { useAsync } from '@/lib/use-async';
import { useFocoTrasMover } from '@/lib/use-foco-tras-mover';
import { variablesCss } from '@/lib/variables-css';
import { Button, ColorInput, Field, FieldErrorNote, Modal, TextArea, TextInput } from '../form';
import { Icono } from '../icono';
import type { NombreIcono } from '../icono-trazos';
import { RegionDeAnuncios } from '../region-de-anuncios';
import { useSession } from '../session-provider';
import { Badge, EmptyNote, ErrorNote, Spinner } from '../ui';
import { useToast } from '../toast';
import { erroresDeCampo, mensajeDeError } from './area-errors';

const ICONOS_AREA: { id: NombreIcono; label: string }[] = [
  { id: 'areas', label: 'Estructura' },
  { id: 'panel', label: 'Panel' },
  { id: 'catalogo', label: 'Catálogo' },
  { id: 'plataformas', label: 'Plataformas' },
  { id: 'usuarios', label: 'Usuarios' },
  { id: 'inventario', label: 'Inventario' },
  { id: 'ejecuciones', label: 'Operaciones' },
  { id: 'auditoria', label: 'Auditoría' },
  { id: 'ajustes', label: 'Configuración' },
  { id: 'solicitudes', label: 'Solicitudes' },
  { id: 'aprobaciones', label: 'Aprobaciones' },
  { id: 'escudo', label: 'Seguridad' },
  { id: 'documento', label: 'Documentos' },
  { id: 'actividad', label: 'Monitoreo' },
  { id: 'marca', label: 'Destacado' },
  { id: 'favorito', label: 'Prioritario' },
];

/** Id del campo Nombre: recibe el foco cuando es inválido (`TextInput` no acepta `ref`). */
const NAME_ID = 'area-name';

function enfocarNombre() {
  document.getElementById(NAME_ID)?.focus();
}

/** Atributos de accesibilidad de un control con posible error. */
function invalido(id: string, message?: string) {
  return message ? { 'aria-invalid': true, 'aria-describedby': id } : {};
}

function coincideUsuario(user: ManagedUser, query: string): boolean {
  const q = query.trim().toLowerCase();
  return !q || (user.name || '').toLowerCase().includes(q) || user.email.toLowerCase().includes(q);
}

export function AreaForm({
  area,
  onClose,
  onSaved,
}: {
  area: Area | null;
  onClose: () => void;
  /** Recibe el área que devolvió el servidor. */
  onSaved: (saved: Area) => void;
}) {
  const [paso, setPaso] = useState<1 | 2 | 3>(1);
  const [form, setForm] = useState<AreaInput>(
    area
      ? {
          name: area.name,
          description: area.description ?? '',
          icon: area.icon || 'areas',
          color: area.color,
        }
      : { name: '', description: '', icon: 'areas' },
  );
  // El estado ya no se edita aquí (DIS-114): se conmuta con el badge de la tarjeta o la tabla.
  // Al editar no se envía, para no pisarlo. Al crear (DIS-165, regla FNC-220): el admin de área
  // queda como administrador y el área nace Activa; el superadmin la crea Inactiva, asigna los
  // administradores y solo entonces la activa (sin administradores queda Inactiva).
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fields, setFields] = useState<Record<string, string>>({});
  const toast = useToast();
  const { session } = useSession();
  const isSuperadmin = session?.permissions.is_admin ?? false;

  // Usuarios para el Dual Picklist del paso 3
  const usersAsync = useAsync(() => api.users(), []);
  const todosLosUsuarios = useMemo(() => usersAsync.data ?? [], [usersAsync.data]);

  const [cambiosAcceso, setCambiosAcceso] = useState<Record<number, boolean>>({});
  const [cambiosAdmin, setCambiosAdmin] = useState<Record<number, boolean>>({});
  const [searchSinAcceso, setSearchSinAcceso] = useState('');
  const [searchConAcceso, setSearchConAcceso] = useState('');
  const [anuncio, setAnuncio] = useState('');
  const { refLista, enfocarTras } = useFocoTrasMover();

  const perteneceInicialmente = useCallback(
    (u: ManagedUser) => Boolean(area && u.areas?.some((a) => a.id === area.id)),
    [area],
  );

  const esAdminInicialmente = useCallback(
    (u: ManagedUser) =>
      Boolean(
        area &&
          u.role === 'admin_area' &&
          u.managed_areas?.some((a) => a.id === area.id),
      ),
    [area],
  );

  const tieneAcceso = useCallback(
    (u: ManagedUser) => cambiosAcceso[u.id] ?? perteneceInicialmente(u),
    [cambiosAcceso, perteneceInicialmente],
  );

  const esAdmin = useCallback(
    (u: ManagedUser) => cambiosAdmin[u.id] ?? esAdminInicialmente(u),
    [cambiosAdmin, esAdminInicialmente],
  );

  // Listas de la Dual Picklist
  const sinAcceso = useMemo(
    () => todosLosUsuarios.filter((u) => !tieneAcceso(u)),
    [todosLosUsuarios, tieneAcceso],
  );

  const conAcceso = useMemo(
    () => todosLosUsuarios.filter((u) => tieneAcceso(u)),
    [todosLosUsuarios, tieneAcceso],
  );

  const sinAccesoVisibles = useMemo(
    () => sinAcceso.filter((u) => coincideUsuario(u, searchSinAcceso)),
    [sinAcceso, searchSinAcceso],
  );

  const conAccesoVisibles = useMemo(
    () => conAcceso.filter((u) => coincideUsuario(u, searchConAcceso)),
    [conAcceso, searchConAcceso],
  );

  const adminsCount = useMemo(
    () => conAcceso.filter((u) => esAdmin(u)).length,
    [conAcceso, esAdmin],
  );
  // Vista previa del estado: el actual al editar; al crear, el que tendrá (DIS-165).
  const estadoVista = area?.status ?? (isSuperadmin && adminsCount === 0 ? 'Inactivo' : 'Activo');

  function darAcceso(user: ManagedUser) {
    enfocarTras('sin-acceso', sinAccesoVisibles, user.id);
    setCambiosAcceso((prev) => ({ ...prev, [user.id]: true }));
    setAnuncio(`«${user.name || user.email}» agregado al área, ${conAcceso.length + 1} con acceso`);
  }

  function quitarAcceso(user: ManagedUser) {
    enfocarTras('con-acceso', conAccesoVisibles, user.id);
    setCambiosAcceso((prev) => ({ ...prev, [user.id]: false }));
    setCambiosAdmin((prev) => ({ ...prev, [user.id]: false }));
    setAnuncio(`«${user.name || user.email}» retirado del área, ${sinAcceso.length + 1} sin acceso`);
  }

  function alternarAdmin(user: ManagedUser, checked: boolean) {
    if (!isSuperadmin) return;
    setCambiosAdmin((prev) => ({ ...prev, [user.id]: checked }));
    setAnuncio(
      `«${user.name || user.email}» ${checked ? 'marcado como administrador' : 'desmarcado como administrador'}`,
    );
  }

  function agregarTodosFiltrados() {
    if (sinAccesoVisibles.length === 0) return;
    const nuevosCambios: Record<number, boolean> = {};
    for (const u of sinAccesoVisibles) {
      nuevosCambios[u.id] = true;
    }
    setCambiosAcceso((prev) => ({ ...prev, ...nuevosCambios }));
    setAnuncio(`${sinAccesoVisibles.length} usuarios agregados al área`);
  }

  function quitarTodosFiltrados() {
    if (conAccesoVisibles.length === 0) return;
    const nuevosAccesos: Record<number, boolean> = {};
    const nuevosAdmins: Record<number, boolean> = {};
    for (const u of conAccesoVisibles) {
      nuevosAccesos[u.id] = false;
      nuevosAdmins[u.id] = false;
    }
    setCambiosAcceso((prev) => ({ ...prev, ...nuevosAccesos }));
    setCambiosAdmin((prev) => ({ ...prev, ...nuevosAdmins }));
    setAnuncio(`${conAccesoVisibles.length} usuarios retirados del área`);
  }

  function validarPaso1(): boolean {
    if (!form.name?.trim()) {
      setError(null);
      setFields({ name: 'El nombre es obligatorio.' });
      toast.avisar('warning', 'El nombre es obligatorio.', 'Datos incompletos');
      enfocarNombre();
      return false;
    }
    setError(null);
    setFields({});
    return true;
  }

  function avanzarAlPaso2() {
    if (validarPaso1()) {
      setPaso(2);
    }
  }

  function avanzarAlPaso3() {
    if (validarPaso1()) {
      setPaso(3);
    }
  }

  function retrocederAlPaso1() {
    setError(null);
    setPaso(1);
    setTimeout(enfocarNombre, 50);
  }

  function retrocederAlPaso2() {
    setError(null);
    setPaso(2);
  }

  async function save() {
    if (!validarPaso1()) {
      setPaso(1);
      setTimeout(enfocarNombre, 50);
      return;
    }
    setSaving(true);
    setError(null);
    setFields({});
    try {
      const result = area
        ? await api.updateArea(area.id, form)
        : await api.createArea(isSuperadmin ? { ...form, status: 'Inactivo' } : form);
      let targetArea = result.area;
      let sinAdmin = false;

      const userIdsConAcceso = todosLosUsuarios.filter((u) => tieneAcceso(u)).map((u) => u.id);
      const adminUsers = todosLosUsuarios.filter((u) => tieneAcceso(u) && esAdmin(u));

      if (!area) {
        // En nueva área: aplicar usuarios seleccionados
        if (userIdsConAcceso.length > 0) {
          await api.setAreaUsers(targetArea.id, userIdsConAcceso);
        }
        if (isSuperadmin) {
          for (const adminUser of adminUsers) {
            if (adminUser.role !== 'admin_area') {
              await api.updateUser(adminUser.id, { role: 'admin_area' });
            }
            const existing = (adminUser.managed_areas || []).map((a) => a.id);
            if (!existing.includes(targetArea.id)) {
              await usersApi.setManagedAreas(adminUser.id, [...existing, targetArea.id]);
            }
          }
          // DIS-165: con administradores ya asignados se activa; sin ellos queda Inactiva.
          if (adminUsers.length > 0) {
            targetArea = (await api.updateArea(targetArea.id, { status: 'Activo' })).area;
          } else {
            sinAdmin = true;
          }
        }
      } else {
        // Al editar área existente
        const cambiosEnUsuarios = todosLosUsuarios.some((u) => tieneAcceso(u) !== perteneceInicialmente(u));
        if (cambiosEnUsuarios) {
          await api.setAreaUsers(targetArea.id, userIdsConAcceso);
        }
        if (isSuperadmin) {
          for (const adminUser of adminUsers) {
            if (!esAdminInicialmente(adminUser)) {
              if (adminUser.role !== 'admin_area') {
                await api.updateUser(adminUser.id, { role: 'admin_area' });
              }
              const existing = (adminUser.managed_areas || []).map((a) => a.id);
              if (!existing.includes(targetArea.id)) {
                await usersApi.setManagedAreas(adminUser.id, [...existing, targetArea.id]);
              }
            }
          }
          const desmarcadosAdmin = todosLosUsuarios.filter(
            (u) => esAdminInicialmente(u) && (!tieneAcceso(u) || !esAdmin(u)),
          );
          for (const user of desmarcadosAdmin) {
            const restantes = (user.managed_areas || []).map((a) => a.id).filter((id) => id !== targetArea.id);
            await usersApi.setManagedAreas(user.id, restantes);
          }
        }
      }

      // Un solo aviso: sin administrador, el de acción pendiente (no lo tapa el de éxito).
      if (sinAdmin) {
        toast.avisar(
          'warning',
          `«${targetArea.name}» se creó inactiva: asígnale un administrador para poder activarla.`,
          'Área sin administrador',
        );
      } else {
        toast.avisar(
          'success',
          area
            ? `Área «${targetArea.name}» actualizada correctamente.`
            : `Área «${targetArea.name}» creada correctamente.`,
          'Guardado',
        );
      }
      onSaved(targetArea);
    } catch (err) {
      const msg = mensajeDeError(err, 'No se pudo guardar');
      setError(msg);
      toast.avisar('error', msg, 'Error al guardar');
      const errores = erroresDeCampo(err);
      setFields(errores);
      if (errores.name || errores.description) {
        setPaso(1);
        if (errores.name) setTimeout(enfocarNombre, 50);
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal
      title={area ? 'Editar área' : 'Nueva área'}
      icon="areas"
      size="2xl"
      onClose={onClose}
      footer={
        <div className="flex w-full items-center justify-between gap-3">
          {paso === 1 ? (
            <>
              <Button variant="secondary" onClick={onClose}>
                <Icono nombre="cerrar" tamano="sm" ariaHidden={true} className="mr-1.5" />
                Cancelar
              </Button>
              <Button onClick={avanzarAlPaso2}>
                <span>Siguiente</span>
                <Icono nombre="chevron-der" tamano="sm" ariaHidden={true} className="ml-1.5" />
              </Button>
            </>
          ) : paso === 2 ? (
            <>
              <Button variant="secondary" onClick={retrocederAlPaso1} disabled={saving}>
                <Icono nombre="chevron-izq" tamano="sm" ariaHidden={true} className="mr-1.5" />
                Atrás
              </Button>
              <div className="flex items-center gap-2">
                <Button variant="secondary" onClick={save} disabled={saving}>
                  <Icono nombre="aprobar" tamano="sm" ariaHidden={true} className="mr-1.5" />
                  {saving ? 'Guardando…' : 'Guardar'}
                </Button>
                <Button onClick={avanzarAlPaso3} disabled={saving}>
                  <span>Siguiente: Accesos</span>
                  <Icono nombre="chevron-der" tamano="sm" ariaHidden={true} className="ml-1.5" />
                </Button>
              </div>
            </>
          ) : (
            <>
              <Button variant="secondary" onClick={retrocederAlPaso2} disabled={saving}>
                <Icono nombre="chevron-izq" tamano="sm" ariaHidden={true} className="mr-1.5" />
                Atrás
              </Button>
              <Button onClick={save} disabled={saving}>
                <Icono nombre="aprobar" tamano="sm" ariaHidden={true} className="mr-1.5" />
                {saving ? 'Guardando…' : area ? 'Guardar cambios' : 'Crear área'}
              </Button>
            </>
          )}
        </div>
      }
    >
      <div className="space-y-4">
        {/* Indicador de progreso de 3 pasos con diseño accesible */}
        <nav
          aria-label="Progreso del formulario"
          className="flex items-center justify-between gap-2 sm:gap-3 p-3 rounded-xl border border-panel-border/80 bg-surface-container/60 shadow-xs select-none"
        >
          {/* Paso 1: Descripción */}
          <button
            type="button"
            onClick={() => setPaso(1)}
            aria-current={paso === 1 ? 'step' : undefined}
            className="min-h-12 min-w-12 px-3 flex items-center gap-2.5 text-left cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-lg transition-all"
          >
            <span
              className={`size-7 rounded-lg flex items-center justify-center text-xs font-black transition-colors ${
                paso === 1
                  ? 'bg-primary text-superficie shadow-xs'
                  : paso > 1
                  ? 'bg-primary/20 text-primary-text'
                  : 'bg-surface-container text-label border border-panel-border/60'
              }`}
            >
              {paso > 1 ? '✓' : '1'}
            </span>
            <span className={`text-xs font-bold ${paso === 1 ? 'text-body-text' : 'text-label'}`}>
              Descripción
            </span>
          </button>

          <div className="flex-1 h-0.5 bg-panel-border/60 mx-1" aria-hidden="true" />

          {/* Paso 2: Estilo */}
          <button
            type="button"
            onClick={avanzarAlPaso2}
            aria-current={paso === 2 ? 'step' : undefined}
            className="min-h-12 min-w-12 px-3 flex items-center gap-2.5 text-left cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-lg transition-all"
          >
            <span
              className={`size-7 rounded-lg flex items-center justify-center text-xs font-black transition-colors ${
                paso === 2
                  ? 'bg-primary text-superficie shadow-xs'
                  : paso > 2
                  ? 'bg-primary/20 text-primary-text'
                  : 'bg-surface-container text-label border border-panel-border/60'
              }`}
            >
              {paso > 2 ? '✓' : '2'}
            </span>
            <span className={`text-xs font-bold ${paso === 2 ? 'text-body-text' : 'text-label'}`}>
              Estilo
            </span>
          </button>

          <div className="flex-1 h-0.5 bg-panel-border/60 mx-1" aria-hidden="true" />

          {/* Paso 3: Accesos */}
          <button
            type="button"
            onClick={avanzarAlPaso3}
            aria-current={paso === 3 ? 'step' : undefined}
            className="min-h-12 min-w-12 px-3 flex items-center gap-2.5 text-left cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-lg transition-all"
          >
            <span
              className={`size-7 rounded-lg flex items-center justify-center text-xs font-black transition-colors ${
                paso === 3
                  ? 'bg-primary text-superficie shadow-xs'
                  : 'bg-surface-container text-label border border-panel-border/60'
              }`}
            >
              3
            </span>
            <span className={`text-xs font-bold ${paso === 3 ? 'text-body-text' : 'text-label'}`}>
              Accesos
            </span>
          </button>
        </nav>

        {error ? <div className="sr-only">{error}</div> : null}

        {/* PASO 1: Descripción (Nombre y Descripción) */}
        {paso === 1 ? (
          <div className="space-y-4">
            <div>
              <Field label="Nombre">
                <TextInput
                  id={NAME_ID}
                  placeholder="Ej. Finanzas, Infraestructura…"
                  value={form.name ?? ''}
                  onChange={(e) => {
                    setForm({ ...form, name: e.target.value });
                    if (fields.name) setFields({ ...fields, name: '' });
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      avanzarAlPaso2();
                    }
                  }}
                  {...invalido('area-name-error', fields.name)}
                />
              </Field>
              <FieldErrorNote id="area-name-error" message={fields.name} />
            </div>

            <div>
              <Field label="Descripción">
                <TextArea
                  rows={3}
                  placeholder="Describe las funciones, plataformas y propósito del área…"
                  value={form.description ?? ''}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  {...invalido('area-description-error', fields.description)}
                />
              </Field>
              <FieldErrorNote id="area-description-error" message={fields.description} />
            </div>
          </div>
        ) : null}

        {/* PASO 2: Estilo visual (Color, Icono, Vista previa, Estado) */}
        {paso === 2 ? (
          <div className="space-y-5">
            <div>
              <Field
                label="Color"
                hint={form.color ? undefined : 'Si no eliges uno, se usa el color por omisión.'}
              >
                <div className="flex items-center gap-3 pt-1">
                  <ColorInput
                    id="area-color"
                    aria-label="Color"
                    value={form.color ?? ''}
                    onChange={(e) => setForm({ ...form, color: e.target.value })}
                    {...invalido('area-color-error', fields.color)}
                  />
                  <div className="text-xs text-label">
                    <span className="font-semibold text-body-text">{form.color || 'Por omisión'}</span>
                    <p>Color de identificación del área en tarjetas e insignias.</p>
                  </div>
                </div>
              </Field>
              <FieldErrorNote id="area-color-error" message={fields.color} />
            </div>

            <div>
              <Field
                label="Icono representativo"
                hint="Selecciona el icono que identificará al área en listas, insignias y tarjetas."
              >
                <div
                  role="radiogroup"
                  aria-label="Icono del área"
                  className="grid grid-cols-4 sm:grid-cols-8 gap-2 pt-1"
                >
                  {ICONOS_AREA.map(({ id, label }) => {
                    const seleccionado = (form.icon || 'areas') === id;
                    return (
                      <button
                        key={id}
                        type="button"
                        role="radio"
                        aria-checked={seleccionado}
                        aria-label={label}
                        title={label}
                        onClick={() => setForm({ ...form, icon: id })}
                        className={`min-h-12 min-w-12 flex flex-col items-center justify-center gap-1 rounded-xl border p-2 transition-all outline-none focus-visible:ring-2 focus-visible:ring-primary cursor-pointer ${
                          seleccionado
                            ? 'border-primary bg-primary/10 text-primary-text ring-2 ring-primary/40 shadow-xs'
                            : 'border-panel-border/80 bg-surface-container/60 text-label hover:border-body-text/30 hover:text-body-text'
                        }`}
                      >
                        <Icono nombre={id} tamano="md" ariaHidden={true} />
                        <span className="text-xs font-medium leading-none truncate max-w-full">
                          {label}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </Field>
              <FieldErrorNote id="area-icon-error" message={fields.icon} />
            </div>

            {/* Vista previa en vivo del estilo visual */}
            <div className="rounded-xl border border-panel-border/80 bg-surface-container/30 p-4 space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-label block">
                Vista previa
              </span>
              <div className="flex items-center justify-between gap-3 p-3.5 rounded-xl border border-panel-border/80 bg-panel-fill shadow-xs">
                <div className="flex items-center gap-3 min-w-0">
                  <span
                    className="nx-chip-tint grid size-10 shrink-0 place-items-center rounded-xl text-xs font-black shadow-xs"
                    style={variablesCss({ '--chip-color': form.color })}
                    aria-hidden="true"
                  >
                    {(form.name || 'Área').slice(0, 2).toUpperCase()}
                  </span>
                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5 truncate">
                      <span className="inline-flex size-5 items-center justify-center rounded-md border border-panel-border/60 bg-surface-container text-primary-text shrink-0">
                        <Icono nombre={((form.icon as NombreIcono) || 'areas')} tamano="xs" ariaHidden={true} />
                      </span>
                      <p className="truncate font-bold text-sm text-body-text leading-tight">
                        {form.name || 'Nombre del área'}
                      </p>
                    </div>
                    <p className="truncate text-xs text-label leading-tight mt-0.5">
                      {form.description || 'Sin descripción.'}
                    </p>
                  </div>
                </div>
                <Badge tone={estadoVista === 'Activo' ? 'success' : 'warning'} dot>
                  {estadoVista === 'Activo' ? 'Activa' : 'Inactiva'}
                </Badge>
              </div>
            </div>
          </div>
        ) : null}

        {/* PASO 3: Accesos (Dual Pick List y Checkbox Admin) */}
        {paso === 3 ? (
          <div className="space-y-4">
            <RegionDeAnuncios mensaje={anuncio} />

            {/* Cabecera informativa */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 rounded-xl border border-panel-border/80 bg-surface-container/60 shadow-xs">
              <div className="min-w-0">
                <p className="text-xs font-bold text-body-text">
                  Asignación rápida de accesos y administradores
                </p>
                <p className="text-xs text-label">
                  Transfiere usuarios a la lista con acceso y marca la casilla para nombrarlos administradores del área.
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className="text-xs font-bold px-2.5 py-1 rounded-lg border border-primary/20 bg-primary/10 text-primary-text">
                  {conAcceso.length} con acceso
                </span>
                {adminsCount > 0 ? (
                  <span className="text-xs font-bold px-2.5 py-1 rounded-lg border border-primary/40 bg-primary/20 text-primary-text">
                    {adminsCount} {adminsCount === 1 ? 'admin' : 'admins'}
                  </span>
                ) : null}
                <span className="text-xs font-bold px-2.5 py-1 rounded-lg border border-panel-border/60 bg-superficie text-label">
                  {sinAcceso.length} sin acceso
                </span>
              </div>
            </div>

            {usersAsync.loading && !usersAsync.data ? <Spinner /> : null}
            {usersAsync.error ? <ErrorNote message={usersAsync.error} /> : null}

            {!usersAsync.loading && !usersAsync.error ? (
              todosLosUsuarios.length === 0 ? (
                <EmptyNote message="No hay usuarios registrados en el sistema." />
              ) : (
                /* DUAL PICK LIST: 2 columnas limpias */
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 items-stretch w-full min-h-0">
                  {/* COLUMNA IZQUIERDA: Sin acceso */}
                  <div className="flex flex-col rounded-2xl border border-panel-border/80 bg-surface-container/60 p-3.5 shadow-xs min-w-0">
                    <div className="flex items-center justify-between gap-2 mb-2.5">
                      <span className="text-xs font-bold uppercase tracking-wider text-body-text flex items-center gap-1.5">
                        <Icono nombre="usuarios" tamano="xs" ariaHidden={true} className="text-label" />
                        <span>Sin acceso</span>
                      </span>
                      <div className="flex items-center gap-1.5">
                        {sinAccesoVisibles.length > 0 ? (
                          <button
                            type="button"
                            onClick={agregarTodosFiltrados}
                            title="Agregar todos los usuarios filtrados al área"
                            className="min-h-12 inline-flex items-center px-3 text-xs font-bold text-primary-text hover:underline cursor-pointer"
                          >
                            Agregar todos
                          </button>
                        ) : null}
                        <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-superficie text-label border border-panel-border/60">
                          {sinAcceso.length}
                        </span>
                      </div>
                    </div>

                    <div className="relative mb-2.5">
                      <input
                        type="text"
                        placeholder="Filtrar disponibles…"
                        value={searchSinAcceso}
                        onChange={(e) => setSearchSinAcceso(e.target.value)}
                        aria-label="Filtrar usuarios sin acceso"
                        className="w-full h-10 rounded-xl border border-panel-border bg-fondo pl-9 pr-3 text-xs text-body-text placeholder:text-placeholder focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary transition-colors"
                      />
                      <div
                        className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-label"
                        aria-hidden="true"
                      >
                        <Icono nombre="buscar" tamano="xs" ariaHidden={true} />
                      </div>
                    </div>

                    <ul
                      ref={refLista('sin-acceso')}
                      tabIndex={-1}
                      aria-label="Usuarios sin acceso al área"
                      className="outline-none focus-visible:ring-2 focus-visible:ring-primary flex-1 min-h-48 max-h-64 overflow-y-auto overflow-x-hidden space-y-1.5 p-1 rounded-xl bg-superficie/50 border border-panel-border"
                    >
                      {sinAccesoVisibles.length === 0 ? (
                        <li className="flex items-center justify-center h-32 text-xs text-label italic p-4 text-center">
                          {searchSinAcceso.trim()
                            ? 'Ningún usuario coincide con la búsqueda.'
                            : 'Todos los usuarios tienen acceso.'}
                        </li>
                      ) : (
                        sinAccesoVisibles.map((user) => (
                          <li key={user.id} className="p-0 list-none">
                            <button
                              type="button"
                              data-item-id={user.id}
                              onClick={() => darAcceso(user)}
                              aria-label={`Agregar ${user.name || user.email} al área`}
                              title={`Haz clic para agregar a ${user.name || user.email}`}
                              className="w-full min-h-12 flex items-center justify-between gap-2 px-3 py-2 rounded-xl border border-panel-border bg-superficie hover:border-primary/60 hover:bg-primary/5 active:scale-95 transition-all cursor-pointer select-none text-left shadow-2xs group"
                            >
                              <div className="flex items-center gap-2.5 min-w-0">
                                <div className="size-7 rounded-lg bg-surface-container group-hover:bg-primary/10 group-hover:text-primary-text flex items-center justify-center shrink-0 text-label font-bold text-xs transition-colors">
                                  {(user.name || user.email).charAt(0).toUpperCase()}
                                </div>
                                <div className="min-w-0">
                                  <p className="text-xs font-bold truncate text-body-text group-hover:text-primary-text transition-colors">
                                    {user.name || user.email}
                                  </p>
                                  <p className="text-xs text-label truncate max-w-36">
                                    {user.email}
                                  </p>
                                </div>
                              </div>

                              <span className="size-7 rounded-lg bg-surface-container group-hover:bg-primary group-hover:text-on-primary flex items-center justify-center text-label transition-all shrink-0">
                                <Icono nombre="mas" tamano="xs" ariaHidden={true} />
                              </span>
                            </button>
                          </li>
                        ))
                      )}
                    </ul>
                  </div>

                  {/* COLUMNA DERECHA: Con acceso al área y Casilla Admin */}
                  <div className="flex flex-col rounded-2xl border border-primary/40 bg-gradient-to-b from-primary/5 via-superficie to-primary/5 p-3.5 shadow-xs min-w-0">
                    <div className="flex items-center justify-between gap-2 mb-2.5">
                      <span className="text-xs font-bold uppercase tracking-wider text-primary-text flex items-center gap-1.5">
                        <Icono nombre="exito" tamano="xs" ariaHidden={true} className="text-primary-text" />
                        <span>Con acceso</span>
                      </span>
                      <div className="flex items-center gap-1.5">
                        {conAccesoVisibles.length > 0 ? (
                          <button
                            type="button"
                            onClick={quitarTodosFiltrados}
                            title="Quitar todos los usuarios filtrados del área"
                            className="min-h-12 inline-flex items-center px-3 text-xs font-bold text-error-text hover:underline cursor-pointer"
                          >
                            Quitar todos
                          </button>
                        ) : null}
                        <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-primary/20 text-primary-text border border-primary/40">
                          {conAcceso.length}
                        </span>
                      </div>
                    </div>

                    <div className="relative mb-2.5">
                      <input
                        type="text"
                        placeholder="Filtrar con acceso…"
                        value={searchConAcceso}
                        onChange={(e) => setSearchConAcceso(e.target.value)}
                        aria-label="Filtrar usuarios con acceso"
                        className="w-full h-10 rounded-xl border border-primary/30 bg-fondo pl-9 pr-3 text-xs text-body-text placeholder:text-placeholder focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary transition-colors"
                      />
                      <div
                        className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-label"
                        aria-hidden="true"
                      >
                        <Icono nombre="buscar" tamano="xs" ariaHidden={true} />
                      </div>
                    </div>

                    <ul
                      ref={refLista('con-acceso')}
                      tabIndex={-1}
                      aria-label="Usuarios con acceso al área"
                      className="outline-none focus-visible:ring-2 focus-visible:ring-primary flex-1 min-h-48 max-h-64 overflow-y-auto overflow-x-hidden space-y-1.5 p-1 rounded-xl bg-superficie/50 border border-primary/20"
                    >
                      {conAccesoVisibles.length === 0 ? (
                        <li className="flex items-center justify-center h-32 text-xs text-label italic p-4 text-center">
                          {searchConAcceso.trim()
                            ? 'Ningún usuario coincide con la búsqueda.'
                            : 'Ningún usuario asignado. Haz clic en los disponibles a la izquierda.'}
                        </li>
                      ) : (
                        conAccesoVisibles.map((user) => {
                          const administrando = esAdmin(user);
                          return (
                            <li
                              key={user.id}
                              className="min-h-12 flex items-center justify-between gap-2 px-3 py-2 rounded-xl border border-primary/30 bg-superficie shadow-2xs"
                            >
                              <div className="flex items-center gap-2.5 min-w-0 flex-1">
                                <div className="size-7 rounded-lg bg-primary/10 text-primary-text flex items-center justify-center shrink-0 font-bold text-xs">
                                  {(user.name || user.email).charAt(0).toUpperCase()}
                                </div>
                                <div className="min-w-0 flex-1">
                                  <p className="text-xs font-bold truncate text-body-text">
                                    {user.name || user.email}
                                  </p>
                                  <p className="text-xs text-label truncate max-w-32">
                                    {user.email}
                                  </p>
                                </div>
                              </div>

                              <div className="flex items-center gap-2 shrink-0">
                                {/* Checkbox para hacer admin del área */}
                                <label
                                  className={`flex min-h-12 items-center gap-1.5 px-2 rounded-lg select-none transition-colors ${
                                    isSuperadmin
                                      ? 'cursor-pointer hover:bg-primary/5'
                                      : 'cursor-not-allowed estado-deshabilitado'
                                  }`}
                                  title={
                                    isSuperadmin
                                      ? `Marcar a ${user.name || user.email} como administrador del área`
                                      : 'Solo el superadministrador puede asignar administradores de área.'
                                  }
                                >
                                  <input
                                    type="checkbox"
                                    checked={administrando}
                                    disabled={!isSuperadmin}
                                    onChange={(e) => alternarAdmin(user, e.target.checked)}
                                    aria-label={`Hacer admin de área a ${user.name || user.email}`}
                                    className={`nexus-checkbox ${isSuperadmin ? 'cursor-pointer' : 'cursor-not-allowed'}`}
                                  />
                                  <span
                                    className={`text-xs font-bold transition-colors ${
                                      administrando ? 'text-primary-text' : 'text-label'
                                    }`}
                                  >
                                    Admin
                                  </span>
                                </label>

                                {/* Botón para quitar del área */}
                                <button
                                  type="button"
                                  data-item-id={user.id}
                                  onClick={() => quitarAcceso(user)}
                                  aria-label={`Quitar a ${user.name || user.email} del área`}
                                  title={`Quitar a ${user.name || user.email} del área`}
                                  className="min-h-12 min-w-12 flex items-center justify-center rounded-lg bg-surface-container hover:bg-error hover:text-superficie text-label transition-all cursor-pointer"
                                >
                                  <Icono nombre="cerrar" tamano="xs" ariaHidden={true} />
                                </button>
                              </div>
                            </li>
                          );
                        })
                      )}
                    </ul>
                  </div>
                </div>
              )
            ) : null}
          </div>
        ) : null}
      </div>
    </Modal>
  );
}
