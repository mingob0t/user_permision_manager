"""Guardia de rutas (FNC-020): ninguna ruta /api/v1 queda sin clasificar.

Si se agrega un endpoint /api/v1, estas pruebas fallan hasta que se añada su
caso en `tests/matriz_proteccion.py`. Fuera de /api/v1 no puede haber rutas
(los blueprints heredados se retiraron en FNC-027).
"""

from collections import Counter

from tests.matriz_proteccion import CASOS

PREFIJO_API = '/api/v1'
METODOS_IMPLICITOS = {'HEAD', 'OPTIONS'}


def _rutas(app):
    """(método, regla, blueprint) de cada ruta registrada."""
    for regla in app.url_map.iter_rules():
        blueprint = regla.endpoint.split('.')[0]
        for metodo in sorted(regla.methods - METODOS_IMPLICITOS):
            yield metodo, regla.rule, blueprint


def test_toda_ruta_api_v1_esta_en_la_matriz(app):
    clasificadas = {caso.clave for caso in CASOS}
    sin_clasificar = sorted(
        (metodo, regla) for metodo, regla, _ in _rutas(app)
        if regla.startswith(PREFIJO_API + '/') and (metodo, regla) not in clasificadas)
    assert not sin_clasificar, (
        f'Rutas /api/v1 sin caso en tests/matriz_proteccion.py: {sin_clasificar}')


def test_la_matriz_no_tiene_rutas_inexistentes_ni_repetidas(app):
    existentes = {(m, r) for m, r, _ in _rutas(app)}
    claves = [caso.clave for caso in CASOS]
    repetidas = [c for c, n in Counter(claves).items() if n > 1]
    inexistentes = sorted(set(claves) - existentes)
    assert not repetidas, f'Casos repetidos: {repetidas}'
    assert not inexistentes, f'Casos de rutas que ya no existen: {inexistentes}'


def test_fuera_de_api_v1_no_hay_rutas(app):
    otras = sorted(
        (metodo, regla) for metodo, regla, _ in _rutas(app)
        if not regla.startswith(PREFIJO_API + '/'))
    assert not otras, f'Rutas fuera de /api/v1 sin retirar o sin clasificar: {otras}'
