"""Gestor de secretos en ejecución: Vaultwarden (FNC-068, ADR-005).

- `configuracion`: variables `VAULTWARDEN_*` y su validación al arrancar.
- `cifrado`: descifrado del lado del cliente del protocolo Bitwarden.
- `vaultwarden`: cliente de solo lectura de una colección.

Lo usan `connectors.credenciales` (credenciales de conectores) y el cliente
del directorio (contraseña de bind con `LDAP_BIND_PASSWORD_REF`).
"""
