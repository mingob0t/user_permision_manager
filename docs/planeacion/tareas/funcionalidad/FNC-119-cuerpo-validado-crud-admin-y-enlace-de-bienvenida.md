# FNC-119 — Backend: cuerpo validado en crud/admin y enlace de bienvenida sin ruta heredada

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 4 |
| **Módulo / Área** | api |
| **Prioridad** | Baja |
| **Estatus** | En revisión |
| **Responsable** | desarrollador |
| **Inicio** | 2026-10-27 |
| **Estatus Git** | Commit local, sin push |
| **Rama** | `fnc/FNC-029-119-dividir-monolitos` |
| **Requiere auditor-seguridad** | No |
| **Creada** | 2026-10-27 |

## Contexto
- `crud.py` y `admin.py` leen el cuerpo con `json_payload()` (laxo, FNC-030): un cuerpo que no es objeto falla con 500 en lugar de `400 cuerpo_invalido`.
- El aviso de bienvenida del login de directorio usa `{BASE_URL}/auth/login`, ruta heredada que ya no existe; SSO usa `BASE_URL`.
- Origen: decisiones de FNC-030.

## Criterios de aceptación
- [x] Los endpoints de `crud.py` y `admin.py` que leen cuerpo responden `400 cuerpo_invalido` con un cuerpo que no es objeto (prueba que primero falla)
- [x] El enlace de bienvenida del directorio apunta a la pantalla de acceso vigente (`/login`)

## Decisiones
Todas: **decisión del orquestador (pendiente de validar en la prueba de concepto)**.
- Los endpoints se migraron a `leer_cuerpo` ya movidos por FNC-029: `PUT /areas/<id>/users`, `POST /users`, `PUT /users/<id>`, `POST /users/purge`, `PUT /me/preferences`, `PUT /settings`, `PUT /smtp`, `POST /smtp/test`, `PUT /templates/<slug>`, `POST /notifications/read`.
- Lista de campos permitidos: los endpoints de `crud`/`admin` no tenían lista blanca, solo `POST/PUT /users` una lista negra (`CAMPOS_NO_PERMITIDOS`, que se conserva). La interfaz reenvía objetos completos (p. ej. `Partial<SmtpConfig>` con `source`/`editable`), así que una lista blanca nueva habría roto la pantalla. Por eso `leer_cuerpo` acepta `permitidos=None` (solo exige objeto) y los endpoints siguen ignorando en silencio los campos que no leen. Pasar a lista blanca estricta queda como propuesta **FNC-120** (requiere cambiar también el frontend; ficha creada como `Propuesta`).
- Cambio de comportamiento a propósito: un cuerpo `[]` (antes tratado como `{}` por el `or {}`) ahora es `400 cuerpo_invalido`; `null` o sin cuerpo siguen siendo `{}`.
- `PUT /areas/<id>/users`: además, `user_ids` que no es lista de enteros da `400 cuerpo_invalido` (antes 500 al iterar).
- Enlace de bienvenida: `{BASE_URL}/login`, que es la pantalla vigente (`frontend/src/app/login/page.tsx`); el prefijo `/auth` solo existe en la API (`/api/v1/auth`). Con `BASE_URL` vacío el enlace queda `/login` (relativo), igual que antes quedaba `/auth/login`.
- Recomendación de la auditoría "exigir BASE_URL": **no se implementa aquí**; anotada en la ficha de FNC-009.

## Verificación
- Pruebas nuevas `tests/test_cuerpo_validado.py` (33): 10 endpoints × 3 cuerpos no objeto → `400 cuerpo_invalido`; `user_ids` no lista; cuerpo objeto sigue 200; enlace de bienvenida `https://.../login` con `BASE_URL` configurada. Contra el código anterior (`29e96f4`) las pruebas de cuerpo fallan con 500 y la del enlace con `/auth/login`: `32 fallan y 1 pasa (el cuerpo objeto), ejecutado sobre una copia exportada de `29e96f4``.
- Pytest completo: ``venv/bin/python -m pytest -q -p no:cacheprovider -rX` → **2393 passed, 15 xfailed, código de salida 0** (2360 + 33 pruebas nuevas)`.
- No ejecutado: revisor, navegador.

## Impacto en elementos compartidos
- `leer_cuerpo` (`app/modules/api/helpers.py`): parámetro `permitidos=None` nuevo (sin permitidos sigue rechazando todo campo; `None` solo valida objeto). Lo usan `access`, `access_requests`, `connectors`, `directory`, `platforms`, `provisioning`, `areas`, `users` (sin cambio para ellos, que pasan un valor). Validar que ninguno pasa `None`.
- Tabla de `impacto.py`: ver FNC-029 (misma rama y misma salida).

## Impacto cruzado
- Origen ← FNC-030
- Se implementa junto con → FNC-029 (división de `crud.py` y `admin.py`, misma rama)
- Genera → FNC-120 (propuesta: lista blanca estricta de campos con cambio de frontend)
- Anotado en → FNC-009 (exigir `BASE_URL`)

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-27 | Creada como Propuesta (decisiones de FNC-030) |
| 2026-10-27 | Propuesta → En curso → En revisión: `leer_cuerpo` en crud/admin, enlace de bienvenida a `/login`, 33 pruebas nuevas. Commit `[FNC-119]` local, sin push |
