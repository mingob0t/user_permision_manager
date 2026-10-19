"""Ejecutor de aprovisionamiento: cola, worker, reintentos y bitácora (FNC-049).

Uso desde otro módulo (p. ej. FNC-054):
- `queue.encolar(...)` dentro de la transacción del cambio de negocio;
- `manejadores.registrar_manejador(on_success=..., on_failure=...)`.
"""
from app.modules.provisioning.ldap_provider import ProveedorLdap
from app.modules.provisioning.providers import registrar_proveedor
from app.modules.provisioning.tipos import PROVEEDOR_LDAP

# `conector` lo registra FNC-050; mientras tanto da `conector_no_disponible`.
registrar_proveedor(PROVEEDOR_LDAP, ProveedorLdap)
