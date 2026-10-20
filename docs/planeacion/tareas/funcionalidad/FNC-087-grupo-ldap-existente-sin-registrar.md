# FNC-087 — Confirmación del superadmin cuando el grupo LDAP derivado ya existe

| Campo | Valor |
|---|---|
| **Carril** | Funcionalidad |
| **Plataforma** | backend |
| **Agente** | desarrollador |
| **Fase** | 3 |
| **Módulo / Área** | plataformas |
| **Prioridad** | Media |
| **Estatus** | Propuesta |
| **Creada** | 2026-10-20 |

## Contexto
- SEG-FNC055-01 (auditor-seguridad, Media): un admin de área crea un área y una plataforma cuyo nombre deriva el DN de un grupo LDAP que ya existe y que ninguna plataforma tiene registrado. FNC-055 lo mete solo en ese grupo, sin aprobación.
- Dónde: `app/modules/platforms/api.py:203-229`, `platforms/grupos.py:61-71`, `access/area_admin_sync.py:70-79`.
- Origen: FNC-055.

## Criterios de aceptación
- [ ] Si quien da de alta o mueve la plataforma no es superadmin y el grupo derivado ya existe en el directorio: 409 o pendiente de confirmación del superadmin (decidir y registrar)
- [ ] Sin accesos automáticos mientras el grupo no esté confirmado
- [ ] Prueba de regresión que primero falle

## Impacto cruzado
- Origen ← FNC-055
- Relacionadas → FNC-046, FNC-080

## Bitácora
| Fecha | Nota |
|---|---|
| 2026-10-20 | Creada por el orquestador desde la auditoría de seguridad de FNC-055 |
