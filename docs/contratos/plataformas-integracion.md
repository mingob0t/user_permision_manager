# Contrato — Plataformas: tipo de integración y grupos por nivel

| Campo | Valor |
|---|---|
| Versión | 1 (2026-10-14) |
| Proveedor | backend (FNC-046, FNC-055) |
| Consumidores | web (FNC-069; pantalla DIS-017) |
| Solicitudes | — |

Convenciones comunes: [README.md](README.md). Cambia `POST /platforms`, `PUT /platforms/<id>` y la forma de `Platform`. Sin cambios: `DELETE /platforms/<id>`, visitas y favoritos.

## Endpoints

| Método y ruta | Usuario | Admin (sus áreas) | Admin (ajena) | Superadmin |
|---|---|---|---|---|
| `POST /platforms` | 403 | 201 | 404 (`area_id` ajena) | 201 |
| `PUT /platforms/<id>` | 403 | 200 (sin DN de grupos) | 404 | 200 |
| `GET /platforms`, `GET /platforms/<id>` | Ver FNC-063 | 200 | según FNC-063 | 200 |

## Campos nuevos de `Platform` (respuesta)
| Campo | Tipo | Nota |
|---|---|---|
| `integration_type` | `"ldap"` \| `"conector"` | Obligatorio |
| `ldap_group_user_dn` | string \| null | Grupo del nivel `usuario`; null solo si `conector` |
| `ldap_group_admin_dn` | string \| null | Grupo del nivel `admin`; null solo si `conector` |
| `groups_status` | `"ok"` \| `"no_existe"` \| `"sin_verificar"` | Resultado de la comprobación en el directorio |
| `has_connector` | boolean | Hay conector configurado (ver conectores-y-ejecuciones.md) |
| `active_grants` | int | Accesos vigentes (definición en accesos.md) |

- `user_ids` deja de exponerse (FNC-065; P4: los accesos de NEXUS se descartan).
- Plataformas heredadas: tras la migración 0005 quedan `integration_type: "ldap"` con ambos DN `null` y `groups_status: "sin_verificar"`; se editan sin completarlos y el superadmin define sus grupos (FNC-046).
- `direct_link` y `logo_url` guardados que no cumplan la regla de entrada se devuelven `null` (FNC-046).
- Los demás campos de `Platform` no cambian.

## Entrada (`POST` y `PUT`, lista blanca)
| Campo | Tipo | Obligatorio | Regla |
|---|---|---|---|
| `name` | string | Sí en POST | 2–100 |
| `description` | string | Sí en POST | 1–1000 |
| `area_id` | int | Sí en POST | Área en alcance del actor; se lee de la BD |
| `direct_link` | string \| null | No | Solo `https://`, ≤ 255 (SEC-SES-10) |
| `logo_url` | string \| null | No | Solo `https://`, ≤ 255 |
| `icon`, `bg_color`, `text_color`, `status` | string | No | Igual que hoy |
| `integration_type` | `"ldap"` \| `"conector"` | Sí en POST | — |
| `ldap_group_user_dn` | string | No | **Solo superadmin** (SEC-LDAP-05); admin → 403 `dn_solo_superadmin` |
| `ldap_group_admin_dn` | string | No | **Solo superadmin**; distinto del de usuario |

- Si no llegan los DN, el backend los **deriva** de la convención de las variables `LDAP_*` del `.env` (ADR-004, FNC-043).
- Todo DN se valida bajo la OU de grupos de plataforma, comparando RDN normalizados (SEC-LDAP-04) → si no, 422.
- Si el grupo no existe en el directorio, la plataforma se guarda y la respuesta trae un aviso (los grupos los crea el administrador del directorio en v1).
- Cambiar `integration_type`, los DN o `area_id` con `active_grants > 0` → 409.

### Alta por un admin (decisión del dueño, P6)
En la misma transacción:
1. Crea la plataforma → auditoría `plataforma_creada` (actor: admin X; "admin X dio de alta la plataforma Y").
2. Otorga acceso a todos los admins del área (incluido el creador) (origen `admin_de_area`, nivel `usuario`) → auditoría `acceso_otorgado` con actor `sistema` ("sistema dio permisos de acceso a admin X").
3. Encola el aprovisionamiento (accesos.md, estado `en_proceso`).

- El superadmin tiene acceso por defecto: su alta no genera acceso automático.
- Todos los admins del área reciben el acceso automático (nivel `usuario`); al quitarle el área a un admin se revocan sus accesos `admin_de_area` de esa área (FNC-055).

## Salida
```json
{
  "status": "success",
  "platform": { "id": 12, "name": "Contabilidad", "area_id": 3, "integration_type": "ldap",
    "ldap_group_user_dn": "cn=contabilidad-usuario,ou=finanzas,ou=plataformas,dc=ejemplo,dc=local",
    "ldap_group_admin_dn": "cn=contabilidad-admin,ou=finanzas,ou=plataformas,dc=ejemplo,dc=local",
    "groups_status": "no_existe", "has_connector": false, "active_grants": 1 },
  "warnings": [ { "code": "grupo_no_existe", "message": "El grupo de nivel usuario no existe en el directorio." } ]
}
```
`warnings`: arreglo, vacío si no hay avisos.

## Errores
| HTTP | `code` | Mensaje |
|---|---|---|
| 403 | `dn_solo_superadmin` | Solo el superadmin define los grupos del directorio (también al cambiar `integration_type` en `PUT`). |
| 409 | `plataforma_con_accesos` | No se puede cambiar el tipo, los grupos ni el área con accesos vigentes. |
| 409 | `grupos_iguales` | Los grupos de usuario y admin deben ser distintos. |
| 409 | `grupo_en_uso` | El grupo ya pertenece a otra plataforma. |
| 422 | `validacion` | `fields.direct_link`: "Usa una dirección https://." · `fields.ldap_group_user_dn`: "El grupo debe estar en la OU de plataformas." |

- Directorio sin respuesta al verificar: no es error; se guarda con `groups_status: "sin_verificar"` y aviso `directorio_no_disponible`.

## Refresco
- Sin polling; recarga tras cada escritura propia.

## Datos simulados
```json
[ { "id": 12, "name": "Contabilidad", "description": "ERP contable", "area_id": 3, "area_name": "Finanzas",
    "integration_type": "conector", "ldap_group_user_dn": null, "ldap_group_admin_dn": null,
    "groups_status": "sin_verificar", "has_connector": true, "active_grants": 4, "status": "Activo" } ]
```

## Historial
| Versión | Fecha | Cambio |
|---|---|---|
| 1 | 2026-10-14 | Versión inicial (FNC-038) |
| 1 | 2026-10-19 | Aditivo (FNC-046): nota de plataformas heredadas (0005), URL guardadas no válidas como `null`, `409 grupo_en_uso`; cambiar `integration_type` en `PUT` solo superadmin (`403 dn_solo_superadmin`) |
