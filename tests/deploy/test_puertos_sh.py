"""Puertos de backend y frontend configurables (FNC-127): `deploy/puertos.sh`.

Precedencia: opción (`--web-port`/`--api-port`) > variable de entorno > `.env`
del prefijo > valor por defecto (3000/5001). El `.env` es SINTÉTICO, en un
directorio temporal: nunca se lee el real.
"""
import os
import re
import subprocess
from pathlib import Path

import pytest

DEPLOY = Path(__file__).resolve().parents[2] / 'deploy'
SCRIPT = DEPLOY / 'puertos.sh'
INSTALL = DEPLOY / 'install.sh'
PLANTILLAS = ('backend.service.tmpl', 'frontend.service.tmpl',
              'worker.service.tmpl', 'nginx.conf.tmpl')
NO_ROOT = pytest.mark.skipif(os.geteuid() == 0,
                             reason='no se ejecuta install.sh como root')


def _bash(codigo, *args):
    return subprocess.run(
        ['bash', '-c', f'set -Eeuo pipefail; . "{SCRIPT}"; {codigo}', '_', *args],
        capture_output=True, text=True, timeout=10)


def _render_de_install():
    """Texto de la función render() tal como está en install.sh."""
    m = re.search(r'^render\(\) \{\n.*?^\}\n', INSTALL.read_text(),
                  re.MULTILINE | re.DOTALL)
    assert m, 'install.sh debe definir render()'
    return m.group(0)


def _render(plantilla, web, api):
    """Renderiza una plantilla con el render() real de install.sh."""
    codigo = (
        f'. "{DEPLOY / "servicio_bd.sh"}"; . "{SCRIPT}"; '
        'APP_NAME=portal APP_TITLE=Portal PREFIX=/opt/portal '
        'LOGDIR=/var/log/portal SVC_USER=svc SVC_GROUP=svc DOMAIN= '
        f'DB_SERVICE=mariadb.service WEB_PORT={web} API_PORT={api}; '
        f'{_render_de_install()}'
        f'render "{DEPLOY / plantilla}"')
    r = subprocess.run(['bash', '-c', codigo], capture_output=True,
                       text=True, timeout=10)
    assert r.returncode == 0, r.stderr
    return r.stdout


# --- Render con puertos personalizados --------------------------------------

@pytest.mark.parametrize('plantilla', PLANTILLAS)
def test_render_sin_marcadores_sobrantes(plantilla):
    salida = _render(plantilla, 3100, 5101)
    assert not re.findall(r'@[A-Z_]+@', salida)


def test_nginx_y_unidades_usan_el_mismo_puerto():
    nginx = _render('nginx.conf.tmpl', 3100, 5101)
    backend = _render('backend.service.tmpl', 3100, 5101)
    frontend = _render('frontend.service.tmpl', 3100, 5101)
    assert 'server 127.0.0.1:5101;' in nginx
    assert 'server 127.0.0.1:3100;' in nginx
    assert '--bind 127.0.0.1:5101' in backend
    assert 'Environment=PORT=3100' in frontend
    # El SSR de Next llega al backend por el mismo puerto.
    assert 'Environment=BACKEND_URL=http://localhost:5101' in frontend
    # El bind sigue en loopback.
    assert 'Environment=HOSTNAME=127.0.0.1' in frontend
    for texto in (nginx, backend, frontend):
        assert '5001' not in texto and ':3000' not in texto


def test_por_defecto_conserva_3000_y_5001():
    r = _bash('printf "%s %s" "$WEB_PORT_POR_DEFECTO" "$API_PORT_POR_DEFECTO"')
    assert r.stdout == '3000 5001'


# --- Validación ---------------------------------------------------------------

@pytest.mark.parametrize('valor', ['1024', '3100', '65535'])
def test_puerto_valido(valor):
    assert _bash('puerto_servicio_valido "$1"', valor).returncode == 0


@pytest.mark.parametrize('valor', ['80', '1023', '70000', '65536', 'abc', '',
                                   '30 00', '3000;reboot', '-1'])
def test_puerto_invalido(valor):
    assert _bash('puerto_servicio_valido "$1"', valor).returncode != 0


@NO_ROOT
@pytest.mark.parametrize('args', [
    ['--web-port', '80'], ['--api-port', '70000'], ['--web-port', 'abc'],
    ['--web-port', '4000', '--api-port', '4000'],
])
def test_install_rechaza_puertos(args):
    r = subprocess.run(['bash', str(INSTALL), *args], capture_output=True,
                       text=True, timeout=10)
    assert r.returncode == 2, r.stderr
    assert 'root' not in r.stderr


@NO_ROOT
def test_install_rechaza_puerto_por_entorno():
    r = subprocess.run(['bash', str(INSTALL)], capture_output=True, text=True,
                       timeout=10, env={**os.environ, 'WEB_PORT': 'abc'})
    assert r.returncode == 2
    assert 'WEB_PORT' in r.stderr


@NO_ROOT
def test_install_rechaza_iguales_por_entorno_y_opcion():
    r = subprocess.run(['bash', str(INSTALL), '--api-port', '3100'],
                       capture_output=True, text=True, timeout=10,
                       env={**os.environ, 'WEB_PORT': '3100'})
    assert r.returncode == 2


@NO_ROOT
def test_install_acepta_puertos_validos():
    # Pasa la validación y se detiene en la comprobación de root.
    r = subprocess.run(['bash', str(INSTALL), '--web-port', '3100',
                        '--api-port', '5101'], capture_output=True, text=True,
                       timeout=10)
    assert r.returncode == 1
    assert 'root' in r.stderr


# --- .env y precedencia -------------------------------------------------------

def _env(tmp_path, contenido):
    f = tmp_path / '.env'
    f.write_text(contenido)
    return f


def test_puerto_desde_env(tmp_path):
    f = _env(tmp_path, 'SECRET_KEY=no-se-imprime\nWEB_PORT="3100"\n')
    r = _bash('resolver_puerto "" "$1" WEB_PORT 3000', str(f))
    assert r.returncode == 0
    assert r.stdout == '3100'
    assert 'no-se-imprime' not in r.stdout + r.stderr


def test_opcion_gana_sobre_env(tmp_path):
    f = _env(tmp_path, 'API_PORT=5101\n')
    r = _bash('resolver_puerto 5201 "$1" API_PORT 5001', str(f))
    assert r.stdout == '5201'


def test_sin_valor_usa_por_defecto(tmp_path):
    f = _env(tmp_path, '# WEB_PORT=3100\nOTRA=1\n')
    r = _bash('resolver_puerto "" "$1" WEB_PORT 3000', str(f))
    assert r.stdout == '3000'


def test_sin_env_usa_por_defecto(tmp_path):
    r = _bash('resolver_puerto "" "$1" WEB_PORT 3000', str(tmp_path / 'no'))
    assert r.stdout == '3000'


@pytest.mark.parametrize('valor', ['80', 'abc', '$(reboot)'])
def test_env_invalido_falla(tmp_path, valor):
    f = _env(tmp_path, f'WEB_PORT={valor}\n')
    r = _bash('resolver_puerto "" "$1" WEB_PORT 3000', str(f))
    assert r.returncode != 0
    assert r.stdout == ''


def test_env_enlace_no_se_sigue(tmp_path):
    real = _env(tmp_path, 'WEB_PORT=3100\n')
    enlace = tmp_path / 'enlace.env'
    enlace.symlink_to(real)
    r = _bash('resolver_puerto "" "$1" WEB_PORT 3000', str(enlace))
    assert r.stdout == '3000'
