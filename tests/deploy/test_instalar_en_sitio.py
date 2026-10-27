"""Instalador en sitio (FNC-129): `deploy/install.sh` y `deploy/preflight.sh`.

El código se clona donde se instala (p. ej. /opt/portal) y el instalador
trabaja sobre esa carpeta: no copia nada a otro prefijo, `--prefix` ya no
existe y el nombre por defecto es el de la carpeta (antes, `nexus`).
Las ejecuciones usan una copia de `deploy/` en tmp_path; nunca el `.env` real.
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
DEPLOY = RAIZ / 'deploy'
INSTALL = DEPLOY / 'install.sh'
PREFLIGHT = DEPLOY / 'preflight.sh'
NOMBRE = DEPLOY / 'nombre_despliegue.sh'
NO_ROOT = pytest.mark.skipif(os.geteuid() == 0,
                             reason='no se ejecuta install.sh como root')


def _clon(tmp_path, carpeta):
    """Simula un clon en tmp_path/<carpeta> con el deploy/ actual."""
    raiz = tmp_path / carpeta
    shutil.copytree(DEPLOY, raiz / 'deploy')
    return raiz


def _install(raiz, *args):
    return subprocess.run(['bash', str(raiz / 'deploy' / 'install.sh'), *args],
                          capture_output=True, text=True, timeout=10)


# --- nombre por defecto desde la carpeta --------------------------------------

def _nombre(codigo, *args):
    return subprocess.run(
        ['bash', '-c', f'set -Eeuo pipefail; . "{NOMBRE}"; {codigo}', '_', *args],
        capture_output=True, text=True, timeout=10)


@pytest.mark.parametrize('ruta, esperado', [
    ('/opt/portal', 'portal'), ('/opt/mi-portal_2', 'mi-portal_2'),
    ('/srv/apps/pokemon/', 'pokemon'),
])
def test_nombre_por_defecto_es_la_carpeta(ruta, esperado):
    r = _nombre('nombre_por_defecto "$1"', ruta)
    assert r.returncode == 0, r.stderr
    assert r.stdout == esperado


@pytest.mark.parametrize('valor', ['portal', 'a', 'mi-portal_2', 'a' * 32])
def test_nombre_valido(valor):
    assert _nombre('nombre_despliegue_valido "$1"', valor).returncode == 0


@pytest.mark.parametrize('valor', ['', 'Portal', 'mi portal', '2portal',
                                   'a' * 33, 'por.tal', '-x'])
def test_nombre_invalido(valor):
    assert _nombre('nombre_despliegue_valido "$1"', valor).returncode != 0


@NO_ROOT
def test_install_toma_el_nombre_de_la_carpeta(tmp_path):
    # Carpeta válida: pasa la validación y se detiene en la comprobación de root.
    r = _install(_clon(tmp_path, 'portal'))
    assert r.returncode == 1, r.stderr
    assert 'root' in r.stderr
    assert '--name' not in r.stderr


def test_install_carpeta_invalida_pide_name(tmp_path):
    r = _install(_clon(tmp_path, 'Mi Portal'))
    assert r.returncode == 2, r.stderr
    assert '--name' in r.stderr
    assert 'Mi Portal' in r.stderr


@NO_ROOT
def test_install_name_explicito_gana(tmp_path):
    r = _install(_clon(tmp_path, 'Mi Portal'), '--name', 'portal')
    assert r.returncode == 1, r.stderr
    assert 'root' in r.stderr


def test_install_name_explicito_invalido(tmp_path):
    r = _install(_clon(tmp_path, 'portal'), '--name', 'Mal Nombre')
    assert r.returncode == 2
    assert '--name' in r.stderr


def test_nexus_ya_no_es_valor_por_defecto():
    for script in (INSTALL, PREFLIGHT):
        texto = script.read_text()
        assert 'APP_NAME="nexus"' not in texto, script.name
        assert 'APP_NAME:-nexus' not in texto, script.name
        for literal in ('/opt/nexus', '/var/log/nexus', 'nexus-backend',
                        'nexus.conf'):
            assert literal not in texto, (script.name, literal)


def test_preflight_usa_el_nombre_de_la_carpeta():
    texto = PREFLIGHT.read_text()
    assert 'nombre_despliegue.sh' in texto
    assert 'nombre_por_defecto' in texto


# --- --prefix rechazado -------------------------------------------------------

@pytest.mark.parametrize('args', [['--prefix', '/opt/otro'],
                                  ['--prefix=/opt/otro']])
def test_install_rechaza_prefix(tmp_path, args):
    r = _install(_clon(tmp_path, 'portal'), *args)
    assert r.returncode == 2
    assert 'clona el repositorio donde quieras instalarlo' in r.stderr
    assert 'root' not in r.stderr


# --- sin copia ----------------------------------------------------------------

def test_install_no_copia():
    texto = INSTALL.read_text()
    assert 'rsync' not in texto
    assert 'copiar_proyecto' not in texto
    assert 'copia_proyecto.sh' not in texto
    assert not (DEPLOY / 'copia_proyecto.sh').exists()


def test_install_prefijo_es_la_carpeta_del_codigo():
    texto = INSTALL.read_text()
    assert 'PREFIX="$(realpath "$(dirname "${BASH_SOURCE[0]}")/..")"' in texto
