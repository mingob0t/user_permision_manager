# FNC-126 — `.env` fuera de rutas escribibles por la cuenta de servicio

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | infra |
| **Agente** | devops |
| **Fase** | 5 |
| **Módulo / Área** | despliegue |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Rama** | `fnc/FNC-126-env-fuera-del-prefijo` |
| **Creada** | 2026-10-27 |

## Contexto
- Riesgo previo detectado por `auditor-seguridad` al revisar FNC-125.
- El prefijo es de la cuenta de servicio y las unidades leen `<prefijo>/.env` con `EnvironmentFile=` (`backend.service.tmpl:15`, `worker.service.tmpl:26`).
- Quien ya ejecute código como esa cuenta puede cambiar el `.env` por un enlace a un archivo legible solo por root con líneas `CLAVE=valor`, forzar un reinicio y recibir esas variables. No da root directo.

## Objetivo
- `.env` en `/etc/<app>/app.env` (`root:<grupo>`, 640) o `LoadCredential=`; prefijo de root con escritura solo en directorios de datos.
- `revisar_vaultwarden` lee la nueva ruta.
- Migración documentada para instalaciones existentes.

## Resuelto en FNC-129 (2026-10-27, SEG-1)
- Prefijo de root: código, `venv`, `node_modules` y `.next` de root sin escritura de grupo ni otros; `install.sh` lo exige antes de cargar nada.
- La cuenta de servicio solo posee `instance/`, `uploads/`, `storage/`, `backups/` y el logdir.
- `.env` `root:<grupo de servicio>` 640 (sigue en el prefijo, pero la cuenta ya no puede cambiarlo ni sustituirlo, porque el prefijo es de root).
- **Pendiente aquí:** mover el `.env` a `/etc/<app>/app.env` o `LoadCredential=`, `revisar_vaultwarden` con la nueva ruta y la migración documentada.

## Impacto cruzado
- Origen ← FNC-125
