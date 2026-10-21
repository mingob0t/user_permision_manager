"""Destino seguro de los conectores que salen por red (FNC-051, SEC-CON-06).

- El host ya viene de la lista blanca (`Destino`, SEC-CON-07), pero un nombre
  autorizado podría resolver a una dirección interna (DNS *rebinding*). Por
  eso se resuelve aquí y **se conecta a la IP validada**, sin volver a
  resolver.
- Se rechaza el destino si **alguna** dirección resuelta no es pública:
  privada, de loopback, *link-local*, *site-local* (`fec0::/10`), multicast, sin especificar, reservada o
  compartida (CGNAT), en IPv4 e IPv6; también las IPv4 incrustadas en
  IPv4-mapeada, NAT64 (`64:ff9b::/96`) y 6to4.
- Un fallo de DNS es transitorio (`ErrorResolucion`); una dirección no
  pública es permanente (`DestinoNoPermitido`).
"""
import ipaddress
import socket

PREFIJO_NAT64 = ipaddress.ip_network('64:ff9b::/96')
SEPARADOR_AMBITO = '%'


class DestinoNoPermitido(Exception):
    """El host resuelve a una dirección no pública (permanente)."""


class ErrorResolucion(Exception):
    """El DNS no respondió o no dio direcciones (transitorio)."""


def _incrustada(ip):
    """IPv4 que lleva una IPv6 de transición, o `None`."""
    if ip.version != 6:
        return None
    if ip.ipv4_mapped is not None:
        return ip.ipv4_mapped
    if ip.sixtofour is not None:
        return ip.sixtofour
    if ip.teredo is not None:
        return ip.teredo[1]
    if ip in PREFIJO_NAT64:
        return ipaddress.IPv4Address(int(ip) & 0xFFFFFFFF)
    return None


def ip_permitida(direccion):
    """`True` solo para una dirección pública y enrutable."""
    ip = ipaddress.ip_address(direccion)
    incrustada = _incrustada(ip)
    if incrustada is not None and not ip_permitida(incrustada):
        return False
    site_local = ip.version == 6 and ip.is_site_local  # fec0::/10
    return not (ip.is_multicast or ip.is_unspecified or ip.is_loopback
                or ip.is_link_local or ip.is_reserved or ip.is_private
                or site_local or not ip.is_global)


def resolver_seguro(host, puerto, getaddrinfo=socket.getaddrinfo):
    """Direcciones públicas de `host` (sin repetir, en el orden del DNS)."""
    try:
        informacion = getaddrinfo(host, puerto, type=socket.SOCK_STREAM)
    except (OSError, UnicodeError):
        raise ErrorResolucion() from None
    direcciones = []
    for _familia, _tipo, _protocolo, _nombre, destino in informacion:
        ip = ipaddress.ip_address(destino[0].split(SEPARADOR_AMBITO)[0])
        if not ip_permitida(ip):
            raise DestinoNoPermitido()
        if str(ip) not in direcciones:
            direcciones.append(str(ip))
    if not direcciones:
        raise ErrorResolucion()
    return tuple(direcciones)
