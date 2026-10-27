# FNC-076 — Mover _trusted_proxy de api/auth.py a app/utils/

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 4 |
| **Módulo / Área** | utils |
| **Prioridad** | Baja |
| **Estatus** | En revisión |
| **Creada** | 2026-10-14 |

## Contexto
- `audit/ip_cliente.py` importa `_trusted_proxy` (privada) de `api/auth.py` con importación diferida: el servicio depende de un módulo de rutas.
- Origen: revisión de FNC-047.

## Criterios de aceptación
- [x] `_trusted_proxy` (ahora `es_proxy_confiable`) vive en `app/utils/` y la usan `api/auth.py` y `audit/ip_cliente.py`
- [x] Sin cambio de comportamiento: pruebas de SSO y de `tests/audit/` en verde

## Impacto en elementos compartidos
- Nuevo compartido: `es_proxy_confiable` en `app/utils/proxy_confiable.py` (lógica idéntica a `_trusted_proxy`, lee `TRUSTED_PROXIES`).
- Usos: `api/auth.py` (`/context`, `/sso`) y `audit/ip_cliente.py` (`ip_cliente`, usada por la auditoría). Se elimina la importación diferida.
- Validar: SSO (`/api/v1/auth/context` y `/sso`) y la IP registrada en auditoría.

## Verificación
- pytest completo (salida a archivo, `echo $?`): código de salida 0; 2397 passed, 15 xfailed (los de seguridad de fase 5, sin tocar). Pruebas de SSO y auditoría en verde. Sin revisor ni auditor-seguridad (no lanzables desde este subagente); no verificado en despliegue real.

## Bitácora
- 2026-10-27: En curso → En revisión. Decisión del orquestador (pendiente de validar en la prueba de concepto): nombre `es_proxy_confiable`, archivo `proxy_confiable.py`; sin cambio de comportamiento ni de variables (`TRUSTED_PROXIES` ya registrada).
