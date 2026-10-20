"""Solicitudes de acceso (FNC-056, contrato `solicitudes.md`).

- `catalogo.py`: plataformas solicitables del actor (P1) y su estado.
- `services.crear(...)`: reglas, alta y auditoría en la transacción del
  llamador; el endpoint hace el `commit` y después avisa (FNC-048).
- La bandeja y la decisión son de FNC-057.
"""
