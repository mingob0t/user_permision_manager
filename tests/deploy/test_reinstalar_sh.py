"""Reinstalación limpia con `--force` / `--reinstall` (FNC-129): `deploy/reinstalar.sh`.

Todo sobre una raíz temporal (prefijo, logdir, /etc/systemd/system y
/etc/nginx/conf.d falsos) y con un `systemctl` falso que solo registra sus
argumentos. La confirmación se prueba con stdin sin terminal y con una
pseudoterminal real (pty). El `.env` es SINTÉTICO.
"""
import os
import pty
import subprocess
from pathlib import Path

import pytest

DEPLOY = Path(__file__).resolve().parents[2] / 'deploy'
SCRIPT = DEPLOY / 'reinstalar.sh'
INSTALL = DEPLOY / 'install.sh'
NOMBRE = 'portal'
UNIDADES = [f'{NOMBRE}-backend', f'{NOMBRE}-frontend', f'{NOMBRE}-worker']
# Lo que --force nunca toca.
INTACTOS = ('.env', 'run.py', '.git/HEAD', 'instance/app.db', 'backups/bd.dump',
            'uploads/logo.png', 'storage/x.bin', 'frontend/package.json',
            'frontend/src/page.tsx')
NO_ROOT = pytest.mark.skipif(os.geteuid() == 0,
                             reason='no se ejecuta install.sh como root')


@pytest.fixture
def raiz(tmp_path):
    prefix = tmp_path / 'opt' / NOMBRE
    for rel in INTACTOS:
        (prefix / rel).parent.mkdir(parents=True, exist_ok=True)
        (prefix / rel).write_text(f'intacto {rel}\n')
    for rel in ('venv/bin/python', 'frontend/node_modules/x/index.js',
                'frontend/.next/standalone/server.js'):
        (prefix / rel).parent.mkdir(parents=True, exist_ok=True)
        (prefix / rel).write_text('generado\n')
    logdir = tmp_path / 'var' / 'log' / NOMBRE
    logdir.mkdir(parents=True)
    (logdir / 'app.log').write_text('log\n')
    systemd = tmp_path / 'etc' / 'systemd' / 'system'
    systemd.mkdir(parents=True)
    for u in UNIDADES:
        (systemd / f'{u}.service').write_text('[Unit]\n')
    # De otra instalación: no se toca.
    (systemd / 'otro-backend.service').write_text('[Unit]\n')
    nginx = tmp_path / 'etc' / 'nginx' / 'conf.d'
    nginx.mkdir(parents=True)
    (nginx / f'{NOMBRE}.conf').write_text('server {}\n')
    (nginx / 'otro.conf').write_text('server {}\n')
    binfalso = tmp_path / 'bin'
    binfalso.mkdir()
    registro = tmp_path / 'systemctl.log'
    sc = binfalso / 'systemctl'
    sc.write_text(f'#!/usr/bin/env bash\necho "$*" >> "{registro}"\n')
    sc.chmod(0o755)
    return {'tmp': tmp_path, 'prefix': prefix, 'logdir': logdir,
            'logbase': tmp_path / 'var' / 'log',
            'systemd': systemd, 'nginx': nginx, 'bin': binfalso,
            'registro': registro}


def _limpiar(r, stdin=None, nombre=NOMBRE, prefix=None, logdir=None):
    env = {**os.environ, 'PATH': f'{r["bin"]}:{os.environ["PATH"]}'}
    return subprocess.run(
        ['bash', '-c', f'set -Eeuo pipefail; . "{SCRIPT}"; '
         'reinstalar_limpio "$@"', '_', nombre,
         str(prefix or r['prefix']), str(logdir or r['logdir']),
         str(r['systemd']), str(r['nginx']), str(r['logbase'])],
        stdin=stdin, capture_output=True, text=True, timeout=15, env=env)


def _con_tty(r, respuesta, **kw):
    maestro, esclavo = pty.openpty()
    try:
        os.write(maestro, respuesta.encode() + b'\n')
        return _limpiar(r, stdin=esclavo, **kw)
    finally:
        os.close(esclavo)
        os.close(maestro)


