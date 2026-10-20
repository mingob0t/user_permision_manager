"""Accesos otorgados: modelo, reglas y servicio de otorgar y revocar (FNC-054).

Uso desde otro módulo (FNC-055, FNC-057, FNC-058):
- `services.otorgar(...)` y `services.revocar(...)` dentro de la transacción
  del llamador, que hace el `commit`;
- `ErrorDeAcceso.respuesta` para responder el error de contrato.
"""
