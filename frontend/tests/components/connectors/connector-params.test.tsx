/**
 * DIS-042: parámetros del conector por tipo (`api`, `ssh` y `bd`; contrato
 * `conectores-y-ejecuciones.md` 1.4). Campos visibles, validación, envío y
 * error del servidor por `params.<ruta>`. Sin secretos ni direcciones IP.
 */
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { Connector } from '@/lib/access/types';

vi.mock('@/lib/access/connectors', () => ({
  connectorsApi: { get: vi.fn(), save: vi.fn(), remove: vi.fn(), test: vi.fn() },
}));

import { ApiError } from '@/lib/api';
import { connectorsApi } from '@/lib/access/connectors';
import { ConnectorForm } from '@/components/connectors/connector-form';
import { cuerpoConector, formularioDesde } from '@/components/connectors/connector-catalog';
import { MENSAJE_REVISA, describeConnectorSaveError } from '@/components/connectors/connector-errors';
import { OBLIGATORIO_PARAM, claveDeError, validarParametros } from '@/components/connectors/connector-params';

const save = vi.mocked(connectorsApi.save);

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function conector(tipo: Connector['type'], params: Record<string, unknown>, extra: Partial<Connector> = {}): Connector {
  return {
    platform_id: 12, type: tipo, host: 'erp.ejemplo.local', port: 443, params, credential_ref: 'pokemon/erp',
    credential_status: 'ok', active: true, updated_at: '2026-10-27T10:00:00Z', ...extra,
  };
}

const HUELLA = `SHA256:${'A'.repeat(43)}`;
const HUELLA_2 = `SHA256:${'b'.repeat(43)}`;

const SSH = conector('ssh', {
  huellas: [HUELLA],
  otorgar: { comando: ['/usr/local/bin/acceso', 'otorgar'], sin_cambios: [3] },
  revocar: { comando: ['/usr/local/bin/acceso', 'revocar'], sin_cambios: [4] },
  consultar: { comando: ['/usr/local/bin/acceso', 'consultar'], ausente: [1] },
}, { port: 22 });

const BD = conector('bd', {
  motor: 'mysql', base_datos: 'erp',
  otorgar: { sentencia: 'INSERT INTO usuarios (email, rol) VALUES (%s, %s)', parametros: ['correo', 'nivel'], max_filas: 2 },
  revocar: { sentencia: 'DELETE FROM usuarios WHERE email = %s', parametros: ['correo'] },
}, { port: 3306 });

const API = conector('api', {
  auth: { esquema: 'cabecera', nombre: 'X-Api-Key' },
  otorgar: { metodo: 'POST', ruta: '/usuarios', consulta: { email: '{correo}' }, cuerpo: { rol: '{nivel}' } },
  revocar: { metodo: 'DELETE', ruta: '/usuarios/{correo}' },
});

function abrir(guardado: Connector) {
  render(<ConnectorForm platformId={12} guardado={guardado} onSaved={vi.fn()} onStale={vi.fn()} />);
}

function guardar() {
  fireEvent.click(screen.getByRole('button', { name: 'Guardar conector' }));
}

describe('tipo api', () => {
  it('muestra sus campos, con la cabecera solo si el esquema la pide, y sin contraseñas', () => {
    abrir(API);
    for (const etiqueta of ['Ruta base', 'Esquema de autenticación *', 'Nombre de la cabecera *']) {
      expect(screen.getByLabelText(etiqueta)).toBeTruthy();
    }
    expect(screen.getAllByLabelText('Método HTTP *')).toHaveLength(3);
    expect(document.querySelector('input[type="password"]')).toBeNull();
    fireEvent.change(screen.getByLabelText('Esquema de autenticación *'), { target: { value: 'bearer' } });
    expect(screen.queryByLabelText('Nombre de la cabecera *')).toBeNull();
    // El cuerpo solo aplica con POST, PUT o PATCH.
    expect(screen.getAllByLabelText('Cuerpo (JSON)')).toHaveLength(1);
  });

  it('valida obligatorios, ruta y JSON, y marca cada campo con su error asociado', () => {
    abrir(conector('api', {}));
    guardar();
    expect(save).not.toHaveBeenCalled();
    const esquema = screen.getByLabelText('Esquema de autenticación *');
    expect(esquema.getAttribute('aria-invalid')).toBe('true');
    expect(document.getElementById(esquema.getAttribute('aria-describedby')!.split(' ').pop()!)?.textContent)
      .toBe(OBLIGATORIO_PARAM);
    expect(validarParametros('api', {
      'auth.esquema': 'bearer', 'otorgar.metodo': 'POST', 'otorgar.ruta': '/a/../b',
      'otorgar.cuerpo': '[1]', 'revocar.metodo': 'DELETE', 'revocar.ruta': '/ok/{correo}',
    })).toEqual({
      'otorgar.ruta': expect.stringContaining('..'), 'otorgar.cuerpo': 'Escribe un objeto JSON válido.',
    });
  });

  it('envía el cuerpo anidado del contrato y omite lo vacío y lo oculto', async () => {
    save.mockResolvedValue({ status: 'success', connector: API });
    abrir(API);
    guardar();
    await waitFor(() => expect(save).toHaveBeenCalledWith(12, {
      type: 'api', host: 'erp.ejemplo.local', port: 443, credential_ref: 'pokemon/erp', active: true,
      params: {
        auth: { esquema: 'cabecera', nombre: 'X-Api-Key' },
        otorgar: { metodo: 'POST', ruta: '/usuarios', consulta: { email: '{correo}' }, cuerpo: { rol: '{nivel}' } },
        revocar: { metodo: 'DELETE', ruta: '/usuarios/{correo}' },
      },
    }));
    // La consulta opcional vacía no se envía; sin POST el cuerpo tampoco.
    const form = formularioDesde(API);
    form.params['otorgar.metodo'] = 'GET';
    form.params['auth.esquema'] = 'bearer';
    const { params } = cuerpoConector(form, API);
    expect(params).toEqual({
      auth: { esquema: 'bearer' },
      otorgar: { metodo: 'GET', ruta: '/usuarios', consulta: { email: '{correo}' } },
      revocar: { metodo: 'DELETE', ruta: '/usuarios/{correo}' },
    });
  });
});

