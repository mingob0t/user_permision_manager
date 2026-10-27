'use client';

/**
 * Conector de una plataforma (DIS-022, F-CON-01; `GET`, `PUT`, `DELETE
 * /platforms/<id>/connector` y `POST .../test`, contrato 1.1; solo superadmin).
 *
 * - Sección bajo la lista, no `Modal`: así la confirmación de eliminar no
 *   queda dentro de otro diálogo (patrón de `UserAccessPanel`, DIS-018).
 * - `404` al leer = la plataforma aún no tiene configuración.
 * - "Probar conexión" usa la configuración guardada; el resultado es un texto
 *   propio (el detalle del fallo solo va al registro del servidor).
 * - Sin refresco periódico (contrato, "Refresco"). Tras guardar, eliminar o
 *   probar, el aviso (`status`) recibe el foco.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { ApiError } from '@/lib/api';
import { connectorsApi } from '@/lib/access/connectors';
import type { Connector } from '@/lib/access/types';
import type { Platform } from '@/lib/types';
import { useAsync } from '@/lib/use-async';
import { formatearFecha } from '../access/fecha';
import { Dato } from '../audit/audit-detail-modal';
import { Button } from '../form';
import { Badge, Card, ErrorNote, Spinner, SuccessNote } from '../ui';
import { ESTADOS_CREDENCIAL, TIPOS_CONECTOR, esTipoConocido } from './connector-catalog';
import { ConnectorDeleteDialog } from './connector-delete-dialog';
import {
  PRUEBA_ERROR, PRUEBA_OK, describeConnectorLoadError, describeConnectorTestError,
} from './connector-errors';
import { ConnectorForm } from './connector-form';

type Tono = 'exito' | 'error';
interface Aviso { texto: string; tono: Tono }

export const AVISO_GUARDADO = 'Conector guardado.';
export const AVISO_SIN_VERIFICAR = 'Conector guardado. La credencial queda sin verificar: prueba la conexión.';
export const AVISO_ELIMINADO = 'Conector eliminado.';

/** Configuración guardada (`null` = sin configurar) o el error de carga. */
async function cargar(platformId: number): Promise<{ connector: Connector | null }> {
  try {
    return { connector: await connectorsApi.get(platformId) };
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return { connector: null };
    throw new Error(describeConnectorLoadError(err));
  }
}

