"""Plantilla de Nginx: ningún `location` con `proxy_pass` deja pasar `Remote-*` (FNC-027).

`proxy_set_header` en un `location` anula TODOS los del nivel `server`; si uno
define los suyos sin repetir el borrado, el cliente podría inyectar
`Remote-Email` y entrar como otro usuario (FNC-004).
"""
import re
from pathlib import Path

import pytest

PLANTILLA = Path(__file__).resolve().parents[2] / 'deploy' / 'nginx.conf.tmpl'
REMOTAS = ('remote-email', 'remote-name', 'remote-groups')
FIJAS = ('host', 'x-real-ip', 'x-forwarded-for', 'x-forwarded-proto')
_SET = re.compile(r'proxy_set_header\s+(\S+)\s+("(?:[^"]*)"|\S+?)\s*;')


def _texto():
    return '\n'.join(l.split('#', 1)[0]
                     for l in PLANTILLA.read_text().splitlines())


def _bloque(texto, inicio):
    """Contenido entre la llave que abre en `inicio` y su cierre."""
    nivel = 0
    for i in range(inicio, len(texto)):
        if texto[i] == '{':
            nivel += 1
        elif texto[i] == '}':
            nivel -= 1
            if nivel == 0:
                return texto[texto.index('{', inicio) + 1:i]
    raise AssertionError('llaves sin cerrar')


def _cabeceras(cuerpo):
    return {n.lower(): v for n, v in _SET.findall(cuerpo)}


def _locations():
    texto = _texto()
    server = _bloque(texto, texto.index('server {'))
    locs = []
    for m in re.finditer(r'location\s+(\S+(?:\s+\S+)?)\s*\{', server):
        cuerpo = _bloque(server, m.start())
        locs.append((m.group(1), cuerpo))
    # Cabeceras del nivel server: lo que queda sin los bloques location.
    sin_locs = server
    for _, cuerpo in locs:
        sin_locs = sin_locs.replace(cuerpo, '')
    return _cabeceras(sin_locs), [(n, c) for n, c in locs
                                  if 'proxy_pass' in c]


def test_hay_locations_con_proxy_pass():
    _, locs = _locations()
    assert {n for n, _ in locs} >= {'/api/', '/'}


def _casos():
    _, locs = _locations()
    return [n for n, _ in locs]


@pytest.mark.parametrize('nombre', _casos())
def test_location_limpia_remote_y_fija_las_cabeceras_del_proxy(nombre):
    del_server, locs = _locations()
    cuerpo = dict(locs)[nombre]
    propias = _cabeceras(cuerpo)
    # Con cabeceras propias, las del server no se heredan.
    efectivas = propias if propias else del_server
    for cab in REMOTAS:
        assert efectivas.get(cab) == '""', f'{nombre}: no borra {cab}'
    for cab in FIJAS:
        assert cab in efectivas, f'{nombre}: no fija {cab}'
