# FNC-119 — Backend: cuerpo validado en crud/admin y enlace de bienvenida sin ruta heredada

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 4 |
| **Módulo / Área** | api |
| **Prioridad** | Baja |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-27 |

## Contexto
- `crud.py` y `admin.py` leen el cuerpo con `json_payload()` (laxo, FNC-030): un cuerpo que no es objeto falla con 500 en lugar de `400 cuerpo_invalido`.
- El aviso de bienvenida del login de directorio usa `{BASE_URL}/auth/login`, ruta heredada que ya no existe; SSO usa `BASE_URL`.
- Origen: decisiones de FNC-030.

## Criterios de aceptación
- [ ] Los endpoints de `crud.py` y `admin.py` que leen cuerpo responden `400 cuerpo_invalido` con un cuerpo que no es objeto (prueba que primero falla)
- [ ] El enlace de bienvenida del directorio apunta a la pantalla de acceso vigente (`/login`)

## Impacto cruzado
- Origen ← FNC-030
- Coordinar con → FNC-029 (división de `crud.py` y `admin.py`)

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-27 | Creada como Propuesta (decisiones de FNC-030) |
