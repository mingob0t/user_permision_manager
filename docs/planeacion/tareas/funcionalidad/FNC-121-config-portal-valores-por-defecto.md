# FNC-121 — Configuración del portal: la API entrega los valores por defecto

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 4 |
| **Módulo / Área** | settings |
| **Prioridad** | Media |
| **Estatus** | Hecha |
| **Rama** | `fnc/FNC-121-config-portal-por-defecto` |
| **Creada** | 2026-10-27 |

## Contexto
- `GET` de la configuración del portal (`app/modules/app/modules/settings/api.py:26`) devuelve `SystemConfig().to_dict()` sin guardar: los `default=` de columna solo se aplican al insertar, así que sin configuración `bg_color`, `text_color`, `portal_name` e `portal_identity_type` llegan `null`.
- Por eso el frontend (`settings/portal-tab.tsx`, antes `settings-panel.tsx`) guarda colores literales de respaldo (`#0f172a`, `#ffffff`), que el hook de lineamientos bloquea al tocar el archivo (DIS-011).

## Objetivo
- Constantes con nombre para los valores por defecto del portal en el módulo `settings`, usadas por el modelo y por la respuesta cuando no hay registro.
- La respuesta sin configuración trae los valores por defecto, nunca `null` en esos campos.
- Registro en `docs/configuracion/VARIABLES.md`.
- Prueba: sin registro, la respuesta trae los valores por defecto.
- Después, el frontend quita el respaldo literal y la excepción de `colores-literales.excepciones.ts` (en DIS-011 o tarea DIS vinculada).

## Impacto cruzado
- Origen ← DIS-011 (commit bloqueado por el hook por los literales de respaldo)
- Coordinar con FNC-029 (divide `admin.py`): se implementa sobre su resultado.
- Desbloquea → DIS-011

## Implementación
- `app/modules/settings/valores_por_defecto.py`: `PORTAL_NAME_POR_DEFECTO`, `PORTAL_IDENTITY_TYPE_POR_DEFECTO`, `BG_COLOR_POR_DEFECTO`, `TEXT_COLOR_POR_DEFECTO` (mismos valores que tenía el modelo).
- `SystemConfig` (`models.py`): `default=` con las constantes y `por_defecto()` (instancia sin guardar con los valores asignados).
- `settings/api.py` (`GET` y `PUT` sin registro) y `respaldo_api.py:107` usan `SystemConfig.por_defecto()`.
- `app/__init__.py` (`inject_global_data`) sin cambio: no hay plantillas y `sys_config`/`portal_settings` no se usan.
- Decisiones del orquestador (pendiente de validar en la prueba de concepto): constantes en archivo propio; el hook de lineamientos no bloqueó los colores en el backend.
- Variables: 4 constantes en `docs/configuracion/VARIABLES.md`; sin cambio de valor, no va a `HISTORIAL.md`; no hay variable de entorno ni `.env.example`.

## Impacto en elementos compartidos
| Elemento | Definido en | Usado en | Validar |
|---|---|---|---|
| `SystemConfig` (clase; `default=` y `por_defecto()` nuevo) | `app/modules/settings/models.py` | `settings/api.py`, `settings/respaldo_api.py` (exportar/restaurar), `app/__init__.py`, `tests/test_respaldo.py` | restaurar un respaldo con `system_config` parcial |
| `por_defecto` (aviso de `impacto.py`) | `models.py` | falso positivo: homónimas de otros módulos (`connectors`, `directory`, `provisioning`, `secretos`), sin relación | ninguna |

## Verificación
- Antes: `tests/test_configuracion_portal.py` rojo (`portal_name` `None`).
- Después: verde. Pytest completo (`-x`): 2397 passed, 15 xfailed, 0 fallos (línea base 2393 + 3 nuevas + 1 previa de develop), 17 min. Código de salida inferido (sin fallos con `-x`); el `$?` capturado fue el de `tail`.
- No verificado: el frontend (fuera de alcance; lo retira DIS-011).

## Bitácora
- 2026-10-27: implementada (pytest completo registrado en el cierre).

- 2026-10-27: verificado por el orquestador: pytest completo 2397 passed, 15 xfailed, código de salida 0 (capturado directamente). Sin auditor-seguridad: no toca autenticación, permisos ni datos de usuarios (solo valores por defecto de la respuesta). Hecha (decisión del orquestador, pendiente de validar en la prueba de concepto).