export function ConnectorPanel({
  platform,
  onClose,
  onChanged,
}: {
  platform: Platform;
  onClose: () => void;
  /** La configuración cambió (guardada o eliminada): recargar la lista. */
  onChanged: () => void;
}) {
  const titleId = `conector-${platform.id}-titulo`;
  const titulo = useRef<HTMLHeadingElement>(null);
  const avisoRef = useRef<HTMLDivElement>(null);
  const eliminarId = `conector-${platform.id}-eliminar`;

  const carga = useAsync(() => cargar(platform.id), [platform.id]);
  /** Respuesta de una escritura propia: manda sobre la última lectura. */
  const [propio, setPropio] = useState<{ connector: Connector | null } | null>(null);
  const [aviso, setAviso] = useState<Aviso | null>(null);
  const [probando, setProbando] = useState(false);
  const [eliminando, setEliminando] = useState(false);

  useEffect(() => {
    titulo.current?.focus();
    setPropio(null);
    setAviso(null);
  }, [platform.id]);

  const estado = propio ?? carga.data;
  const connector = estado?.connector ?? null;

  function anunciar(texto: string, tono: Tono) {
    setAviso({ texto, tono });
    requestAnimationFrame(() => avisoRef.current?.focus());
  }

  function recargar() {
    setPropio(null);
    carga.reload();
  }

  function guardado(nuevo: Connector) {
    setPropio({ connector: nuevo });
    anunciar(nuevo.credential_status === 'sin_verificar' ? AVISO_SIN_VERIFICAR : AVISO_GUARDADO, 'exito');
    onChanged();
  }

  async function probar() {
    if (probando) return;
    setProbando(true);
    setAviso(null);
    try {
      const resultado = await connectorsApi.test(platform.id);
      const ok = resultado.result === 'ok';
      anunciar(ok ? PRUEBA_OK : PRUEBA_ERROR, ok ? 'exito' : 'error');
      // La prueba actualiza `credential_status`.
      recargar();
    } catch (err) {
      const view = describeConnectorTestError(err);
      anunciar(view.message, 'error');
      if (view.stale) { recargar(); onChanged(); }
    } finally {
      setProbando(false);
    }
  }

  // Estable: `Modal` reinstala su efecto (y el foco) si cambia `onClose`.
  const cerrarEliminar = useCallback(() => {
    setEliminando(false);
    const boton = document.getElementById(eliminarId);
    if (boton) boton.focus();
    else titulo.current?.focus();
  }, [eliminarId]);

  function eliminado() {
    setEliminando(false);
    setPropio({ connector: null });
    anunciar(AVISO_ELIMINADO, 'exito');
    onChanged();
  }

  return (
    <section aria-labelledby={titleId} className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h2
            id={titleId}
            ref={titulo}
            tabIndex={-1}
            className="rounded text-lg font-semibold outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            Conector de {platform.name}
          </h2>
          <p className="text-sm text-label">{platform.area_name ?? '—'}</p>
        </div>
        <Button variant="secondary" onClick={onClose} className="focus-visible:ring-2 focus-visible:ring-primary">
          Cerrar
        </Button>
      </div>

      {/* Dos regiones vivas fijas: el éxito se anuncia con `status` y el fallo con `alert`. */}
      <div
        ref={avisoRef}
        tabIndex={-1}
        className="rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-primary"
      >
        <div role="status">
          {aviso?.tono === 'exito' ? (
            <Card>
              <SuccessNote>{aviso.texto}</SuccessNote>
            </Card>
          ) : null}
        </div>
        <div role="alert">
          {aviso?.tono === 'error' ? (
            <Card>
              <p className="text-sm font-bold text-error-text">{aviso.texto}</p>
            </Card>
          ) : null}
        </div>
      </div>

      {carga.loading && !estado ? <Spinner label="Cargando el conector…" /> : null}

      {carga.error && !propio ? (
        <div className="space-y-3">
          <ErrorNote message={carga.error} />
          <Button variant="secondary" onClick={recargar}>Reintentar</Button>
        </div>
      ) : null}

      {estado ? (
        <Card className="space-y-5">
          {connector ? (
            <>
              <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <Dato
                  etiqueta="Tipo"
                  valor={esTipoConocido(connector.type) ? TIPOS_CONECTOR[connector.type] : connector.type}
                />
                <Dato etiqueta="Destino" valor={`${connector.host}:${connector.port}`} />
                <Dato
                  etiqueta="Credencial"
                  valor={
                    <Badge tone={ESTADOS_CREDENCIAL[connector.credential_status]?.tono ?? 'slate'}>
                      {ESTADOS_CREDENCIAL[connector.credential_status]?.texto ?? connector.credential_status}
                    </Badge>
                  }
                />
                <Dato etiqueta="Actualizado" valor={formatearFecha(connector.updated_at)} />
              </dl>
              <div className="flex flex-wrap items-center gap-3">
                <Button
                  variant="secondary"
                  onClick={probar}
                  aria-disabled={probando || undefined}
                  aria-describedby={`${titleId}-prueba-pista`}
                  className="aria-disabled:opacity-40 focus-visible:ring-2 focus-visible:ring-primary"
                >
                  {probando ? 'Probando…' : 'Probar conexión'}
                </Button>
                <Button
                  id={eliminarId}
                  variant="secondary"
                  onClick={() => { setAviso(null); setEliminando(true); }}
                  aria-label={`Eliminar el conector de ${platform.name}`}
                  className="focus-visible:ring-2 focus-visible:ring-primary"
                >
                  Eliminar
                </Button>
                <span id={`${titleId}-prueba-pista`} className="text-sm text-label">
                  Se prueba la configuración guardada, sin cambios en la plataforma.
                </span>
              </div>
            </>
          ) : (
            <p className="text-sm text-label">
              Esta plataforma aún no tiene conector. Configúralo para que sus accesos se apliquen.
            </p>
          )}

          <ConnectorForm
            // Se reinicia con cada configuración guardada distinta.
            key={connector?.updated_at ?? 'nuevo'}
            platformId={platform.id}
            guardado={connector}
            onSaved={guardado}
            onStale={() => { recargar(); onChanged(); }}
          />
        </Card>
      ) : null}

      {eliminando ? (
        <ConnectorDeleteDialog
          platform={platform}
          onClose={cerrarEliminar}
          onDeleted={eliminado}
          onStale={() => { recargar(); onChanged(); }}
        />
      ) : null}
    </section>
  );
}
