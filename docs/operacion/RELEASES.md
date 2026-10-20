# Releases y versionado

- **Versionado semántico** `MAYOR.MENOR.PARCHE`:
  - MAYOR: cambios incompatibles (API, datos, configuración obligatoria nueva).
  - MENOR: funcionalidades nuevas compatibles.
  - PARCHE: correcciones.
- **Etiqueta** `vX.Y.Z` en cada release, sobre la versión desplegada.
- **`CHANGELOG.md`** en la raíz, con una sección por versión: Agregado, Cambiado, Corregido, Eliminado, Seguridad. Cada línea referencia su tarea (`FNC-###`/`DIS-###`).

## Checklist de release

- [ ] Todas las tareas incluidas están en `Hecha`, con pruebas y revisión.
- [ ] `auditor-seguridad` en modo proyecto, sin hallazgos Críticos ni Altos abiertos.
- [ ] Migraciones de BD probadas en pruebas, con un plan de reversión.
- [ ] Despliegue: respaldo, `venv/bin/alembic upgrade head` y después reiniciar backend y worker (`systemctl restart <nombre>-backend <nombre>-worker`, FNC-067); reversión con `alembic downgrade <revisión anterior>` (`docs/backend/README.md` §7).
- [ ] Variables nuevas o cambiadas registradas en `docs/configuracion/` y en `.env.example`.
- [ ] Respaldo previo hecho.
- [ ] `CHANGELOG.md` y la etiqueta actualizados.

## Notas por cambio

- FNC-067: Redis pasa a obligatorio (con `REDIS_PASS`) y se instala la unidad `<nombre>-worker`; `preflight.sh` bloquea sin Redis.
- FNC-042: revisar las cuentas `administrador` y `admin_area` heredadas antes de desplegar (el directorio y el SSO ya no asignan ni quitan roles; las elevadas antes por LDAP/SSO conservan el rol).

## Historial

| Versión | Fecha | Entorno | Notas | Responsable |
|---|---|---|---|---|
