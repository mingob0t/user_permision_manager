"""Copia del proyecto al prefijo (FNC-125): `deploy/copia_proyecto.sh`.

Regresión: `rsync --delete` borraba (o pisaba) el `.env` del prefijo y los
datos locales que no vienen del repo. Todo con directorios y `.env`
SINTÉTICOS en tmp_path; nunca toca el `.env` real.
"""
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / 'deploy' / 'copia_proyecto.sh'
ENV_PREFIJO = 'MARCA=del-prefijo\n'
ENV_ORIGEN = 'MARCA=del-origen\n'
# Locales del prefijo que no vienen del repo y deben sobrevivir.
LOCALES = ('.env.respaldo', 'instance/nexus.db', 'backups/bd.dump',
           'uploads/logo.png', 'storage/x.bin', 'logs/app.log')

pytestmark = pytest.mark.skipif(shutil.which('rsync') is None,
                                reason='rsync no instalado')


def _origen(tmp_path, con_env):
    src = tmp_path / 'src'
    (src / 'app').mkdir(parents=True)
    (src / 'run.py').write_text('# nuevo\n')
    (src / 'app' / 'x.py').write_text('# nuevo\n')
    (src / '.env.example').write_text('MARCA=\n')
    (src / 'docs' / 'logs').mkdir(parents=True)
    (src / 'docs' / 'logs' / 'dia.md').write_text('bitacora\n')
    if con_env:
        (src / '.env').write_text(ENV_ORIGEN)
    return src


def _prefijo(tmp_path, con_env):
    prefix = tmp_path / 'opt'
    prefix.mkdir()
    (prefix / 'obsoleto.py').write_text('# ya no está en el repo\n')
    for rel in LOCALES:
        (prefix / rel).parent.mkdir(parents=True, exist_ok=True)
        (prefix / rel).write_text(f'local {rel}\n')
    if con_env:
        (prefix / '.env').write_text(ENV_PREFIJO)
    return prefix