describe('tipo ssh', () => {
  it('muestra huellas, autenticación y las tres operaciones sin pedir secretos', () => {
    abrir(SSH);
    expect((screen.getByLabelText('Huellas de la llave del host') as HTMLTextAreaElement).value)
      .toBe(HUELLA);
    expect(screen.getByLabelText('Método de autenticación')).toBeTruthy();
    expect(screen.getAllByLabelText('Comando *')).toHaveLength(3);
    expect(screen.getByLabelText('Códigos «sin acceso»')).toBeTruthy();
    expect(screen.getByRole('group', { name: 'Consultar acceso (opcional)' })).toBeTruthy();
    expect(document.querySelector('input[type="password"]')).toBeNull();
    expect(screen.queryByLabelText(/Ruta base|Método HTTP|Sentencia/)).toBeNull();
  });

  it('valida el comando, las huellas y los códigos; consultar solo exige lo suyo si se completa', () => {
    const base = {
      huellas: HUELLA, 'otorgar.comando': '/usr/bin/acceso otorgar', 'revocar.comando': '/usr/bin/acceso revocar',
    };
    expect(validarParametros('ssh', base)).toEqual({});
    expect(validarParametros('ssh', { ...base, 'consultar.ausente': '1' })).toEqual({
      'consultar.comando': OBLIGATORIO_PARAM,
    });
    const malos = validarParametros('ssh', {
      huellas: 'md5:aa', 'otorgar.comando': 'acceso otorgar', 'revocar.comando': '/bin/../sh',
      'otorgar.sin_cambios': '0, 300',
    });
    expect(Object.keys(malos).sort()).toEqual(['huellas', 'otorgar.comando', 'otorgar.sin_cambios', 'revocar.comando']);
  });

  it('envía comandos como listas y códigos como enteros', async () => {
    save.mockResolvedValue({ status: 'success', connector: SSH });
    abrir(SSH);
    fireEvent.change(screen.getByLabelText('Huellas de la llave del host'), {
      target: { value: `${HUELLA}\n${HUELLA_2}` },
    });
    guardar();
    await waitFor(() => expect(save).toHaveBeenCalledWith(12, {
      type: 'ssh', host: 'erp.ejemplo.local', port: 22, credential_ref: 'pokemon/erp', active: true,
      params: {
        huellas: [HUELLA, HUELLA_2],
        otorgar: { comando: ['/usr/local/bin/acceso', 'otorgar'], sin_cambios: [3] },
        revocar: { comando: ['/usr/local/bin/acceso', 'revocar'], sin_cambios: [4] },
        consultar: { comando: ['/usr/local/bin/acceso', 'consultar'], ausente: [1] },
      },
    }));
  });
});

