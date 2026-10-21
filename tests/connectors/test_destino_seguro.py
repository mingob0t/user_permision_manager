"""Destino seguro de los conectores HTTP (FNC-051): resolución de DNS y
rechazo de IP no públicas (DNS rebinding, SEC-CON-06)."""
import socket

import pytest

from app.modules.connectors.destino_seguro import (DestinoNoPermitido,
                                                   ErrorResolucion,
                                                   ip_permitida,
                                                   resolver_seguro)


def ip(*partes):
    return '.'.join(str(p) for p in partes)


def respuesta(*direcciones):
    def getaddrinfo(host, puerto, **_):
        return [(socket.AF_INET6 if ':' in d else socket.AF_INET,
                 socket.SOCK_STREAM, 6, '', (d, puerto)) for d in direcciones]
    return getaddrinfo


PUBLICAS = [ip(8, 8, 8, 8), '2606:4700:4700::1111']
NO_PUBLICAS = [
    ip(10, 0, 0, 5), ip(172, 16, 0, 1), ip(192, 168, 1, 1),   # privadas
    ip(127, 0, 0, 1), '::1',                                   # loopback
    ip(169, 254, 169, 254), 'fe80::1',                         # link-local
    ip(224, 0, 0, 1), 'ff02::1',                               # multicast
    ip(0, 0, 0, 0), '::',                                      # sin especificar
    ip(100, 64, 0, 1),                                         # CGNAT
    ip(240, 0, 0, 1),                                          # reservada
    ip(192, 0, 2, 10),                                         # documentación
    'fc00::1',                                                 # ULA
    '::ffff:' + ip(10, 0, 0, 5),                               # IPv4 mapeada
    '::ffff:' + ip(127, 0, 0, 1),
    '64:ff9b::' + '0a00:0005',                                 # NAT64 a privada
    '2002:0a00:0005::1',                                       # 6to4 a privada
]


@pytest.mark.parametrize('direccion', PUBLICAS)
def test_acepta_ip_publicas(direccion):
    assert ip_permitida(direccion)


@pytest.mark.parametrize('direccion', NO_PUBLICAS)
def test_rechaza_ip_no_publicas(direccion):
    assert not ip_permitida(direccion)


@pytest.mark.parametrize('direccion', NO_PUBLICAS)
def test_resolver_rechaza_si_resuelve_a_ip_no_publica(direccion):
    with pytest.raises(DestinoNoPermitido):
        resolver_seguro('erp.pruebas.local', 443, respuesta(direccion))


def test_resolver_rechaza_si_alguna_de_varias_no_es_publica():
    with pytest.raises(DestinoNoPermitido):
        resolver_seguro('erp.pruebas.local', 443,
                        respuesta(PUBLICAS[0], ip(10, 0, 0, 5)))


def test_resolver_devuelve_ips_publicas_sin_repetir():
    ips = resolver_seguro('erp.pruebas.local', 443,
                          respuesta(PUBLICAS[0], PUBLICAS[0], PUBLICAS[1]))
    assert ips == tuple(PUBLICAS)


def test_resolver_ignora_el_ambito_de_ipv6():
    with pytest.raises(DestinoNoPermitido):
        resolver_seguro('erp.pruebas.local', 443, respuesta('fe80::1%eth0'))


def test_dns_caido_es_error_de_resolucion():
    def falla(*_, **__):
        raise socket.gaierror('sin dns')
    with pytest.raises(ErrorResolucion):
        resolver_seguro('erp.pruebas.local', 443, falla)


def test_sin_direcciones_es_error_de_resolucion():
    with pytest.raises(ErrorResolucion):
        resolver_seguro('erp.pruebas.local', 443, respuesta())
