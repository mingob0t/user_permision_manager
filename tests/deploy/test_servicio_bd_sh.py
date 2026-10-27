"""Servicio de BD en las unidades systemd (FNC-125): `deploy/servicio_bd.sh`.

La detección se prueba con un `systemctl` falso en el PATH: nunca consulta el
systemd de la máquina que corre las pruebas.
"""
import os
import subprocess
from pathlib import Path

import pytest

DEPLOY = Path(__file__).resolve().parents[2] / 'deploy'
SCRIPT = DEPLOY / 'servicio_bd.sh'
INSTALL = DEPLOY / 'install.sh'
PLANTILLAS = ('backend.service.tmpl', 'worker.service.tmpl')
MARCADOR = '@DB_SERVICE@'

# list-unit-files [opciones] PATRON: imprime las unidades de UNIDADES_FALSAS
# ("nombre estado" por línea) cuyo nombre coincide con el patrón.
SYSTEMCTL_FALSO = r'''#!/usr/bin/env bash
[[ "$1" == list-unit-files ]] || exit 1
shift
patron=""
for a in "$@"; do [[ "$a" == -* ]] || patron="$a"; done
while read -r unidad estado; do
    [[ -n "$unidad" ]] || continue
    [[ -z "$patron" || "$unidad" == $patron ]] \
        && printf '%s %s %s\n' "$unidad" "$estado" "$estado"
done <<< "${UNIDADES_FALSAS:-}"
exit 0
'''


def _bash(codigo, *args, entorno=None, entrada=None):
    return subprocess.run(
        ['bash', '-c', f'. "{SCRIPT}"; {codigo}', '_', *args],
        capture_output=True, text=True, timeout=10, env=entorno,
        input=entrada)


def _con_systemctl_falso(tmp_path, unidades):
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    falso = bin_dir / 'systemctl'
    falso.write_text(SYSTEMCTL_FALSO)
    falso.chmod(0o755)
    return {**os.environ, 'PATH': f'{bin_dir}:{os.environ["PATH"]}',
            'UNIDADES_FALSAS': unidades}


# --- Detección ---------------------------------------------------------------

@pytest.mark.parametrize('unidades, esperado', [
    ('mysqld.service enabled', 'mysqld.service'),
    ('mariadb.service enabled', 'mariadb.service'),
    ('mysql.service enabled', 'mysql.service'),
    # Orden de preferencia: mysqld, mariadb, mysql.
    ('mysql.service enabled\nmariadb.service enabled', 'mariadb.service'),
    ('mariadb.service enabled\nmysqld.service disabled', 'mysqld.service'),
    # Los alias de MariaDB (mysqld/mysql) no cuentan: se da el nombre real.
    ('mysqld.service alias\nmysql.service alias\nmariadb.service enabled',
     'mariadb.service'),
])
def test_detecta_servicio(tmp_path, unidades, esperado):
    r = _bash('detectar_servicio_bd',
              entorno=_con_systemctl_falso(tmp_path, unidades))
    assert r.returncode == 0, r.stderr
    assert r.stdout == esperado


@pytest.mark.parametrize('unidades', ['', 'redis.service enabled',
                                      'mysqld-extra.service enabled'])
def test_sin_servicio_local(tmp_path, unidades):
    r = _bash('detectar_servicio_bd',
              entorno=_con_systemctl_falso(tmp_path, unidades))
    assert r.returncode == 1
    assert r.stdout == ''


# --- Validación de --db-service ---------------------------------------------

@pytest.mark.parametrize('entrada, normalizado', [
    ('mariadb', 'mariadb.service'),
    ('mysqld.service', 'mysqld.service'),
    ('mysql@main.service', 'mysql@main.service'),
    ('rh-mysql80-mysqld', 'rh-mysql80-mysqld.service'),
])
def test_nombre_valido(entrada, normalizado):
    r = _bash('servicio_bd_valido "$1"', entrada)
    assert r.returncode == 0, r.stderr
    assert r.stdout == normalizado


@pytest.mark.parametrize('entrada', [
    '', '.service', '-mysqld', 'mysql;reboot', 'my sql', 'mysql|x',
    'a/b.service', '../x', 'mysql$(id)', 'mysql\nWants=x', 'mysql\\x',
    'x' * 300,
])
def test_nombre_invalido(entrada):
    r = _bash('servicio_bd_valido "$1"', entrada)
    assert r.returncode != 0
    assert r.stdout == ''


@pytest.mark.skipif(os.geteuid() == 0, reason='no se ejecuta install.sh como root')
def test_install_rechaza_nombre_invalido():
    r = subprocess.run(['bash', str(INSTALL), '--db-service', 'mysql;reboot'],
                       capture_output=True, text=True, timeout=10)
    assert r.returncode == 2
    assert '--db-service' in r.stderr


@pytest.mark.skipif(os.geteuid() == 0, reason='no se ejecuta install.sh como root')
def test_install_acepta_nombre_valido():
    # Pasa la validación y se detiene en la comprobación de root.
    r = subprocess.run(['bash', str(INSTALL), '--db-service', 'mariadb'],
                       capture_output=True, text=True, timeout=10)
    assert r.returncode == 1
    assert 'root' in r.stderr
    assert '--db-service' not in r.stderr


# --- Reemplazo en las plantillas --------------------------------------------

def _aplicar(plantilla, servicio):
    texto = (DEPLOY / plantilla).read_text()
    r = _bash('aplicar_servicio_bd "$1"', servicio, entrada=texto)
    assert r.returncode == 0, r.stderr
    return r.stdout


def _directivas(texto, nombre):
    return [l.split('=', 1)[1].split() for l in texto.splitlines()
            if l.startswith(f'{nombre}=')]


