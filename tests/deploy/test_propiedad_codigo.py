"""Propiedad del código y de los datos (FNC-129, SEG-1 de auditor-seguridad).

El código del prefijo (install.sh, deploy/, plantillas, .git, app/, frontend/,
venv/, node_modules, .next) es de root y sin escritura de grupo ni de otros:
si la cuenta de servicio pudiera editarlo, el siguiente `sudo install.sh`
ejecutaría su código como root. La cuenta solo es dueña de lo que escribe
(datos y registros). Sin root real: la comprobación recibe el uid esperado y
`chown` es falso. Todo en tmp_path.
"""
import os
import re
import subprocess
from pathlib import Path

import pytest

DEPLOY = Path(__file__).resolve().parents[2] / 'deploy'
INSTALL = DEPLOY / 'install.sh'
PROPIEDAD = DEPLOY / 'propiedad.sh'
DATOS = ('instance', 'uploads', 'storage', 'backups')


# --- comprobación del código (inline en install.sh, antes de cargar nada) ----

def _funcion_codigo():
    m = re.search(r'^codigo_protegido\(\) \{\n.*?^\}\n', INSTALL.read_text(),
                  re.S | re.M)
    assert m, 'install.sh debe definir codigo_protegido()'
    return m.group(0)


def _protegido(prefix, uid):
    return subprocess.run(
        ['bash', '-c', 'set -Eeuo pipefail; ' + _funcion_codigo() +
         f'\nDATOS_SERVICIO=({" ".join(DATOS)})\n'
         'codigo_protegido "$1" "$2"', '_', str(prefix), str(uid)],
        capture_output=True, text=True, timeout=30)


@pytest.fixture
def clon(tmp_path):
    raiz = tmp_path / 'portal'
    for rel in ('deploy/install.sh', 'deploy/env_seguro.sh',
                'deploy/backend.service.tmpl', '.git/HEAD', 'app/x.py',
                'frontend/package.json', 'run.py', 'requirements.txt'):
        (raiz / rel).parent.mkdir(parents=True, exist_ok=True)
        (raiz / rel).write_text('x\n')
    for d in (raiz, *[p for p in raiz.rglob('*')]):
        d.chmod(0o755 if d.is_dir() else 0o644)
    return raiz


def test_codigo_del_uid_esperado_pasa(clon):
    r = _protegido(clon, os.getuid())
    assert r.returncode == 0, r.stdout + r.stderr


def test_rechaza_codigo_de_otro_dueno(clon):
    # El clon es del usuario de la prueba, no de root (uid 0).
    r = _protegido(clon, 0)
    assert r.returncode != 0
    assert str(clon) in r.stdout


@pytest.mark.parametrize('rel', ['deploy/install.sh', 'deploy',
                                 'deploy/backend.service.tmpl', '.git/HEAD',
                                 'requirements.txt', '.'])
def test_rechaza_escritura_de_grupo_u_otros(clon, rel):
    ruta = clon / rel
    ruta.chmod((0o775 if ruta.is_dir() else 0o664))
    r = _protegido(clon, os.getuid())
    assert r.returncode != 0
    assert str(ruta.resolve()) in r.stdout or rel == '.'


def test_ignora_env_y_datos_de_la_cuenta(clon):
    env = clon / '.env'
    env.write_text('X=1\n')
    env.chmod(0o660)
    for d in DATOS:
        (clon / d).mkdir()
        (clon / d).chmod(0o775)
    r = _protegido(clon, os.getuid())
    assert r.returncode == 0, r.stdout


def test_rechaza_ancestro_escribible(tmp_path, clon):
    clon.parent.chmod(0o777)
    try:
        r = _protegido(clon, os.getuid())
    finally:
        clon.parent.chmod(0o755)
    assert r.returncode != 0


def test_install_comprueba_antes_de_cargar_nada():
    texto = INSTALL.read_text()
    llamada = texto.index('codigo_protegido "$PREFIX" 0')
    primera_carga = texto.index('. "$PREFIX/deploy/')
    assert llamada < primera_carga
    # Mensaje con la corrección.
    assert 'chown -R root:root' in texto
    assert 'chmod -R go-w' in texto


# --- sin chown -R del prefijo; artefactos de root ----------------------------

def test_no_hay_chown_del_prefijo():
    for linea in INSTALL.read_text().splitlines():
        l = linea.strip()
        if l.startswith('chown '):
            assert not re.search(r'"\$PREFIX"(\s|$)', l), l


def test_artefactos_los_crea_root():
    texto = INSTALL.read_text()
    assert 'sudo -u "$SVC_USER"' not in texto
    assert 'umask 022' in texto


# --- datos y registros de la cuenta de servicio -------------------------------

def _entregar(tmp_path, prefix, logdir):
    binfalso = tmp_path / 'bin'
    binfalso.mkdir(exist_ok=True)
    registro = tmp_path / 'chown.log'
    (binfalso / 'chown').write_text(
        f'#!/usr/bin/env bash\necho "$*" >> "{registro}"\n')
    (binfalso / 'chown').chmod(0o755)
    env = {**os.environ, 'PATH': f'{binfalso}:{os.environ["PATH"]}'}
    r = subprocess.run(
        ['bash', '-c', f'set -Eeuo pipefail; . "{PROPIEDAD}"; '
         'entregar_datos_a_servicio "$@"', '_', str(prefix), str(logdir),
         'svc', 'grp', *DATOS],
        capture_output=True, text=True, timeout=10, env=env)
    return r, (registro.read_text().splitlines() if registro.exists() else [])


def test_datos_existentes_y_logdir_son_de_la_cuenta(tmp_path, clon):
    (clon / 'instance').mkdir()
    (clon / 'uploads').mkdir()
    logdir = tmp_path / 'log' / 'portal'
    r, llamadas = _entregar(tmp_path, clon, logdir)
    assert r.returncode == 0, r.stderr
    assert logdir.is_dir()
    destinos = [l.split()[-1] for l in llamadas]
    assert str(clon / 'instance') in destinos
    assert str(clon / 'uploads') in destinos
    assert str(logdir) in destinos
    # Solo los que existen; nunca el prefijo ni el código.
    assert str(clon / 'storage') not in destinos
    assert str(clon) not in destinos
    for l in llamadas:
        assert '-h' in l.split() and 'svc:grp' in l


def test_dato_enlace_no_se_entrega(tmp_path, clon):
    fuera = tmp_path / 'fuera'
    fuera.mkdir()
    (clon / 'uploads').symlink_to(fuera)
    r, llamadas = _entregar(tmp_path, clon, tmp_path / 'log' / 'portal')
    assert r.returncode != 0
    assert 'enlace' in r.stderr
    assert not any(str(clon / 'uploads') in l for l in llamadas)


def test_install_entrega_datos_y_no_el_codigo():
    texto = INSTALL.read_text()
    assert 'entregar_datos_a_servicio "$PREFIX" "$LOGDIR" "$SVC_USER" "$SVC_GROUP" "${DATOS_SERVICIO[@]}"' in texto