def _nada_borrado(r):
    assert (r['prefix'] / 'venv' / 'bin' / 'python').exists()
    assert (r['prefix'] / 'frontend' / 'node_modules').exists()
    assert (r['prefix'] / 'frontend' / '.next').exists()
    assert (r['logdir'] / 'app.log').exists()
    for u in UNIDADES:
        assert (r['systemd'] / f'{u}.service').exists()
    assert (r['nginx'] / f'{NOMBRE}.conf').exists()
    assert not r['registro'].exists(), 'no debe llamar a systemctl'


def _intactos(r):
    for rel in INTACTOS:
        assert (r['prefix'] / rel).read_text() == f'intacto {rel}\n', rel
    assert (r['systemd'] / 'otro-backend.service').exists()
    assert (r['nginx'] / 'otro.conf').exists()


def test_sin_tty_aborta(raiz):
    res = _limpiar(raiz, stdin=subprocess.DEVNULL)
    assert res.returncode != 0
    assert 'terminal' in res.stderr
    _nada_borrado(raiz)
    _intactos(raiz)


def test_respuesta_incorrecta_aborta(raiz):
    res = _con_tty(raiz, 'otro')
    assert res.returncode != 0
    _nada_borrado(raiz)
    _intactos(raiz)


def test_muestra_la_lista_antes_de_preguntar(raiz):
    res = _con_tty(raiz, 'no')
    salida = res.stdout + res.stderr
    for esperado in (*UNIDADES, f'{NOMBRE}.conf', 'venv', 'node_modules',
                     '.next', str(raiz['logdir'])):
        assert esperado in salida, esperado
    assert f'Escribe el nombre de la instalación ({NOMBRE}) para confirmar' in salida


def test_respuesta_correcta_borra_solo_lo_listado(raiz):
    res = _con_tty(raiz, NOMBRE)
    assert res.returncode == 0, res.stdout + res.stderr
    p = raiz['prefix']
    assert not (p / 'venv').exists()
    assert not (p / 'frontend' / 'node_modules').exists()
    assert not (p / 'frontend' / '.next').exists()
    assert not raiz['logdir'].exists()
    for u in UNIDADES:
        assert not (raiz['systemd'] / f'{u}.service').exists()
    assert not (raiz['nginx'] / f'{NOMBRE}.conf').exists()
    llamadas = raiz['registro'].read_text()
    for u in UNIDADES:
        assert u in llamadas
    assert 'daemon-reload' in llamadas
    _intactos(raiz)


def test_enlace_en_el_prefijo_no_se_sigue(raiz):
    # frontend/node_modules como enlace a algo de fuera: se quita el enlace,
    # nunca su destino.
    fuera = raiz['tmp'] / 'fuera'
    fuera.mkdir()
    (fuera / 'sensible').write_text('no-tocar\n')
    nm = raiz['prefix'] / 'frontend' / 'node_modules'
    import shutil
    shutil.rmtree(nm)
    nm.symlink_to(fuera)
    res = _con_tty(raiz, NOMBRE)
    assert res.returncode == 0, res.stdout + res.stderr
    assert (fuera / 'sensible').read_text() == 'no-tocar\n'
    _intactos(raiz)


@pytest.mark.parametrize('caso', ['nombre_vacio', 'nombre_invalido',
                                  'prefijo_raiz', 'prefijo_vacio',
                                  'logdir_raiz', 'logdir_otro_nombre',
                                  'logdir_fuera_de_var_log'])