@pytest.mark.parametrize('plantilla', PLANTILLAS)
def test_plantillas_usan_marcador(plantilla):
    texto = (DEPLOY / plantilla).read_text()
    assert MARCADOR in texto
    assert 'mysql.service' not in texto


@pytest.mark.parametrize('plantilla', PLANTILLAS)
@pytest.mark.parametrize('servicio', ['mysqld.service', 'mariadb.service',
                                      'mysql.service'])
def test_reemplazo_con_servicio(plantilla, servicio):
    texto = _aplicar(plantilla, servicio)
    assert MARCADOR not in texto
    for directiva in ('After', 'Wants'):
        valores = [v for linea in _directivas(texto, directiva) for v in linea]
        assert servicio in valores
    if plantilla.startswith('worker'):
        for directiva in ('After', 'Wants'):
            assert any('redis.service' in l and 'network-online.target' in l
                       for l in _directivas(texto, directiva))


@pytest.mark.parametrize('plantilla', PLANTILLAS)
def test_reemplazo_sin_servicio(plantilla):
    original = (DEPLOY / plantilla).read_text()
    texto = _aplicar(plantilla, '')
    assert MARCADOR not in texto
    for linea in texto.splitlines():
        if linea.startswith(('After=', 'Wants=')):
            assert linea.split('=', 1)[1].strip(), f'directiva vacía: {linea}'
            assert '  ' not in linea and not linea.endswith(' ')
    directivas = [l for l in texto.splitlines()
                  if l.startswith(('After=', 'Wants='))]
    assert not any(s in l for l in directivas
                   for s in ('mysqld', 'mariadb', 'mysql'))
    # Solo se tocan las líneas con el marcador.
    otras = [l for l in original.splitlines() if MARCADOR not in l]
    assert [l for l in texto.splitlines()
            if not l.startswith(('After=', 'Wants='))] == \
        [l for l in otras if not l.startswith(('After=', 'Wants='))]
    if plantilla.startswith('worker'):
        assert _directivas(texto, 'After') == [['network-online.target',
                                                'redis.service']]
        assert _directivas(texto, 'Wants') == [['network-online.target',
                                                'redis.service']]
    else:
        assert _directivas(texto, 'After') == [['network.target']]
        assert _directivas(texto, 'Wants') == []


# --- Cliente mysql opcional (dnf falso) --------------------------------------

DNF_FALSO = r'''#!/bin/bash
printf '%s\n' "$*" >> "$REGISTRO_DNF"
exit "${SALIDA_DNF:-0}"
'''


def _con_dnf_falso(tmp_path, con_mysql=False, salida_dnf=0):
    """PATH solo con el dnf falso (y un mysql falso si se pide): `command -v
    mysql` no ve el cliente real de la máquina que corre las pruebas."""
    bin_dir = tmp_path / 'bin_dnf'
    bin_dir.mkdir()
    falsos = {'dnf': DNF_FALSO}
    if con_mysql:
        falsos['mysql'] = '#!/bin/bash\nexit 0\n'
    for nombre, cuerpo in falsos.items():
        (bin_dir / nombre).write_text(cuerpo)
        (bin_dir / nombre).chmod(0o755)
    registro = tmp_path / 'dnf.log'
    registro.write_text('')
    entorno = {'PATH': str(bin_dir), 'REGISTRO_DNF': str(registro),
               'SALIDA_DNF': str(salida_dnf)}
    return entorno, registro


def _instalar_cliente(tmp_path, servicio, **kw):
    entorno, registro = _con_dnf_falso(tmp_path, **kw)
    r = subprocess.run(
        ['/bin/bash', '-c',
         f'set -Eeuo pipefail; . "{SCRIPT}"; instalar_cliente_bd "$1"',
         '_', servicio], capture_output=True, text=True, timeout=10,
        env=entorno)
    return r, registro.read_text().splitlines()


def test_cliente_presente_no_instala(tmp_path):
    r, llamadas = _instalar_cliente(tmp_path, 'mariadb.service',
                                    con_mysql=True)
    assert r.returncode == 0, r.stderr
    assert llamadas == []


@pytest.mark.parametrize('servicio, paquete', [
    ('mariadb.service', 'mariadb'),
    ('mysqld.service', 'mysql'),
    ('mysql.service', 'mysql'),
    ('', 'mysql'),
])
def test_cliente_segun_servicio(tmp_path, servicio, paquete):
    r, llamadas = _instalar_cliente(tmp_path, servicio)
    assert r.returncode == 0, r.stderr
    assert llamadas == [f'-y install {paquete}']


@pytest.mark.parametrize('servicio, paquete', [
    ('mariadb.service', 'mariadb'), ('mysqld.service', 'mysql')])
def test_cliente_falla_es_aviso(tmp_path, servicio, paquete):
    r, llamadas = _instalar_cliente(tmp_path, servicio, salida_dnf=1)
    assert r.returncode == 0, r.stderr
    assert 'AVISO' in r.stdout
    assert f'dnf install {paquete}' in r.stdout


def test_install_sin_paquetes_de_bd_ni_ldap():
    """mysqlclient y python-ldap no se usan (PyMySQL y ldap3 son puro
    Python); el cliente mysql va aparte y es opcional."""
    texto = INSTALL.read_text()
    inicio = texto.index('dnf -y install gcc')
    linea = texto[inicio:texto.index('|| die', inicio)]
    for paquete in ('mariadb-devel', 'openldap-devel', ' mysql ',
                    'policycoreutils-python-utils'):
        assert paquete not in linea + ' ', paquete
    assert 'instalar_cliente_bd "$DB_SERVICE"' in texto
