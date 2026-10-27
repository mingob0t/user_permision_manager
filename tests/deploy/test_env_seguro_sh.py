""".env del prefijo nunca a través de un enlace (FNC-125, movido en FNC-129).

`deploy/env_seguro.sh` (`asegurar_env_prefijo`). Hallazgo Alto de
auditor-seguridad: el prefijo es de la cuenta de servicio, y con
`ln -sf /etc/shadow .env` el chown/chmod de root seguía el enlace y le daba el
destino a esa cuenta. Todo con archivos SINTÉTICOS en tmp_path; nunca toca el
`.env` real.
"""
import getpass
import grp
import os
import stat
import subprocess
import sys
from pathlib import Path

DEPLOY = Path(__file__).resolve().parents[2] / 'deploy'
SCRIPT = DEPLOY / 'env_seguro.sh'
INSTALL = DEPLOY / 'install.sh'
ENV_PREFIJO = 'MARCA=del-prefijo\n'


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


def test_env_ausente_aborta_pidiendo_crearlo(tmp_path):
    prefix = tmp_path / 'opt'
    prefix.mkdir()
    r = _asegurar(prefix)
    assert r.returncode != 0
    salida = r.stdout + r.stderr
    assert 'no existe' in salida
    # FNC-129: ya no hay copia desde otro origen; se crea desde el ejemplo.
    assert '.env.example' in salida
    assert not (prefix / '.env').exists()


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


def test_install_no_sigue_enlaces():
    texto = INSTALL.read_text()
    assert '. "$PREFIX/deploy/env_seguro.sh"' in texto
    assert 'asegurar_env_prefijo "$PREFIX"' in texto
    assert 'chmod 600 "$PREFIX/.env"' not in texto
    lineas = [l.strip() for l in texto.splitlines()
              if l.strip().startswith('chown ')]
    assert lineas, 'sin chown en install.sh'
    for linea in lineas:
        if ' -R' in linea:
            assert ' -h' in linea or '--no-dereference' in linea, linea
        assert ' -L' not in linea, linea
