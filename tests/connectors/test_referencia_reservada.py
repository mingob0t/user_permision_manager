"""Regresión B3 de auditor-seguridad sobre FNC-068: el ejecutor no resuelve
como credencial de conector la referencia del bind LDAP."""
from app import db
from app.modules.connectors import credenciales
from app.modules.provisioning.ejecucion import ejecutar_trabajo
from app.modules.provisioning.tipos import (ESTADO_FALLIDO, OPERACION_OTORGAR,
                                            RESULTADO_ERROR_PERMANENTE)
from tests.connectors.test_proveedor_conector import encolar, trabajo

REFERENCIA_BIND = 'pokemon/produccion/LDAP_BIND_PASSWORD'


def test_b3_el_ejecutor_no_resuelve_la_referencia_del_bind(conector_noop,
                                                           monkeypatch):
    plataforma, configuracion, usuario = conector_noop
    configuracion.credential_ref = REFERENCIA_BIND
    db.session.commit()
    monkeypatch.setenv('LDAP_BIND_PASSWORD_REF', REFERENCIA_BIND)
    llamadas = []
    monkeypatch.setattr(credenciales, 'resolver_credencial',
                        lambda ref: llamadas.append(ref))
    t = encolar(plataforma, usuario, OPERACION_OTORGAR, 'ref-bind')
    assert ejecutar_trabajo(t) == ESTADO_FALLIDO
    assert trabajo(t).attempts[0].result == RESULTADO_ERROR_PERMANENTE
    assert llamadas == []