describe('tipo bd', () => {
  it('muestra motor, base y sentencias; sin credenciales en el formulario', () => {
    abrir(BD);
    expect((screen.getByLabelText('Motor *') as HTMLSelectElement).value).toBe('mysql');
    expect((screen.getByLabelText('Base de datos *') as HTMLInputElement).value).toBe('erp');
    expect(screen.getAllByLabelText('Sentencia *')).toHaveLength(3);
    expect(screen.getAllByLabelText('Máximo de filas afectadas')).toHaveLength(2);
    expect(document.querySelector('input[type="password"]')).toBeNull();
  });

  it('valida el verbo, el WHERE y que cada %s tenga su marca', () => {
    const ok = {
      motor: 'postgresql', base_datos: 'erp_1',
      'otorgar.sentencia': 'INSERT INTO t (a) VALUES (%s)', 'otorgar.parametros': 'correo',
      'revocar.sentencia': 'DELETE FROM t WHERE a = %s', 'revocar.parametros': 'correo',
    };
    expect(validarParametros('bd', ok)).toEqual({});
    expect(Object.keys(validarParametros('bd', {
      ...ok, base_datos: 'mi base', 'otorgar.sentencia': 'DROP TABLE t', 'revocar.sentencia': 'DELETE FROM t',
      'revocar.max_filas': '11',
    })).sort()).toEqual(['base_datos', 'otorgar.sentencia', 'revocar.max_filas', 'revocar.sentencia']);
    expect(validarParametros('bd', { ...ok, 'revocar.parametros': 'correo, nivel' })['revocar.sentencia'])
      .toMatch(/%s/);
    expect(validarParametros('bd', { ...ok, 'otorgar.parametros': 'clave' })['otorgar.parametros']).toMatch(/marcas/);
    expect(validarParametros('bd', {})).toMatchObject({ motor: OBLIGATORIO_PARAM, base_datos: OBLIGATORIO_PARAM });
  });

  it('envía los parámetros como lista y max_filas como entero', async () => {
    save.mockResolvedValue({ status: 'success', connector: BD });
    abrir(BD);
    guardar();
    await waitFor(() => expect(save).toHaveBeenCalledWith(12, {
      type: 'bd', host: 'erp.ejemplo.local', port: 3306, credential_ref: 'pokemon/erp', active: true,
      params: {
        motor: 'mysql', base_datos: 'erp',
        otorgar: { sentencia: 'INSERT INTO usuarios (email, rol) VALUES (%s, %s)', parametros: ['correo', 'nivel'], max_filas: 2 },
        revocar: { sentencia: 'DELETE FROM usuarios WHERE email = %s', parametros: ['correo'] },
      },
    }));
  });
});

describe('DIS-042 accesibilidad: grupo opcional, anuncios y resumen', () => {
  it('el grupo Consultar se describe con su explicación y los obligatorios condicionales lo dicen', () => {
    abrir(conector('ssh', {}));
    const grupo = screen.getByRole('group', { name: 'Consultar acceso (opcional)' });
    const nota = document.getElementById(grupo.getAttribute('aria-describedby')!);
    expect(nota?.textContent).toMatch(/Déjalo vacío/);
    const comando = within(grupo).getByLabelText('Comando *');
    const pista = comando.getAttribute('aria-describedby')!.split(' ')
      .map((id) => document.getElementById(id)?.textContent).join(' ');
    expect(pista).toContain('Obligatorio si completas este grupo');
    // Fuera del grupo opcional no se repite.
    const otorgar = within(screen.getByRole('group', { name: 'Otorgar acceso' })).getByLabelText('Comando *');
    expect(otorgar.getAttribute('aria-describedby')).not.toContain('grupo');
    const textoOtorgar = otorgar.getAttribute('aria-describedby')!.split(' ')
      .map((id) => document.getElementById(id)?.textContent).join(' ');
    expect(textoOtorgar).not.toContain('Obligatorio si completas');
  });

  const region = () => document.querySelector('[data-region-anuncios]')?.textContent ?? '';

  it('anuncia los parámetros al cambiar de tipo, también en altas', () => {
    abrir(SSH);
    expect(region()).toBe('');
    fireEvent.change(screen.getByLabelText('Tipo de conector *'), { target: { value: 'bd' } });
    expect(region()).toMatch(/^Parámetros de Base de datos: \d+ campos en \d+ grupos\. Se descartaron los del tipo anterior\.$/);
    cleanup();
    render(<ConnectorForm platformId={12} guardado={null} onSaved={vi.fn()} onStale={vi.fn()} />);
    fireEvent.change(screen.getByLabelText('Tipo de conector *'), { target: { value: 'ssh' } });
    expect(region()).toMatch(/^Parámetros de SSH: \d+ campos en \d+ grupos\./);
  });

  it('anuncia los campos que aparecen o desaparecen según otro valor', () => {
    abrir(conector('api', { auth: { esquema: 'bearer' } }));
    fireEvent.change(screen.getByLabelText('Esquema de autenticación *'), { target: { value: 'cabecera' } });
    expect(region()).toMatch(/Aparece: Nombre de la cabecera/);
    fireEvent.change(screen.getByLabelText('Esquema de autenticación *'), { target: { value: 'basic' } });
    expect(region()).toMatch(/Se oculta: Nombre de la cabecera/);
  });

  it('la validación del cliente muestra el resumen de errores', () => {
    abrir(conector('api', {}));
    guardar();
    expect(screen.getByText(/^Revisa \d+ campos marcados\.$/)).toBeTruthy();
  });

  it('con un solo error usa el mensaje de siempre', () => {
    abrir(conector('bd', { ...BD.params, base_datos: 'mala base' }, { port: 3306 }));
    guardar();
    expect(screen.getByText(MENSAJE_REVISA)).toBeTruthy();
  });

  it('grupos y pistas se encogen en pantallas de 320 px', () => {
    abrir(SSH);
    for (const g of document.querySelectorAll('fieldset fieldset')) expect(g.className).toContain('min-w-0');
    expect(document.getElementById('conector-param-huellas-pista')?.className).toContain('break-words');
  });

  it('alinea con el servidor: huella de 43 caracteres y sentencia sin ;, comillas ni comentarios', () => {
    const ok = { huellas: HUELLA, 'otorgar.comando': '/usr/bin/a', 'revocar.comando': '/usr/bin/b' };
    expect(validarParametros('ssh', ok)).toEqual({});
    expect(validarParametros('ssh', { ...ok, huellas: 'SHA256:abc' }).huellas).toBeTruthy();
    expect(validarParametros('ssh', { ...ok, huellas: `${HUELLA}=` }).huellas).toBeTruthy();
    const bd = {
      motor: 'mysql', base_datos: 'erp', 'otorgar.sentencia': 'INSERT INTO t (a) VALUES (%s)',
      'otorgar.parametros': 'correo', 'revocar.sentencia': 'DELETE FROM t WHERE a = %s', 'revocar.parametros': 'correo',
    };
    expect(validarParametros('bd', bd)).toEqual({});
    for (const malo of ["DELETE FROM t WHERE a = %s; DROP", "DELETE FROM t WHERE a = '%s'", 'DELETE FROM t WHERE a = %s -- x',
      'DELETE FROM t WHERE a = %s # x', 'DELETE FROM t WHERE a = %s /* x */', 'DELETE FROM t WHERE a = "%s"']) {
      expect(validarParametros('bd', { ...bd, 'revocar.sentencia': malo })['revocar.sentencia']).toBeTruthy();
    }
  });
});

