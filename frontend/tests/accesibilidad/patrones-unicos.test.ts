// @vitest-environment node
/**
 * DIS-068: Prueba «Un patrón, un componente» (ADR-007, PLAN-FASE-7 §2.6, §4.4).
 *
 * Garantiza que ningún marcado ad hoc se introduzca en pantallas o componentes
 * para patrones que ya cuentan con un componente de diseño canónico.
 * Las ocurrencias heredadas se registran en `patrones-unicos.excepciones.ts`
 * y solo pueden disminuir conforme se ejecuten los bloques C y D.
 */
import { readdirSync, readFileSync } from 'node:fs';
import { extname, join, relative, resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { EXCEPCIONES_PATRONES } from './patrones-unicos.excepciones';

const RAIZ_SRC = resolve(import.meta.dirname, '../../src');

function listarArchivosTsx(carpeta: string): string[] {
  return readdirSync(carpeta, { withFileTypes: true }).flatMap((entrada) => {
    const ruta = join(carpeta, entrada.name);
    if (entrada.isDirectory()) return listarArchivosTsx(ruta);
    return extname(entrada.name) === '.tsx' ? [ruta] : [];
  });
}

const ARCHIVOS_TSX = listarArchivosTsx(RAIZ_SRC);

function sinComentarios(texto: string): string {
  return texto.replace(/\/\*[\s\S]*?\*\//g, ' ').replace(/(^|[^:'"`\w])\/\/.*$/gm, '$1');
}

describe('DIS-068: Regla «Un patrón, un componente»', () => {
  for (const ruta of ARCHIVOS_TSX) {
    const relativo = relative(RAIZ_SRC, ruta).split('\\').join('/');
    const contenido = sinComentarios(readFileSync(ruta, 'utf8'));
    const excepcionesArchivo = EXCEPCIONES_PATRONES[relativo] ?? [];

    const excepcionDe = (patron: string) => excepcionesArchivo.find((e) => e.patron === patron);

    // 1. Regla <table>: exclusivo de DataTable
    it(`${relativo} respeta la regla de tablas únicas`, () => {
      if (relativo === 'components/data-table.tsx') return;
      const ocurrencias = [...contenido.matchAll(/<table\b/g)].length;
      const exp = excepcionDe('table');
      if (exp) {
        expect(
          ocurrencias,
          `Excepción de tabla superada en ${relativo}. Ajustar contador si se migró en ${exp.tarea}.`,
        ).toBeLessThanOrEqual(exp.cantidad);
      } else {
        expect(ocurrencias, `Se encontró <table en ${relativo}. Usa DataTable (@/components/data-table).`).toBe(0);
      }
    });

    // 2. Regla nexus-btn: exclusivo de Button / ButtonLink
    it(`${relativo} respeta la regla de botones unificados`, () => {
      if (relativo === 'components/form.tsx' || relativo === 'components/button.tsx' || relativo === 'components/button-link.tsx') return;
      const ocurrencias = [...contenido.matchAll(/(?<![\w-])nexus-btn(?![-\w])/g)].length;
      const exp = excepcionDe('nexus-btn');
      if (exp) {
        expect(
          ocurrencias,
          `Excepción de nexus-btn superada en ${relativo}. Ajustar contador si se migró en ${exp.tarea}.`,
        ).toBeLessThanOrEqual(exp.cantidad);
      } else {
        expect(
          ocurrencias,
          `Se encontró clase nexus-btn en ${relativo}. Usa Button o ButtonLink (@/components/form).`,
        ).toBe(0);
      }
    });

    // 3. Regla <h1>: exclusivo de PageHeader
    it(`${relativo} respeta la regla de encabezado h1 único`, () => {
      if (relativo === 'components/page-header.tsx') return;
      const ocurrencias = [...contenido.matchAll(/<h1\b/g)].length;
      const exp = excepcionDe('h1');
      if (exp) {
        expect(
          ocurrencias,
          `Excepción de <h1> superada en ${relativo}. Ajustar contador si se migró en ${exp.tarea}.`,
        ).toBeLessThanOrEqual(exp.cantidad);
      } else {
        expect(ocurrencias, `Se encontró <h1 en ${relativo}. Usa PageHeader (@/components/page-header).`).toBe(0);
      }
    });

    // 4. Regla role="tablist": exclusivo de Tabs
    it(`${relativo} respeta la regla de pestañas únicas`, () => {
      if (relativo === 'components/tabs.tsx') return;
      const ocurrencias = [...contenido.matchAll(/role=["']tablist["']/g)].length;
      const exp = excepcionDe('tablist');
      if (exp) {
        expect(
          ocurrencias,
          `Excepción de tablist superada en ${relativo}. Ajustar contador si se migró en ${exp.tarea}.`,
        ).toBeLessThanOrEqual(exp.cantidad);
      } else {
        expect(ocurrencias, `Se encontró role="tablist" en ${relativo}. Usa Tabs (@/components/tabs).`).toBe(0);
      }
    });

    // 5. Regla role="dialog" / "alertdialog": exclusivo de diálogos modales
    it(`${relativo} respeta la regla de diálogos unificados`, () => {
      if (
        relativo === 'components/form.tsx' ||
        relativo === 'components/modal.tsx' ||
        relativo === 'components/drawer.tsx' ||
        relativo === 'components/alert-dialog.tsx'
      )
        return;
      const ocurrencias = [...contenido.matchAll(/role=["'](?:dialog|alertdialog)["']/g)].length;
      const exp = excepcionDe('dialog');
      if (exp) {
        expect(
          ocurrencias,
          `Excepción de dialog superada en ${relativo}. Ajustar contador si se migró en ${exp.tarea}.`,
        ).toBeLessThanOrEqual(exp.cantidad);
      } else {
        expect(ocurrencias, `Se encontró role="dialog" en ${relativo}. Usa Modal o Drawer.`).toBe(0);
      }
    });
  }
});