def _copiar(src, prefix):
    r = subprocess.run(
        ['bash', '-c', f'set -Eeuo pipefail; . "{SCRIPT}"; '
         'copiar_proyecto "$1" "$2"', '_', str(src), str(prefix)],
        capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr
    return r


@pytest.mark.parametrize('env_en_origen', [False, True])
def test_env_del_prefijo_sobrevive_sin_cambios(tmp_path, env_en_origen):
    src = _origen(tmp_path, con_env=env_en_origen)
    prefix = _prefijo(tmp_path, con_env=True)
    _copiar(src, prefix)
    assert (prefix / '.env').read_text() == ENV_PREFIJO


def test_locales_del_prefijo_sobreviven(tmp_path):
    src = _origen(tmp_path, con_env=False)
    prefix = _prefijo(tmp_path, con_env=True)
    _copiar(src, prefix)
    for rel in LOCALES:
        assert (prefix / rel).read_text() == f'local {rel}\n', rel


def test_sigue_sincronizando_el_repo(tmp_path):
    src = _origen(tmp_path, con_env=False)
    prefix = _prefijo(tmp_path, con_env=True)
    _copiar(src, prefix)
    assert (prefix / 'run.py').read_text() == '# nuevo\n'
    assert (prefix / 'app' / 'x.py').exists()
    assert (prefix / '.env.example').exists()
    # Las exclusiones van ancladas: docs/logs/ (versionada) sí se copia.
    assert (prefix / 'docs' / 'logs' / 'dia.md').exists()
    assert not (prefix / 'obsoleto.py').exists()


def test_env_del_origen_se_copia_una_vez(tmp_path):
    src = _origen(tmp_path, con_env=True)
    prefix = tmp_path / 'opt'
    prefix.mkdir()
    _copiar(src, prefix)
    destino = prefix / '.env'
    assert destino.read_text() == ENV_ORIGEN
    assert stat.S_IMODE(destino.stat().st_mode) == 0o600
    # Una segunda pasada con otro .env en el origen no lo pisa.
    (src / '.env').write_text('MARCA=cambiada\n')
    _copiar(src, prefix)
    assert destino.read_text() == ENV_ORIGEN


def test_sin_env_en_ningun_lado_no_crea_uno(tmp_path):
    src = _origen(tmp_path, con_env=False)
    prefix = tmp_path / 'opt'
    prefix.mkdir()
    _copiar(src, prefix)
    assert not (prefix / '.env').exists()


# --- .env del prefijo: nunca a través de un enlace (hallazgo Alto) -----------
# El prefijo es de la cuenta de servicio: con `ln -sf /etc/shadow .env`, el
# chown/chmod de root seguía el enlace y le daba el destino a esa cuenta.

import getpass
import grp
import os
import sys

INSTALL = SCRIPT.parent / 'install.sh'


def _asegurar(prefix):
    usuario = getpass.getuser()
    grupo = grp.getgrgid(os.getgid()).gr_name
    return subprocess.run(
        ['bash', '-c', f'set -Eeuo pipefail; . "{SCRIPT}"; '
         'asegurar_env_prefijo "$1" "$2" "$3" "$4"', '_', str(prefix),
         usuario, grupo, sys.executable],
        capture_output=True, text=True, timeout=30)


def _fuera(tmp_path):
    fuera = tmp_path / 'fuera'
    fuera.mkdir()
    destino = fuera / 'sensible'
    destino.write_text('no-tocar\n')
    destino.chmod(0o644)
    return destino


def test_env_enlace_aborta_sin_tocar_destino(tmp_path):
    destino = _fuera(tmp_path)
    antes = destino.stat()
    prefix = tmp_path / 'opt'
    prefix.mkdir()
    (prefix / '.env').symlink_to(destino)
    r = _asegurar(prefix)
    assert r.returncode != 0
    assert 'enlace' in (r.stdout + r.stderr)
    despues = destino.stat()
    assert stat.S_IMODE(despues.st_mode) == 0o644
    assert (despues.st_uid, despues.st_gid) == (antes.st_uid, antes.st_gid)
    assert destino.read_text() == 'no-tocar\n'


def test_env_directorio_aborta(tmp_path):
    prefix = tmp_path / 'opt'
    (prefix / '.env').mkdir(parents=True)
    r = _asegurar(prefix)
    assert r.returncode != 0
    assert 'regular' in (r.stdout + r.stderr)


def test_env_enlace_duro_aborta(tmp_path):
    destino = _fuera(tmp_path)
    prefix = tmp_path / 'opt'
    prefix.mkdir()
    os.link(destino, prefix / '.env')
    r = _asegurar(prefix)
    assert r.returncode != 0
    assert 'enlace' in (r.stdout + r.stderr)
    assert stat.S_IMODE(destino.stat().st_mode) == 0o644


def test_env_ausente_aborta(tmp_path):
    prefix = tmp_path / 'opt'
    prefix.mkdir()
    r = _asegurar(prefix)
    assert r.returncode != 0
    assert 'no existe' in (r.stdout + r.stderr)


def test_env_regular_queda_600(tmp_path):
    prefix = tmp_path / 'opt'
    prefix.mkdir()
    env = prefix / '.env'
    env.write_text(ENV_PREFIJO)
    env.chmod(0o644)
    r = _asegurar(prefix)
    assert r.returncode == 0, r.stdout + r.stderr
    assert stat.S_IMODE(env.stat().st_mode) == 0o600
    assert env.read_text() == ENV_PREFIJO


def test_env_del_origen_enlace_no_se_copia(tmp_path):
    destino = _fuera(tmp_path)
    src = _origen(tmp_path, con_env=False)
    (src / '.env').symlink_to(destino)
    prefix = tmp_path / 'opt'
    prefix.mkdir()
    r = subprocess.run(
        ['bash', '-c', f'set -Eeuo pipefail; . "{SCRIPT}"; '
         'copiar_proyecto "$1" "$2"', '_', str(src), str(prefix)],
        capture_output=True, text=True, timeout=30)
    assert r.returncode != 0
    assert 'enlace' in (r.stdout + r.stderr)
    assert not (prefix / '.env').exists() and not (prefix / '.env').is_symlink()


def test_install_no_sigue_enlaces():
    texto = INSTALL.read_text()
    assert 'asegurar_env_prefijo "$PREFIX"' in texto
    assert 'chmod 600 "$PREFIX/.env"' not in texto
    lineas = [l.strip() for l in texto.splitlines()
              if l.strip().startswith('chown ')]
    assert lineas, 'sin chown en install.sh'
    for linea in lineas:
        if ' -R' in linea:
            assert ' -h' in linea or '--no-dereference' in linea, linea
        assert ' -L' not in linea, linea
