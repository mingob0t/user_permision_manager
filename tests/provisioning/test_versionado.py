"""Regresión (auditor-seguridad, Bloqueante): todo el módulo está versionado.

`.gitignore` ignora cualquier `config.py`; un archivo ignorado del módulo no
llegaría al servidor y el ejecutor no arrancaría.
"""
import pathlib
import subprocess

import pytest

RAIZ = pathlib.Path(__file__).resolve().parents[2]
MODULO = RAIZ / 'app' / 'modules' / 'provisioning'


def _git(*args):
    return subprocess.run(['git', *args], cwd=RAIZ, capture_output=True,
                          text=True)


@pytest.mark.skipif(_git('rev-parse').returncode != 0,
                    reason='fuera de un repositorio git')
def test_ningun_archivo_del_modulo_esta_ignorado():
    archivos = [str(p.relative_to(RAIZ)) for p in sorted(MODULO.glob('*.py'))]
    ignorados = _git('check-ignore', *archivos).stdout.split()
    assert ignorados == []
