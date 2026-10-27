# FNC-128 — Despliegue sin Vaultwarden

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | infra |
| **Fase** | 6 |
| **Módulo / Área** | despliegue |
| **Prioridad** | Media |
| **Estatus** | Hecha |
| **Rama** | `fnc/FNC-128-vaultwarden-opcional` |
| **Creada** | 2026-10-27 |

## Decisión del dueño (2026-10-27)
- El portal no usa Vaultwarden por ahora; solo Authelia (más OpenLDAP para los grupos).
- Se desactiva por configuración (todas las `VAULTWARDEN_*` vacías), sin retirar código.
- Efecto: los conectores API/SSH/BD fallan cerrado (sin credencial); el bind LDAP usa `LDAP_BIND_PASSWORD` en el `.env`.
- Pendiente del dueño: revisar para qué se necesitaba Vaultwarden y decidir entre retirar conectores y Vaultwarden, o conectores con credenciales locales.

## Cambio
- `.env.example`: `VAULTWARDEN_TIMEOUT_SECONDS` vacía (antes `5`). El código usa 5 s por defecto (`app/modules/secretos/configuracion.py`), así que no cambia el comportamiento; con valor, `deploy/secretos.sh` daba Vaultwarden por «en uso» y exigía las demás.
- `VARIABLES.md` e `HISTORIAL.md` actualizados.

## Verificación
- `pytest tests/deploy` y `tests/secretos` (ver bitácora).
