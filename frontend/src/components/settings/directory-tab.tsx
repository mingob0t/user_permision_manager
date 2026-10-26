'use client';

/**
 * Pestaña Directorio de Ajustes (DIS-023; `GET /auth-config` y `POST
 * /auth-config/test`, contrato `usuarios-directorio.md`; solo superadmin).
 *
 * - Solo lectura: la configuración efectiva sale de las variables `LDAP_*`
 *   (ADR-004); cada valor muestra su variable y si viene del entorno o es el
 *   valor por defecto. Sin campos de contraseña ni mapeos de rol.
 * - "Probar conexión" no envía cuerpo; el resultado es un texto propio (éxito
 *   en `status`, fallo en `alert`) y el aviso recibe el foco (patrón de DIS-022).
 * - El botón se deshabilita con `aria-disabled` (sigue enfocable, DIS-021/022).
 */

import { useRef, useState } from 'react';
import { directoryApi } from '@/lib/access/directory';
import type { DirectoryConfig } from '@/lib/access/types';
import { useAsync } from '@/lib/use-async';
import { Dato } from '../audit/audit-detail-modal';
import { Button } from '../form';
import { Badge, Card, EmptyNote, ErrorNote, Spinner } from '../ui';
import {
  AVISO_FUENTE, CAMPOS_DIRECTORIO, ESTADOS_DIRECTORIO, ETIQUETA_CONTRASENA, MENSAJE_INVALIDA,
  MENSAJE_SIN_CONFIGURAR, PISTA_PRUEBA, PISTA_PRUEBA_NO_DISPONIBLE, TEXTO_CONTRASENA,
  estadoDirectorio, textoOrigen,
} from './directory-catalog';
import { PRUEBA_OK, describeDirectoryLoadError, describeDirectoryTestError } from './directory-errors';

type Tono = 'exito' | 'error';
interface Aviso { texto: string; tono: Tono }

const PISTA_ID = 'directorio-prueba-pista';

/** Lectura con mensaje propio: nunca el texto del servidor. */
async function cargar(): Promise<DirectoryConfig> {
  try {
    return await directoryApi.config();
  } catch (err) {
    throw new Error(describeDirectoryLoadError(err));
  }
}

export function DirectoryTab() {
  const carga = useAsync(cargar, []);
  const avisoRef = useRef<HTMLDivElement>(null);
  const [aviso, setAviso] = useState<Aviso | null>(null);
  const [probando, setProbando] = useState(false);

  const datos = carga.data;
  const config = datos?.config ?? null;
  const estado = datos ? estadoDirectorio(datos) : null;
  const puedeProbar = estado === 'activo';
  const bloqueado = probando || !puedeProbar;

  function anunciar(texto: string, tono: Tono) {
    setAviso({ texto, tono });
    requestAnimationFrame(() => avisoRef.current?.focus());
  }

  async function probar() {
    if (bloqueado) return;
    setProbando(true);
    setAviso(null);
    try {
      await directoryApi.test();
      anunciar(PRUEBA_OK, 'exito');
    } catch (err) {
      const view = describeDirectoryTestError(err);
      anunciar(view.message, 'error');
      if (view.stale) carga.reload();
    } finally {
      setProbando(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-primary/40 bg-primary/10 p-3 text-sm text-body-text">
        {AVISO_FUENTE}
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
              <p className="text-sm font-bold text-success-text">{aviso.texto}</p>
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

      {carga.loading && !datos ? <Spinner label="Cargando la configuración del directorio…" /> : null}

      {carga.error ? (
        <div className="space-y-3">
          <ErrorNote message={carga.error} />
          <Button variant="secondary" onClick={carga.reload} className="focus-visible:ring-2 focus-visible:ring-primary">
            Reintentar
          </Button>
        </div>
      ) : null}

      {datos && estado ? (
        <>
          {estado === 'sin_configurar' ? <EmptyNote message={MENSAJE_SIN_CONFIGURAR} /> : null}
          {estado === 'invalido' ? <ErrorNote message={MENSAJE_INVALIDA} /> : null}

          <Card className="space-y-5">
            <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <Dato
                etiqueta="Estado"
                valor={<Badge tone={ESTADOS_DIRECTORIO[estado].tono}>{ESTADOS_DIRECTORIO[estado].texto}</Badge>}
              />
              {config
                ? CAMPOS_DIRECTORIO.map((campo) => (
                    <Dato
                      key={campo.id}
                      etiqueta={campo.etiqueta}
                      valor={
                        <>
                          <span className="block">{campo.valor(config)}</span>
                          <span className="block text-label">{textoOrigen(datos, campo.origen)}</span>
                        </>
                      }
                    />
                  ))
                : null}
              <Dato etiqueta={ETIQUETA_CONTRASENA} valor={<span className="text-label">{TEXTO_CONTRASENA}</span>} />
            </dl>

            <div className="flex flex-wrap items-center gap-3 border-t border-panel-border pt-4">
              <Button
                variant="secondary"
                onClick={probar}
                aria-disabled={bloqueado || undefined}
                aria-describedby={PISTA_ID}
                className="aria-disabled:opacity-40 focus-visible:ring-2 focus-visible:ring-primary"
              >
                {probando ? 'Probando…' : 'Probar conexión'}
              </Button>
              <span id={PISTA_ID} className="text-sm text-label">
                {puedeProbar ? PISTA_PRUEBA : PISTA_PRUEBA_NO_DISPONIBLE}
              </span>
            </div>
          </Card>
        </>
      ) : null}
    </div>
  );
}
