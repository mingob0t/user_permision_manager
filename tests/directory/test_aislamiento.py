"""SEC-LDAP-01 (FNC-043): solo `app/modules/directory/` importa `ldap3`."""
import pathlib
import re

RAIZ_APP = pathlib.Path(__file__).resolve().parents[2] / 'app'
PAQUETE_DIRECTORIO = RAIZ_APP / 'modules' / 'directory'
IMPORTA_LDAP3 = re.compile(r'^\s*(?:from|import)\s+ldap3\b', re.MULTILINE)


def test_solo_el_paquete_del_directorio_importa_ldap3():
    fuera = sorted(
        str(ruta.relative_to(RAIZ_APP)) for ruta in RAIZ_APP.rglob('*.py')
        if PAQUETE_DIRECTORIO not in ruta.parents
        and IMPORTA_LDAP3.search(ruta.read_text(encoding='utf-8')))
    assert fuera == []


def test_sin_cert_none_en_la_app():
    """SEC-LDAP-02: ningún TLS sin validar (`CERT_NONE`) en el código."""
    con_cert_none = sorted(
        str(ruta.relative_to(RAIZ_APP)) for ruta in RAIZ_APP.rglob('*.py')
        if 'CERT_NONE' in ruta.read_text(encoding='utf-8'))
    assert con_cert_none == []
