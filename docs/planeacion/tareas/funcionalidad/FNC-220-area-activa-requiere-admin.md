# FNC-220 — Un área activa requiere admin de área

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Fase** | 8 |
| **Estatus** | Hecha |
| **Creada / Finalizada** | 2026-11-28 |
| **Rama** | `fnc/FNC-220-area-activa-requiere-admin` (desde la de FNC-219) |

## Contexto
- Regla general del dueño: «una área no se puede activar si no tiene admin».

## Cambios
- `areas/api.py`: `POST /areas` activa sin admin (y sin ser admin de área quien crea) y `PUT` de `Inactivo` a `Activo` sin `area.admins` → `409 area_sin_admin` (`AREA_SIN_ADMIN` en `api/helpers.py`); `validacion.py`: `ESTADO_ACTIVO`/`ESTADO_INACTIVO`.
- `bulk_import/services.py`: las áreas importadas (CSV, `flask alta areas`) nacen `Inactivo`.
- Docs: `business_rules.md`, `REQUERIMIENTOS.md` (RF-04b), contrato `areas-y-roles.md` 3.5.

## Decisiones
- Decisión del dueño (2026-11-28): quitar el último admin de un área activa NO se bloquea, para no frenar las bajas de usuarios.
- Decisión del orquestador (pendiente de validar): la importación masiva de áreas crea `Inactivo` (no hay admin en el CSV; no falla la fila).
- Decisión del orquestador (pendiente de validar): `demo cargar` no cambia; siembra por modelo y «Demo Finanzas» queda activa sin admin (solo datos demo; la regla vive en la API).
- Decisión del orquestador (pendiente de validar): solo se bloquea la **transición** a activa; editar otros campos de un área ya activa sin admin (datos previos) no se bloquea.
- Cambio visible: el alta del superadmin sin `status` (equivale a `Activo`) ahora da `409`; la web debe enviar `Inactivo` o asignar admin. Pendiente en la web (no cubierto aquí).

## Pruebas
- `tests/areas/test_activar_requiere_admin.py` (7; 2 fallaban sin el cambio), `tests/test_bulk_import.py` (1 nueva). Ajustadas 4 pruebas existentes que creaban áreas como superadmin sin `status`.
- Suite completa: 3745 passed, 2 failed (pruebas que creaban áreas sin admin: `test_proteccion_por_rol` POST /areas y `test_traslado_grupos_inactivos`), corregidas; esas 2 más `tests/areas` reejecutadas: 513 passed, salida 0. No se repitió la suite completa tras los dos ajustes de prueba.

## Impacto en elementos compartidos
- `impacto.py` marca `datos` (fixture de prueba) y `resumen` (de FNC-219): coincidencias por nombre. Real: `POST /areas` (consumidores: formulario de áreas de la web, `flask alta areas`, importación masiva) y `PUT /areas/<id>`; validar el alta del superadmin en la web.