describe('cambio de tipo y errores del servidor', () => {
  it('al cambiar de tipo se descartan los parámetros del anterior', () => {
    abrir(SSH);
    fireEvent.change(screen.getByLabelText('Tipo de conector *'), { target: { value: 'bd' } });
    expect((screen.getByLabelText('Base de datos *') as HTMLInputElement).value).toBe('');
    expect(screen.queryByLabelText('Huellas de la llave del host')).toBeNull();
    fireEvent.change(screen.getByLabelText('Tipo de conector *'), { target: { value: 'ssh' } });
    expect((screen.getByLabelText('Huellas de la llave del host') as HTMLTextAreaElement).value)
      .toBe(HUELLA);
  });

  it('asigna params.<ruta> al campo más específico del tipo, con texto propio', () => {
    expect(claveDeError('ssh', 'otorgar.comando.0')).toBe('otorgar.comando');
    expect(claveDeError('api', 'otorgar.cuerpo.email')).toBe('otorgar.cuerpo');
    expect(claveDeError('bd', 'huellas')).toBeNull();
    const vista = describeConnectorSaveError(new ApiError(422, 'texto del servidor', {
      code: 'validacion', fields: { 'params.huellas': 'x', 'params.otorgar.comando': 'y', 'params.extra': 'z' },
    }), 'ssh');
    expect(Object.keys(vista.paramFields).sort()).toEqual(['huellas', 'otorgar.comando']);
    expect(vista.paramFields.huellas).toMatch(/^Revisa «Huellas de la llave del host»/);
    expect(vista.fields.params).toBeTruthy();
    expect(JSON.stringify(vista)).not.toContain('texto del servidor');
  });

  it('un 422 de params.<ruta> marca el campo del formulario y lo enfoca', async () => {
    save.mockRejectedValue(new ApiError(422, 'srv', { code: 'validacion', fields: { 'params.base_datos': 'srv' } }));
    abrir(BD);
    guardar();
    const campo = screen.getByLabelText('Base de datos *');
    await waitFor(() => expect(campo.getAttribute('aria-invalid')).toBe('true'));
    expect(campo.getAttribute('aria-describedby')).toContain('conector-param-base_datos-error');
    await waitFor(() => expect(document.activeElement).toBe(campo));
  });
});
