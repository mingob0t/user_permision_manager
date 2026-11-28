# DIS-165 — Alta de área compatible con «área activa requiere admin»

| Campo | Valor |
|---|---|
| **Carril** | Diseño |
| **Plataforma** | web |
| **Fase** | 8 |
| **Estatus** | Hecha |
| **Vinculada a** | FNC-220 (backend: 409 `area_sin_admin`) |
| **Creada / Aprobada / Finalizada** | 2026-11-28 (detectado al revisar FNC-220: el alta del superadmin daba 409) |

## Cambios
- `areas/area-form.tsx`: el superadmin crea el área con `status: 'Inactivo'`, asigna usuarios y administradores y, si hay al menos un admin, la activa (`PUT status: Activo`); sin admin queda Inactiva con un solo aviso «se creó inactiva: asígnale un administrador para poder activarla» (sin el de éxito, que lo taparía; observación de auditor-accesibilidad). El admin de área no cambia (el backend lo deja como admin). La vista previa del estado muestra el que tendrá el área.
- `areas/area-errors.ts`: mensaje de `area_sin_admin` (también lo usa el badge de estado al activar).
- Pruebas en `areas-list.test.tsx` (fallaron antes del cambio).

## Decisiones
- Compatible con y sin FNC-220: se integra antes para no romper el alta.

## Impacto en elementos compartidos
- `mensajeDeError` (áreas): un código más; lo usan el formulario y `EstadoBadgeBoton`.
