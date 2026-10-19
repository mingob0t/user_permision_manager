"""Comparación de DN normalizados (FNC-041, SEC-LDAP-04).

Cada RDN se compara como conjunto de AVA (`a=1+b=2` = `b=2+a=1`), con el
tipo en minúsculas y el valor desescapado en minúsculas. Solo se quitan los
espacios sin escapar; un espacio escapado (`\\ ` o `\\20`) es significativo,
así `ou=\\ grupos` no pasa por `ou=grupos`.
"""
import re

from ldap3.core.exceptions import LDAPInvalidDnError
from ldap3.utils.dn import parse_dn

# `\` seguido de dos dígitos hexadecimales o de un carácter (RFC 4514).
_ESCAPE_DN = re.compile(r'\\([0-9a-fA-F]{2}|.)')
SEPARADOR_MULTIVALOR = '+'
# Espacios sin escapar al final (un `\ ` final se conserva).
_ESPACIOS_FINALES = re.compile(r'(?<!\\) +$')


def _desescapar(valor):
    def reemplazo_escape(coincidencia):
        texto = coincidencia.group(1)
        return chr(int(texto, 16)) if len(texto) == 2 else texto
    return _ESCAPE_DN.sub(reemplazo_escape, valor)


def _sin_espacios(valor):
    """Quita espacios sin escapar antes de desescapar."""
    return _ESPACIOS_FINALES.sub('', valor.lstrip(' '))


def normalizar_dn(dn):
    """Tupla de RDN (cada uno, tupla ordenada de AVA); `None` si no es DN."""
    if not dn:
        return None
    try:
        partes = parse_dn(dn)
    except LDAPInvalidDnError:
        return None
    rdns, actual = [], []
    for atributo, valor, separador in partes:
        actual.append((atributo.strip().lower(),
                       _desescapar(_sin_espacios(valor)).lower()))
        if separador != SEPARADOR_MULTIVALOR:
            rdns.append(tuple(sorted(actual)))
            actual = []
    return tuple(rdns)


def mismo_dn(uno, otro):
    normal = normalizar_dn(uno)
    return normal is not None and normal == normalizar_dn(otro)


def bajo_base(dn, base, incluir_base=False):
    """`True` si `dn` está debajo de `base` (o es ella, con `incluir_base`)."""
    rdns, rdns_base = normalizar_dn(dn), normalizar_dn(base)
    if not rdns or not rdns_base or len(rdns) < len(rdns_base):
        return False
    if len(rdns) == len(rdns_base) and not incluir_base:
        return False
    return rdns[-len(rdns_base):] == rdns_base
