# FNC-076 — Mover _trusted_proxy de api/auth.py a app/utils/

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 4 |
| **Módulo / Área** | utils |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-14 |

## Contexto
- `audit/ip_cliente.py` importa `_trusted_proxy` (privada) de `api/auth.py` con importación diferida: el servicio depende de un módulo de rutas.
- Origen: revisión de FNC-047.

## Criterios de aceptación
- [ ] `_trusted_proxy` vive en `app/utils/` y la usan `api/auth.py` y `audit/ip_cliente.py`
- [ ] Sin cambio de comportamiento: pruebas de SSO y de `tests/audit/` en verde