def test_rutas_inesperadas_abortan_sin_borrar(raiz, caso):
    kw = {
        'nombre_vacio': {'nombre': ''},
        'nombre_invalido': {'nombre': '../x'},
        'prefijo_raiz': {'prefix': '/'},
        'prefijo_vacio': {'prefix': raiz['tmp'] / 'vacio'},
        'logdir_raiz': {'logdir': '/'},
        'logdir_otro_nombre': {'logdir': raiz['tmp'] / 'var' / 'log'},
        # SEG-3: termina en /<nombre> pero no está bajo la base de registros.
        'logdir_fuera_de_var_log': {'logdir': raiz['tmp'] / 'srv' / NOMBRE},
    }[caso]
    if caso == 'prefijo_vacio':
        (raiz['tmp'] / 'vacio').mkdir()
    if caso == 'logdir_fuera_de_var_log':
        (raiz['tmp'] / 'srv' / NOMBRE).mkdir(parents=True)
    res = _con_tty(raiz, kw.get('nombre', NOMBRE), **kw)
    assert res.returncode != 0
    _nada_borrado(raiz)
    _intactos(raiz)


def test_logdir_en_subcarpeta_de_var_log_se_acepta(raiz):
    import shutil
    nuevo = raiz['logbase'] / 'apps' / NOMBRE
    nuevo.parent.mkdir(parents=True)
    shutil.move(str(raiz['logdir']), str(nuevo))
    res = _con_tty(raiz, NOMBRE, logdir=nuevo)
    assert res.returncode == 0, res.stdout + res.stderr
    assert not nuevo.exists()


def test_revalida_antes_de_borrar(raiz):
    # SEG-2: entre la validación y el rm, frontend/ pasa a ser un enlace a
    # algo de fuera (el systemctl falso lo cambia en daemon-reload). El
    # contenido de fuera no se borra.
    fuera = raiz['tmp'] / 'fuera'
    (fuera / 'node_modules').mkdir(parents=True)
    (fuera / 'node_modules' / 'sensible').write_text('no-tocar\n')
    (fuera / '.next').mkdir()
    (fuera / '.next' / 'sensible').write_text('no-tocar\n')
    frontend = raiz['prefix'] / 'frontend'
    sc = raiz['bin'] / 'systemctl'
    sc.write_text(
        '#!/usr/bin/env bash\n'
        f'echo "$*" >> "{raiz["registro"]}"\n'
        'if [[ "$1" == daemon-reload ]]; then\n'
        f'  mv "{frontend}" "{raiz["tmp"]}/frontend.movido"\n'
        f'  ln -s "{fuera}" "{frontend}"\n'
        'fi\n')
    res = _con_tty(raiz, NOMBRE)
    assert (fuera / 'node_modules' / 'sensible').read_text() == 'no-tocar\n'
    assert (fuera / '.next' / 'sensible').read_text() == 'no-tocar\n'
    assert res.returncode != 0
    assert 'enlace' in res.stderr


def test_install_pasa_la_base_de_registros():
    texto = INSTALL.read_text()
    assert 'LOGDIR_BASE="/var/log"' in texto
    assert '"$NGINX_CONF_DIR" "$LOGDIR_BASE"' in texto


# --- integración con install.sh ----------------------------------------------

@NO_ROOT
@pytest.mark.parametrize('opcion', ['--force', '--reinstall'])
def test_install_acepta_force(opcion):
    r = subprocess.run(['bash', str(INSTALL), opcion], capture_output=True,
                       text=True, timeout=10, stdin=subprocess.DEVNULL)
    assert r.returncode == 1, r.stderr
    assert 'Opción desconocida' not in r.stderr
    assert 'root' in r.stderr


@NO_ROOT
def test_install_sin_force_no_pregunta():
    r = subprocess.run(['bash', str(INSTALL)], capture_output=True, text=True,
                       timeout=10, stdin=subprocess.DEVNULL)
    assert 'para confirmar' not in r.stdout + r.stderr
    texto = INSTALL.read_text()
    # La limpieza solo se invoca dentro de la rama de --force.
    assert 'if (( FORCE )); then' in texto
    bloque = texto.split('if (( FORCE )); then', 1)[1].split('\nfi\n', 1)[0]
    assert 'reinstalar_limpio' in bloque
    assert texto.count('reinstalar_limpio') == 1
