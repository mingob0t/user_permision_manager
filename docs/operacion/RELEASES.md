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
- [ ] Despliegue: respaldo, `venv/bin/alembic upgrade head` y después reiniciar el servicio; reversión con `alembic downgrade <revisión anterior>` (`docs/backend/README.md` §7).
- [ ] Variables nuevas o cambiadas registradas en `docs/configuracion/` y en `.env.example`.
- [ ] Respaldo previo hecho.
- [ ] `CHANGELOG.md` y la etiqueta actualizados.

## Historial

| Versión | Fecha | Entorno | Notas | Responsable |
|---|---|---|---|---|
